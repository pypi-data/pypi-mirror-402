"""
Subscription and Billing Routes
Lemon Squeezy integration for upgrades/downgrades
"""

import structlog
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from pydantic import BaseModel
from typing import Optional

from src.billing.lemonsqueezy_integration import LemonSqueezyManager
from src.models.user import User, APIKey, PricingTier

logger = structlog.get_logger(__name__)
router = APIRouter()

# Global dependencies (injected from main.py)
_ls_manager: Optional[LemonSqueezyManager] = None


def set_dependencies(ls_manager: LemonSqueezyManager):
    """Set global dependencies"""
    global _ls_manager
    _ls_manager = ls_manager


def get_ls_manager() -> LemonSqueezyManager:
    """Dependency to get LS manager"""
    if _ls_manager is None:
        raise HTTPException(status_code=503, detail="Billing service not initialized")
    return _ls_manager


async def get_current_user_from_header(
    request: Request
) -> tuple[User, APIKey]:
    """Get authenticated user from middleware-injected request state"""
    user = getattr(request.state, "user", None)
    api_key = getattr(request.state, "api_key", None)

    if not user or not api_key:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    return user, api_key


class CreateCheckoutRequest(BaseModel):
    """Request to create checkout session"""
    tier: PricingTier


class CreateCheckoutResponse(BaseModel):
    """Response with checkout URL"""
    checkout_url: str


class SubscriptionInfoResponse(BaseModel):
    """Current subscription information"""
    user_id: str
    tier: str
    status: str
    api_calls_this_month: int
    api_calls_limit: int
    subscription_id: Optional[str]
    billing_period_start: Optional[str]
    billing_period_end: Optional[str]


@router.get("/subscription")
async def get_subscription_info(
    auth: tuple[User, APIKey] = Depends(get_current_user_from_header)
):
    """Get current subscription information"""
    user, _ = auth

    return SubscriptionInfoResponse(
        user_id=user.user_id,
        tier=user.tier.value,
        status=user.status.value,
        api_calls_this_month=user.api_calls_this_month,
        api_calls_limit=user.api_calls_limit,
        subscription_id=user.stripe_subscription_id,
        billing_period_start=user.billing_period_start.isoformat() if user.billing_period_start else None,
        billing_period_end=user.billing_period_end.isoformat() if user.billing_period_end else None
    )


@router.post("/subscription/checkout", response_model=CreateCheckoutResponse)
async def create_checkout_session(
    request: CreateCheckoutRequest,
    auth: tuple[User, APIKey] = Depends(get_current_user_from_header),
    ls_mgr: LemonSqueezyManager = Depends(get_ls_manager)
):
    """
    Create Lemon Squeezy checkout session for upgrading

    Returns a hosted checkout URL.
    """
    user, _ = auth

    try:
        if request.tier == PricingTier.FREE:
            raise HTTPException(
                status_code=400,
                detail="Cannot create checkout for free tier"
            )

        checkout_url = await ls_mgr.get_checkout_url(
            user_id=user.user_id,
            tier=request.tier,
            email=user.email,
            name=user.company_name
        )

        logger.info(
            "Checkout session created",
            user_id=user.user_id,
            tier=request.tier.value
        )

        return CreateCheckoutResponse(checkout_url=checkout_url)

    except ValueError as e:
         raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to create checkout", user_id=user.user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to create checkout session"
        )


@router.post("/subscription/cancel")
async def cancel_subscription(
    auth: tuple[User, APIKey] = Depends(get_current_user_from_header),
    ls_mgr: LemonSqueezyManager = Depends(get_ls_manager)
):
    """Cancel current subscription"""
    user, _ = auth

    try:
        if user.tier == PricingTier.FREE:
            raise HTTPException(
                status_code=400,
                detail="No active subscription to cancel"
            )

        success = await ls_mgr.cancel_subscription(user.user_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail="No active subscription found or cancellation failed"
            )

        return {
            "success": True,
            "message": "Subscription cancelled"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel subscription", user_id=user.user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to cancel subscription"
        )


@router.post("/webhooks/lemonsqueezy")
async def lemonsqueezy_webhook(
    request: Request,
    ls_signature: str = Header(..., alias="x-signature"),
    ls_mgr: LemonSqueezyManager = Depends(get_ls_manager)
):
    """Lemon Squeezy webhook endpoint"""
    try:
        payload = await request.body()
        result = await ls_mgr.handle_webhook(payload, ls_signature)
        return {"success": True}

    except Exception as e:
        logger.error("Webhook processing failed", error=str(e))
        raise HTTPException(status_code=400, detail="Webhook processing failed")


@router.get("/pricing")
async def get_pricing_info():
    """Get pricing tier information"""
    from src.models.user import TIER_LIMITS

    return {
        "tiers": {
            "free": {"price": "$0/month", "limits": TIER_LIMITS[PricingTier.FREE]},
            "starter": {"price": "$49/month", "limits": TIER_LIMITS[PricingTier.STARTER]},
            "professional": {"price": "$199/month", "limits": TIER_LIMITS[PricingTier.PROFESSIONAL]},
            "enterprise": {"price": "$999/month", "limits": TIER_LIMITS[PricingTier.ENTERPRISE]}
        }
    }