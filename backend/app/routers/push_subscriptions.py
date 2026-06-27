"""
Push Subscriptions Router — Phase 6.5, Addendum §4.3.

Endpoints:
  POST   /users/me/push-subscriptions      — register a browser push subscription
  DELETE /users/me/push-subscriptions/{id} — unregister a specific subscription

Authentication: Bearer token (get_current_user).
Authorization: Users can only manage their OWN subscriptions.

Addendum §5.3 notes:
  - No workspace scoping — push subscriptions are user-scoped.
  - Frontend calls POST after user grants notification permission
    (via an explicit user gesture, per Addendum §6.8).
"""

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.attendance import PushSubscriptionCreate, PushSubscriptionResponse
from app.services import push_service

router = APIRouter(prefix="/users/me/push-subscriptions", tags=["Push Subscriptions"])


@router.post("", response_model=PushSubscriptionResponse, status_code=201)
async def register_push_subscription(
    body: PushSubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Register a browser push subscription for the authenticated user.
    Addendum §4.3.

    Upsert semantics: if the same (user_id, endpoint) pair already exists,
    the keys are updated (handles browser key rotation without 409 errors).

    Called by the frontend after browser notification permission is granted
    via an explicit user gesture (Addendum §6.8 — must be triggered by a
    button click, not automatically on page load).
    """
    subscription = await push_service.create_subscription(
        db=db,
        user_id=current_user.id,
        endpoint=body.endpoint,
        p256dh_key=body.p256dh_key,
        auth_key=body.auth_key,
    )
    return PushSubscriptionResponse.model_validate(subscription)


@router.delete("/{subscription_id}", status_code=204)
async def unregister_push_subscription(
    subscription_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Unregister a specific push subscription for the authenticated user.
    Addendum §4.3.

    Returns 404 if the subscription does not exist or belongs to a different user.
    Returns 204 No Content on success.
    """
    await push_service.delete_subscription(
        db=db,
        user_id=current_user.id,
        subscription_id=subscription_id,
    )
    return None
