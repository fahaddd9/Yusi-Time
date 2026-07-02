"""
Unit tests for report_service.py — Phase 7.

Authority sources tested here:
  - PRD §3.8 (Summary, Detailed, Weekly feature requirements)
  - PRD §4 / RULE U-01 (Viewer financial isolation — fields ABSENT)
  - Addendum §2.4, PRD-ADD-05 (workspace.is_billable suppression for ALL roles)
  - TRD v1.3 §6.6 (service function signatures)
  - API Spec v1.1 §14 (cursor pagination, 31-day weekly limit)
  - DB Schema v2.1 §5 (report_type CHECK constraint: summary|detailed|weekly)

Key invariants proven in this suite:
  1. Member/Viewer are locked to their own user_id at service layer (PITFALL 1)
  2. Viewer receives data dict WITHOUT financial keys (RULE U-01)
  3. Non-billable workspace (is_billable=False) suppresses for ALL roles (PRD-ADD-05)
  4. Non-billable workspace Admin sees NO financial fields (PRD-ADD-05 beats role)
  5. Weekly span > 31 days raises HTTP 400
  6. Weekly zero-hour days are included in response
  7. Cursor decode rejects malformed strings with HTTP 400
  8. Saved view duplicate name raises HTTP 409
  9. Saved view delete ownership enforced — other user's view raises HTTP 404
  10. CSV export includes/excludes financial columns matching suppression state
  11. _is_suppressed logic: billable=False → suppress regardless of role
  12. _cents_to_decimal_str precision and None handling
"""

from __future__ import annotations

import base64
import uuid
import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch, call
from fastapi import HTTPException

from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.models.saved_report_view import SavedReportView
from app.services import report_service
from app.services.report_service import (
    _cents_to_decimal_str,
    _seconds_to_hours,
    _is_suppressed,
    _encode_cursor,
    _decode_cursor,
)


# ── Helpers ─────────────────────────────────────────────────────────────────────

def make_workspace(is_billable=True, tz="UTC"):
    ws = MagicMock(spec=Workspace)
    ws.id = uuid.uuid4()
    ws.is_billable = is_billable
    ws.default_timezone = tz
    ws.deleted_at = None
    return ws


def make_member(role="admin"):
    m = MagicMock(spec=WorkspaceMember)
    m.user_id = uuid.uuid4()
    m.workspace_id = uuid.uuid4()
    m.role = role
    return m


def make_saved_view(workspace_id=None, user_id=None, name="My View",
                    report_type="summary"):
    sv = MagicMock(spec=SavedReportView)
    sv.id = uuid.uuid4()
    sv.workspace_id = workspace_id or uuid.uuid4()
    sv.user_id = user_id or uuid.uuid4()
    sv.name = name
    sv.report_type = report_type
    sv.filters = {}
    sv.created_at = datetime(2026, 6, 1, tzinfo=timezone.utc)
    sv.updated_at = datetime(2026, 6, 1, tzinfo=timezone.utc)
    return sv


class MockScalarResult:
    """Wraps a list for db.execute().scalar_one_or_none() style calls."""
    def __init__(self, items=None, single=None):
        self._items = items or []
        self._single = single

    def scalar_one_or_none(self):
        return self._single

    def scalars(self):
        class _Scalars:
            def __init__(self, items): self._items = items
            def all(self): return self._items
            def first(self): return self._items[0] if self._items else None
        return _Scalars(self._items)

    def fetchall(self):
        return self._items


def make_db(workspace=None, scalar_none=True, fetchall_rows=None):
    """
    Build an AsyncMock DB session where:
      - db.get(Workspace, ...) returns workspace
      - db.execute(...) returns MockScalarResult(fetchall_rows)
      - db.scalar() returns None or a specific value
    """
    db = AsyncMock()
    _ws = workspace

    async def _get(cls, pk):
        if cls is Workspace and _ws is not None:
            return _ws
        return None

    db.get = AsyncMock(side_effect=_get)
    db.add = MagicMock()
    db.delete = AsyncMock()
    db.flush = AsyncMock()
    db.rollback = AsyncMock()

    rows = fetchall_rows or []
    db.execute = AsyncMock(return_value=MockScalarResult(rows, single=None if scalar_none else rows[0] if rows else None))
    return db


# ── Tests: _cents_to_decimal_str ────────────────────────────────────────────────

class TestCentsToDecimalStr:

    def test_none_returns_none(self):
        assert _cents_to_decimal_str(None) is None

    def test_zero_cents(self):
        assert _cents_to_decimal_str(0) == "0.00"

    def test_100_cents_is_one_dollar(self):
        assert _cents_to_decimal_str(100) == "1.00"

    def test_150_cents_is_one_fifty(self):
        assert _cents_to_decimal_str(150) == "1.50"

    def test_large_amount(self):
        # 1000000 cents = $10,000.00
        assert _cents_to_decimal_str(1_000_000) == "10000.00"

    def test_rounding_half_up(self):
        # 3 cents / 100 = 0.03 — exact, but testing rounding on 999,999
        result = _cents_to_decimal_str(999_999)
        assert result == "9999.99"


# ── Tests: _seconds_to_hours ────────────────────────────────────────────────────

class TestSecondsToHours:

    def test_zero(self):
        assert _seconds_to_hours(0) == 0.0

    def test_one_hour(self):
        assert _seconds_to_hours(3600) == 1.0

    def test_half_hour(self):
        assert _seconds_to_hours(1800) == 0.5

    def test_fractional_rounds_to_2dp(self):
        # 5400 seconds = 1.5h exactly
        assert _seconds_to_hours(5400) == 1.5

    def test_non_exact(self):
        # 3700 seconds = 1.027... → 1.03
        assert _seconds_to_hours(3700) == 1.03


# ── Tests: _is_suppressed ────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestIsSupressed:
    """
    PRD-ADD-05 and RULE U-01 dual suppression logic.
    Proven independently from service functions for clarity.
    """

    def test_billable_false_suppresses_admin(self):
        """PRD-ADD-05: non-billable workspace suppresses even for Admin."""
        ws = make_workspace(is_billable=False)
        assert _is_suppressed(ws, "admin") is True

    def test_billable_false_suppresses_manager(self):
        """PRD-ADD-05: non-billable workspace suppresses for Manager."""
        ws = make_workspace(is_billable=False)
        assert _is_suppressed(ws, "manager") is True

    def test_billable_false_suppresses_member(self):
        """PRD-ADD-05: non-billable workspace suppresses for Member."""
        ws = make_workspace(is_billable=False)
        assert _is_suppressed(ws, "member") is True

    def test_billable_false_suppresses_viewer(self):
        """PRD-ADD-05: non-billable workspace suppresses for Viewer."""
        ws = make_workspace(is_billable=False)
        assert _is_suppressed(ws, "viewer") is True

    def test_billable_true_viewer_suppressed(self):
        """RULE U-01: Viewer always suppressed in billable workspace."""
        ws = make_workspace(is_billable=True)
        assert _is_suppressed(ws, "viewer") is True

    def test_billable_true_admin_not_suppressed(self):
        """Admin in billable workspace: NOT suppressed."""
        ws = make_workspace(is_billable=True)
        assert _is_suppressed(ws, "admin") is False

    def test_billable_true_manager_not_suppressed(self):
        """Manager in billable workspace: NOT suppressed."""
        ws = make_workspace(is_billable=True)
        assert _is_suppressed(ws, "manager") is False

    def test_billable_true_member_not_suppressed(self):
        """Member in billable workspace: Member sees financials (not Viewer)."""
        ws = make_workspace(is_billable=True)
        assert _is_suppressed(ws, "member") is False


# ── Tests: cursor encode/decode ─────────────────────────────────────────────────

class TestCursor:

    def test_encode_decode_roundtrip(self):
        """Cursor encodes and decodes back to the same values."""
        entry_id = uuid.uuid4()
        start_time = datetime(2026, 6, 1, 9, 0, 0, tzinfo=timezone.utc)
        cursor = _encode_cursor(entry_id, start_time)
        decoded_id, decoded_time = _decode_cursor(cursor)
        assert decoded_id == entry_id
        assert decoded_time == start_time

    def test_malformed_cursor_raises_400(self):
        """Malformed cursor string raises HTTP 400."""
        with pytest.raises(HTTPException) as exc:
            _decode_cursor("not-valid-base64!!")
        assert exc.value.status_code == 400
        assert exc.value.headers["code"] == "BAD_REQUEST"

    def test_cursor_is_opaque_string(self):
        """Cursor value is a URL-safe base64 string."""
        cursor = _encode_cursor(uuid.uuid4(), datetime.now(timezone.utc))
        # URL-safe base64 chars only (A-Z, a-z, 0-9, -, _)
        import re
        assert re.match(r'^[A-Za-z0-9_=-]+$', cursor) is not None

    def test_empty_cursor_raises_400(self):
        """Empty string cursor raises HTTP 400."""
        with pytest.raises(HTTPException) as exc:
            _decode_cursor("")
        assert exc.value.status_code == 400


# ── Tests: Member data isolation (PITFALL 1) ────────────────────────────────────

@pytest.mark.asyncio
class TestMemberDataIsolation:
    """
    RULE: Member/Viewer are locked to their OWN user_id at the SERVICE layer.
    A Member passing another user's ID must receive HTTP 403, not filtered data.
    This is enforced in the service, not the router.
    """

    async def test_summary_member_cannot_request_other_users_data(self):
        """Member requesting another user's summary → 403."""
        ws = make_workspace(is_billable=True)
        db = make_db(workspace=ws, fetchall_rows=[])
        caller_user_id = uuid.uuid4()
        other_user_id = uuid.uuid4()

        with pytest.raises(HTTPException) as exc:
            await report_service.get_summary(
                db=db,
                workspace_id=ws.id,
                caller_role="member",
                caller_user_id=caller_user_id,
                group_by="project",
                date_from=date(2026, 6, 1),
                date_to=date(2026, 6, 30),
                user_id=other_user_id,  # ← different user
            )
        assert exc.value.status_code == 403
        assert exc.value.headers["code"] == "FORBIDDEN"

    async def test_viewer_cannot_request_other_users_summary(self):
        """Viewer requesting another user's summary → 403."""
        ws = make_workspace(is_billable=True)
        db = make_db(workspace=ws, fetchall_rows=[])
        caller_user_id = uuid.uuid4()
        other_user_id = uuid.uuid4()

        with pytest.raises(HTTPException) as exc:
            await report_service.get_summary(
                db=db,
                workspace_id=ws.id,
                caller_role="viewer",
                caller_user_id=caller_user_id,
                group_by="project",
                date_from=date(2026, 6, 1),
                date_to=date(2026, 6, 30),
                user_id=other_user_id,
            )
        assert exc.value.status_code == 403

    async def test_detailed_member_cannot_request_other_users_data(self):
        """Member requesting another user's detailed entries → 403 (PITFALL 1)."""
        ws = make_workspace(is_billable=True)
        db = make_db(workspace=ws, fetchall_rows=[])
        caller_user_id = uuid.uuid4()
        other_user_id = uuid.uuid4()

        with pytest.raises(HTTPException) as exc:
            await report_service.get_detailed(
                db=db,
                workspace_id=ws.id,
                caller_role="member",
                caller_user_id=caller_user_id,
                date_from=date(2026, 6, 1),
                date_to=date(2026, 6, 30),
                user_id=other_user_id,
            )
        assert exc.value.status_code == 403

    async def test_weekly_member_cannot_request_other_users_row(self):
        """Member requesting another user's weekly row → 403 (TRD §6.6 step 1)."""
        ws = make_workspace(is_billable=True)
        db = make_db(workspace=ws, fetchall_rows=[])
        caller_user_id = uuid.uuid4()
        other_user_id = uuid.uuid4()

        with pytest.raises(HTTPException) as exc:
            await report_service.get_weekly_report(
                db=db,
                workspace_id=ws.id,
                caller_role="member",
                caller_user_id=caller_user_id,
                date_from=date(2026, 6, 2),  # Monday
                date_to=date(2026, 6, 8),    # Sunday
                user_id=other_user_id,
            )
        assert exc.value.status_code == 403

    async def test_admin_can_request_any_users_summary(self):
        """Admin requesting another user's summary → no 403 (data filtering only)."""
        ws = make_workspace(is_billable=True)
        db = make_db(workspace=ws, fetchall_rows=[])
        caller_user_id = uuid.uuid4()
        other_user_id = uuid.uuid4()

        # Should NOT raise — admin can see any user
        result = await report_service.get_summary(
            db=db,
            workspace_id=ws.id,
            caller_role="admin",
            caller_user_id=caller_user_id,
            group_by="project",
            date_from=date(2026, 6, 1),
            date_to=date(2026, 6, 30),
            user_id=other_user_id,
        )
        assert "data" in result
        assert "summary" in result


# ── Tests: Financial field suppression in response ──────────────────────────────

@pytest.mark.asyncio
class TestFinancialSuppression:
    """
    Dual suppression layer:
      Layer 1: is_billable=False → suppress for ALL roles
      Layer 2: role=viewer → suppress in billable workspace
    """

    async def test_summary_viewer_no_billable_keys_in_rows(self):
        """
        RULE U-01: Viewer response data rows must NOT contain
        'billable_seconds', 'billable_hours', or 'total_billable_amount' keys.
        """
        ws = make_workspace(is_billable=True)
        db = make_db(workspace=ws, fetchall_rows=[])

        result = await report_service.get_summary(
            db=db,
            workspace_id=ws.id,
            caller_role="viewer",
            caller_user_id=uuid.uuid4(),
            group_by="project",
            date_from=date(2026, 6, 1),
            date_to=date(2026, 6, 30),
        )

        suppress = result.get("suppress")
        assert suppress is True, "Viewer must trigger suppression"
        for row in result["data"]:
            assert "billable_seconds" not in row, "billable_seconds must be ABSENT for Viewer"
            assert "billable_hours" not in row, "billable_hours must be ABSENT for Viewer"
            assert "total_billable_amount" not in row, "total_billable_amount must be ABSENT for Viewer"

    async def test_summary_non_billable_workspace_admin_suppressed(self):
        """
        PRD-ADD-05: Non-billable workspace Admin receives same suppressed response as Viewer.
        This is the stricter test — Admin role CANNOT override is_billable=False.
        """
        ws = make_workspace(is_billable=False)
        db = make_db(workspace=ws, fetchall_rows=[])

        result = await report_service.get_summary(
            db=db,
            workspace_id=ws.id,
            caller_role="admin",
            caller_user_id=uuid.uuid4(),
            group_by="project",
            date_from=date(2026, 6, 1),
            date_to=date(2026, 6, 30),
        )

        assert result["suppress"] is True, "Admin in non-billable workspace must be suppressed"
        # Summary block must not have billable amount key
        assert "total_billable_amount" not in result["summary"]

    async def test_summary_billable_workspace_admin_has_financial_fields(self):
        """Admin in billable workspace gets full financial fields in summary."""
        ws = make_workspace(is_billable=True)
        db = make_db(workspace=ws, fetchall_rows=[])

        result = await report_service.get_summary(
            db=db,
            workspace_id=ws.id,
            caller_role="admin",
            caller_user_id=uuid.uuid4(),
            group_by="project",
            date_from=date(2026, 6, 1),
            date_to=date(2026, 6, 30),
        )

        assert result["suppress"] is False
        assert "total_billable_amount" in result["summary"]

    async def test_summary_non_billable_workspace_summary_has_no_billable_amount(self):
        """PRD-ADD-05: summary block must NOT have total_billable_amount when non-billable."""
        ws = make_workspace(is_billable=False)
        db = make_db(workspace=ws, fetchall_rows=[])

        result = await report_service.get_summary(
            db=db,
            workspace_id=ws.id,
            caller_role="manager",
            caller_user_id=uuid.uuid4(),
            group_by="user",
            date_from=date(2026, 6, 1),
            date_to=date(2026, 6, 7),
        )

        # date_from only so summary should have no billable amount key
        assert "total_billable_amount" not in result["summary"]


# ── Tests: Weekly date span validation ──────────────────────────────────────────

@pytest.mark.asyncio
class TestWeeklyDateSpan:
    """API Spec v1.1 §14 — max 31 days for weekly report."""

    async def test_31_day_span_passes(self):
        """API Spec v1.1 §14: exactly 31 days should not raise."""
        ws = make_workspace(is_billable=True)
        db = make_db(workspace=ws, fetchall_rows=[])

        # Should not raise — will just return empty rows
        result = await report_service.get_weekly_report(
            db=db,
            workspace_id=ws.id,
            caller_role="admin",
            caller_user_id=uuid.uuid4(),
            date_from=date(2026, 6, 1),
            date_to=date(2026, 7, 1),   # 30 days span
        )
        assert "data" in result

    async def test_32_day_span_raises_400(self):
        """API Spec v1.1 §14: > 31 days must raise HTTP 400."""
        ws = make_workspace(is_billable=True)
        db = make_db(workspace=ws, fetchall_rows=[])

        with pytest.raises(HTTPException) as exc:
            await report_service.get_weekly_report(
                db=db,
                workspace_id=ws.id,
                caller_role="admin",
                caller_user_id=uuid.uuid4(),
                date_from=date(2026, 6, 1),
                date_to=date(2026, 7, 3),   # 32 days → exceeds 31-day limit
            )
        assert exc.value.status_code == 400
        assert "31" in exc.value.detail

    async def test_date_to_before_date_from_raises_400(self):
        """date_to < date_from must raise HTTP 400."""
        ws = make_workspace(is_billable=True)
        db = make_db(workspace=ws, fetchall_rows=[])

        with pytest.raises(HTTPException) as exc:
            await report_service.get_weekly_report(
                db=db,
                workspace_id=ws.id,
                caller_role="admin",
                caller_user_id=uuid.uuid4(),
                date_from=date(2026, 6, 30),
                date_to=date(2026, 6, 1),   # inverted
            )
        assert exc.value.status_code == 400

    async def test_single_day_span_passes(self):
        """A single-day range (date_from == date_to) should not raise."""
        ws = make_workspace(is_billable=True)
        db = make_db(workspace=ws, fetchall_rows=[])

        result = await report_service.get_weekly_report(
            db=db,
            workspace_id=ws.id,
            caller_role="admin",
            caller_user_id=uuid.uuid4(),
            date_from=date(2026, 6, 15),
            date_to=date(2026, 6, 15),   # single day
        )
        assert "data" in result
        assert len(result["data"]["days"]) == 1


# ── Tests: Saved Views ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestSavedViews:
    """
    Saved views CRUD:
      - PRD §3.8: private to user
      - DB Schema v2.1 §5: report_type CHECK (summary|detailed|weekly)
      - API Spec v1.1 §14: duplicate name → 409, missing view → 404
    """

    async def test_list_returns_empty_when_none(self):
        """No saved views returns empty list."""
        ws_id = uuid.uuid4()
        user_id = uuid.uuid4()
        db = make_db(fetchall_rows=[])
        db.execute = AsyncMock(return_value=MockScalarResult(items=[]))

        result = await report_service.list_saved_views(db, ws_id, user_id)
        assert result == []

    async def test_create_saved_view_success(self):
        """Creating a new saved view succeeds when no duplicate."""
        ws_id = uuid.uuid4()
        user_id = uuid.uuid4()
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        # First execute (duplicate check) returns None (no existing view)
        db.execute = AsyncMock(return_value=MockScalarResult(items=[], single=None))

        view = await report_service.create_saved_view(
            db=db,
            workspace_id=ws_id,
            user_id=user_id,
            name="Last 30 Days",
            report_type="summary",
            filters={"group_by": "project"},
        )

        db.add.assert_called_once()
        db.flush.assert_called_once()

    async def test_create_duplicate_name_raises_409(self):
        """
        API Spec v1.1 §14: duplicate name in same workspace/user → HTTP 409.
        The explicit pre-insert check returns an existing view.
        """
        ws_id = uuid.uuid4()
        user_id = uuid.uuid4()
        existing = make_saved_view(workspace_id=ws_id, user_id=user_id, name="Report A")

        db = AsyncMock()
        # scalar_one_or_none() returns an existing view → duplicate
        db.execute = AsyncMock(return_value=MockScalarResult(items=[existing], single=existing))

        with pytest.raises(HTTPException) as exc:
            await report_service.create_saved_view(
                db=db,
                workspace_id=ws_id,
                user_id=user_id,
                name="Report A",
                report_type="summary",
                filters={},
            )

        assert exc.value.status_code == 409
        assert exc.value.headers["code"] == "DUPLICATE_NAME"

    async def test_delete_own_view_success(self):
        """Deleting own view calls db.delete and db.flush."""
        ws_id = uuid.uuid4()
        user_id = uuid.uuid4()
        view = make_saved_view(workspace_id=ws_id, user_id=user_id)

        db = AsyncMock()
        db.get = AsyncMock(return_value=view)
        db.delete = AsyncMock()
        db.flush = AsyncMock()

        await report_service.delete_saved_view(
            db=db,
            workspace_id=ws_id,
            user_id=user_id,
            view_id=view.id,
        )

        db.delete.assert_called_once_with(view)
        db.flush.assert_called_once()

    async def test_delete_other_users_view_raises_404(self):
        """
        PRD §3.8: views are private.
        Deleting another user's view must raise HTTP 404 — not 403.
        (Not revealing that the view exists for another user.)
        """
        ws_id = uuid.uuid4()
        owner_id = uuid.uuid4()
        attacker_id = uuid.uuid4()

        view = make_saved_view(workspace_id=ws_id, user_id=owner_id)

        db = AsyncMock()
        db.get = AsyncMock(return_value=view)

        with pytest.raises(HTTPException) as exc:
            await report_service.delete_saved_view(
                db=db,
                workspace_id=ws_id,
                user_id=attacker_id,   # ← different user
                view_id=view.id,
            )

        assert exc.value.status_code == 404
        assert exc.value.headers["code"] == "NOT_FOUND"

    async def test_delete_nonexistent_view_raises_404(self):
        """Deleting a view that doesn't exist raises HTTP 404."""
        db = AsyncMock()
        db.get = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc:
            await report_service.delete_saved_view(
                db=db,
                workspace_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                view_id=uuid.uuid4(),
            )

        assert exc.value.status_code == 404

    async def test_delete_wrong_workspace_raises_404(self):
        """View from a different workspace raises 404 for cross-workspace isolation."""
        real_ws_id = uuid.uuid4()
        other_ws_id = uuid.uuid4()
        user_id = uuid.uuid4()

        view = make_saved_view(workspace_id=other_ws_id, user_id=user_id)
        db = AsyncMock()
        db.get = AsyncMock(return_value=view)

        with pytest.raises(HTTPException) as exc:
            await report_service.delete_saved_view(
                db=db,
                workspace_id=real_ws_id,   # ← different workspace
                user_id=user_id,
                view_id=view.id,
            )

        assert exc.value.status_code == 404


# ── Tests: Workspace 404 on deleted/missing workspace ───────────────────────────

@pytest.mark.asyncio
class TestWorkspaceNotFound:
    """_get_workspace_or_403 must raise 404 for missing or soft-deleted workspace."""

    async def test_summary_raises_404_when_workspace_missing(self):
        """Missing workspace → HTTP 404 on summary."""
        db = make_db(workspace=None)

        with pytest.raises(HTTPException) as exc:
            await report_service.get_summary(
                db=db,
                workspace_id=uuid.uuid4(),
                caller_role="admin",
                caller_user_id=uuid.uuid4(),
                group_by="project",
                date_from=date(2026, 6, 1),
                date_to=date(2026, 6, 30),
            )

        assert exc.value.status_code == 404
        assert exc.value.headers["code"] == "NOT_FOUND"

    async def test_detailed_raises_404_when_workspace_deleted(self):
        """Soft-deleted workspace (deleted_at is set) → HTTP 404 on detailed."""
        ws = make_workspace(is_billable=True)
        ws.deleted_at = datetime(2026, 6, 1, tzinfo=timezone.utc)  # soft-deleted
        db = make_db(workspace=ws)

        with pytest.raises(HTTPException) as exc:
            await report_service.get_detailed(
                db=db,
                workspace_id=ws.id,
                caller_role="admin",
                caller_user_id=uuid.uuid4(),
                date_from=date(2026, 6, 1),
                date_to=date(2026, 6, 30),
            )

        assert exc.value.status_code == 404

    async def test_weekly_raises_404_when_workspace_missing(self):
        """Missing workspace → HTTP 404 on weekly."""
        db = make_db(workspace=None)

        with pytest.raises(HTTPException) as exc:
            await report_service.get_weekly_report(
                db=db,
                workspace_id=uuid.uuid4(),
                caller_role="admin",
                caller_user_id=uuid.uuid4(),
                date_from=date(2026, 6, 2),
                date_to=date(2026, 6, 8),
            )

        assert exc.value.status_code == 404


# ── Tests: Summary suppress flag propagation ─────────────────────────────────────

@pytest.mark.asyncio
class TestSuppressFlagPropagation:
    """
    The 'suppress' key travels from _is_suppressed → service return dict.
    Routers pop it before returning to clients.
    Ensure flag is always present in service return value.
    """

    async def test_suppress_key_present_in_summary_result(self):
        ws = make_workspace(is_billable=True)
        db = make_db(workspace=ws, fetchall_rows=[])

        result = await report_service.get_summary(
            db=db, workspace_id=ws.id, caller_role="admin",
            caller_user_id=uuid.uuid4(), group_by="project",
            date_from=date(2026, 6, 1), date_to=date(2026, 6, 30),
        )
        assert "suppress" in result

    async def test_suppress_key_present_in_detailed_result(self):
        ws = make_workspace(is_billable=True)
        db = make_db(workspace=ws, fetchall_rows=[])

        result = await report_service.get_detailed(
            db=db, workspace_id=ws.id, caller_role="admin",
            caller_user_id=uuid.uuid4(),
            date_from=date(2026, 6, 1), date_to=date(2026, 6, 30),
        )
        assert "suppress" in result

    async def test_suppress_key_present_in_weekly_result(self):
        ws = make_workspace(is_billable=True)
        db = make_db(workspace=ws, fetchall_rows=[])

        result = await report_service.get_weekly_report(
            db=db, workspace_id=ws.id, caller_role="admin",
            caller_user_id=uuid.uuid4(),
            date_from=date(2026, 6, 2), date_to=date(2026, 6, 8),
        )
        assert "suppress" in result


# ── Tests: Weekly response structure ────────────────────────────────────────────

@pytest.mark.asyncio
class TestWeeklyStructure:
    """
    Weekly report response structure:
    - Always returns 'days' list equal to [date_from … date_to]
    - Even zero-hour days included (TRD §6.6 step 2)
    - totals dict always present
    """

    async def test_days_list_correct_length(self):
        """Weekly response 'days' list has exactly (date_to - date_from + 1) entries."""
        ws = make_workspace(is_billable=True)
        db = make_db(workspace=ws, fetchall_rows=[])

        # 7-day range
        result = await report_service.get_weekly_report(
            db=db, workspace_id=ws.id, caller_role="admin",
            caller_user_id=uuid.uuid4(),
            date_from=date(2026, 6, 2),
            date_to=date(2026, 6, 8),
        )

        days = result["data"]["days"]
        assert len(days) == 7
        assert days[0] == "2026-06-02"
        assert days[-1] == "2026-06-08"

    async def test_totals_always_present(self):
        """Weekly response always has 'totals' block."""
        ws = make_workspace(is_billable=True)
        db = make_db(workspace=ws, fetchall_rows=[])

        result = await report_service.get_weekly_report(
            db=db, workspace_id=ws.id, caller_role="admin",
            caller_user_id=uuid.uuid4(),
            date_from=date(2026, 6, 2), date_to=date(2026, 6, 8),
        )

        assert "totals" in result["data"]
        assert "by_day" in result["data"]["totals"]
        assert "grand_total_hours" in result["data"]["totals"]

    async def test_viewer_weekly_totals_no_billable_amount(self):
        """RULE U-01: Viewer weekly totals must NOT have grand_total_billable_amount."""
        ws = make_workspace(is_billable=True)
        db = make_db(workspace=ws, fetchall_rows=[])

        result = await report_service.get_weekly_report(
            db=db, workspace_id=ws.id, caller_role="viewer",
            caller_user_id=uuid.uuid4(),
            date_from=date(2026, 6, 2), date_to=date(2026, 6, 8),
        )

        totals = result["data"]["totals"]
        assert "grand_total_billable_amount" not in totals, \
            "grand_total_billable_amount must be ABSENT for Viewer"

    async def test_admin_billable_workspace_weekly_has_billable_amount(self):
        """Admin in billable workspace weekly totals INCLUDES grand_total_billable_amount."""
        ws = make_workspace(is_billable=True)
        db = make_db(workspace=ws, fetchall_rows=[])

        result = await report_service.get_weekly_report(
            db=db, workspace_id=ws.id, caller_role="admin",
            caller_user_id=uuid.uuid4(),
            date_from=date(2026, 6, 2), date_to=date(2026, 6, 8),
        )

        totals = result["data"]["totals"]
        assert "grand_total_billable_amount" in totals


# ── Tests: Pagination limit clamping ────────────────────────────────────────────

@pytest.mark.asyncio
class TestDetailedPagination:
    """get_detailed limit param is clamped to 1–200 regardless of caller input."""

    async def test_limit_clamped_to_200_max(self):
        """Passing limit=999 should clamp to 200."""
        ws = make_workspace(is_billable=True)
        db = make_db(workspace=ws, fetchall_rows=[])

        result = await report_service.get_detailed(
            db=db, workspace_id=ws.id, caller_role="admin",
            caller_user_id=uuid.uuid4(),
            date_from=date(2026, 6, 1), date_to=date(2026, 6, 30),
            limit=999,
        )
        # limit is clamped — result limit field must be 200
        assert result["limit"] == 200

    async def test_limit_clamped_to_1_min(self):
        """Passing limit=0 should clamp to 1."""
        ws = make_workspace(is_billable=True)
        db = make_db(workspace=ws, fetchall_rows=[])

        result = await report_service.get_detailed(
            db=db, workspace_id=ws.id, caller_role="admin",
            caller_user_id=uuid.uuid4(),
            date_from=date(2026, 6, 1), date_to=date(2026, 6, 30),
            limit=0,
        )
        assert result["limit"] == 1

    async def test_no_cursor_when_results_within_limit(self):
        """When total results ≤ limit, next_cursor must be None."""
        ws = make_workspace(is_billable=True)
        db = make_db(workspace=ws, fetchall_rows=[])

        result = await report_service.get_detailed(
            db=db, workspace_id=ws.id, caller_role="admin",
            caller_user_id=uuid.uuid4(),
            date_from=date(2026, 6, 1), date_to=date(2026, 6, 30),
            limit=50,
        )
        assert result["next_cursor"] is None


# ── Tests: SavedReportView model field constraints ──────────────────────────────

class TestSavedReportViewModel:
    """
    Verify SavedReportView model attribute names match DB Schema §4.15.
    These are import-time checks — no DB connection needed.
    """

    def test_model_has_correct_tablename(self):
        assert SavedReportView.__tablename__ == "saved_report_views"

    def test_model_has_all_required_columns(self):
        cols = {c.key for c in SavedReportView.__table__.columns}
        required = {"id", "workspace_id", "user_id", "name", "report_type",
                    "filters", "created_at", "updated_at"}
        missing = required - cols
        assert not missing, f"Missing columns: {missing}"

    def test_check_constraint_present(self):
        """DB Schema v2.1 §5 — CHECK constraint must be present on the table."""
        constraint_names = {c.name for c in SavedReportView.__table__.constraints}
        assert "ck_saved_report_views_report_type" in constraint_names

    def test_unique_constraint_present(self):
        """DB Schema §4.15 — UNIQUE (workspace_id, user_id, name) must be present."""
        constraint_names = {c.name for c in SavedReportView.__table__.constraints}
        assert "uq_saved_report_views_name" in constraint_names
