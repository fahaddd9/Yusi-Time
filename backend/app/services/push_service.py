"""
Push Service — Phase 6.5, Addendum §5.3.

Wraps pywebpush (Web Push protocol, RFC 8030) to send browser push notifications
for F1 work-start prompts.

Architecture:
  - VAPID keys are loaded from environment variables via Settings (RULE B-07).
  - If VAPID keys are not configured, push is silently skipped with a warning log.
    This keeps the app bootable in dev/test without push infrastructure.
  - Per-user, per-subscription delivery: all active PushSubscription records for
    a user receive the push independently (one browser / one subscription).
  - Failed sends for a subscription (410 Gone) auto-remove the subscription record.

Called from scheduler_service.py (F1 job) after attendance_notification records
are created. NOT called directly from HTTP request handlers.
"""

from __future__ import annotations

import json
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.push_subscription import PushSubscription
from app.models.workspace import Workspace

logger = logging.getLogger(__name__)


async def send_work_start_push(
    db: AsyncSession,
    workspace: Workspace,
    user_id: uuid.UUID,
) -> None:
    """
    F1 — Send a Web Push notification to all active subscriptions for a user.
    Addendum §5.3.

    Payload structure (Addendum §5.3 spec):
      {
        "type": "work_start_prompt",
        "workspace_id": "<uuid>",
        "workspace_name": "<name>",
        "attendance_mode": "fixed_schedule" | "flexible_hours",
        "message": "Time to start tracking — click to open Yusi Time."
      }

    Silently skipped if VAPID keys are not configured (dev/test safety).
    """
    if not settings.vapid_private_key or not settings.vapid_public_key:
        logger.warning(
            "push_service: VAPID keys not configured — skipping push for user %s", user_id
        )
        return

    # Build the notification payload (Addendum §5.3)
    payload = json.dumps({
        "type": "work_start_prompt",
        "workspace_id": str(workspace.id),
        "workspace_name": workspace.name,
        "attendance_mode": workspace.attendance_mode,
        "message": "Time to start tracking — click to open Yusi Time.",
    })

    # Fetch all active subscriptions for this user
    stmt = select(PushSubscription).where(PushSubscription.user_id == user_id)
    result = await db.execute(stmt)
    subscriptions = result.scalars().all()

    if not subscriptions:
        logger.debug(
            "push_service: no subscriptions found for user %s — skipping push", user_id
        )
        return

    subscriptions_to_delete: list[uuid.UUID] = []

    for sub in subscriptions:
        try:
            await _send_single(sub=sub, payload=payload)
        except _SubscriptionExpired:
            # 410 Gone: browser unsubscribed — remove this subscription record
            subscriptions_to_delete.append(sub.id)
        except Exception as exc:
            # Non-fatal: log and continue with other subscriptions
            logger.warning(
                "push_service: failed to send to subscription %s: %s", sub.id, exc
            )

    # Clean up expired subscriptions (Addendum §5.3: auto-remove on 410)
    for sub_id in subscriptions_to_delete:
        sub_obj = await db.get(PushSubscription, sub_id)
        if sub_obj is not None:
            await db.delete(sub_obj)
            logger.info("push_service: removed expired subscription %s", sub_id)


class _SubscriptionExpired(Exception):
    """Raised internally when a push endpoint returns 410 Gone."""


async def _send_single(sub: PushSubscription, payload: str) -> None:
    """
    Perform the actual Web Push send for one subscription.

    Uses pywebpush.webpush() (synchronous, run in executor to avoid blocking
    the event loop — pywebpush uses requests internally).

    Addendum §5.3: uses VAPID for server identification with the
    vapid_claims_subject as the contact URI.
    """
    import asyncio
    from functools import partial

    loop = asyncio.get_event_loop()

    def _send():
        try:
            from pywebpush import webpush, WebPushException
        except ImportError:
            raise RuntimeError(
                "pywebpush is not installed. Run: poetry add pywebpush==2.0.0"
            )

        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {
                        "p256dh": sub.p256dh_key,
                        "auth": sub.auth_key,
                    },
                },
                data=payload,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={
                    "sub": settings.vapid_claims_subject or "mailto:admin@yusitime.com",
                },
            )
        except WebPushException as exc:
            # 410 Gone: subscription is no longer valid (user unsubscribed)
            response = getattr(exc, "response", None)
            status_code = getattr(response, "status_code", None) if response else None
            if status_code == 410:
                raise _SubscriptionExpired() from exc
            raise

    await loop.run_in_executor(None, partial(_send))


async def get_user_subscriptions(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[PushSubscription]:
    """
    Return all push subscriptions for a user.
    Used by the router for listing subscriptions (not in Addendum §4.3 spec
    but useful for debugging and the DELETE endpoint).
    """
    stmt = select(PushSubscription).where(
        PushSubscription.user_id == user_id
    ).order_by(PushSubscription.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_subscription(
    db: AsyncSession,
    user_id: uuid.UUID,
    endpoint: str,
    p256dh_key: str,
    auth_key: str,
) -> PushSubscription:
    """
    Create or update a push subscription for a user+endpoint pair.
    Addendum §4.3 — POST /users/me/push-subscriptions.

    Upsert semantics: if the same (user_id, endpoint) pair already exists
    (unique constraint uq_push_subscriptions_user_endpoint), update the keys.
    This handles browser subscription rotation without 409 errors.
    """
    # Check for existing subscription with same endpoint
    stmt = select(PushSubscription).where(
        PushSubscription.user_id == user_id,
        PushSubscription.endpoint == endpoint,
    )
    existing = await db.scalar(stmt)

    if existing is not None:
        # Update keys in case they rotated (browser key rotation is rare but valid)
        existing.p256dh_key = p256dh_key
        existing.auth_key = auth_key
        await db.flush()
        return existing

    sub = PushSubscription(
        user_id=user_id,
        endpoint=endpoint,
        p256dh_key=p256dh_key,
        auth_key=auth_key,
    )
    db.add(sub)
    await db.flush()
    return sub


async def delete_subscription(
    db: AsyncSession,
    user_id: uuid.UUID,
    subscription_id: uuid.UUID,
) -> None:
    """
    Delete a push subscription.
    Addendum §4.3 — DELETE /users/me/push-subscriptions/{id}.
    Only the owning user can delete their own subscription (enforced here).
    """
    sub = await db.get(PushSubscription, subscription_id)
    if sub is None or sub.user_id != user_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail="Subscription not found",
            headers={"code": "NOT_FOUND"},
        )
    await db.delete(sub)
    await db.flush()
