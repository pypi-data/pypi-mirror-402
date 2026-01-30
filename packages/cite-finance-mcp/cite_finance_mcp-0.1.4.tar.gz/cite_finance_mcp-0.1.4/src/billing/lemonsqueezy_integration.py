"""
Lemon Squeezy Integration for Cite-Finance
Handles checkout links, webhooks, and subscription management.
"""

import hmac
import hashlib
import json
import os
import structlog
from typing import Dict, Any, Optional
from datetime import datetime
import asyncpg
import httpx

from src.models.user import PricingTier, TIER_LIMITS

logger = structlog.get_logger(__name__)

# Map internal tiers to Lemon Squeezy Variant IDs (set via env)
LS_VARIANT_IDS = {
    PricingTier.STARTER: os.getenv("LS_VARIANT_STARTER"),
    PricingTier.PROFESSIONAL: os.getenv("LS_VARIANT_PRO"),
    PricingTier.ENTERPRISE: os.getenv("LS_VARIANT_ENTERPRISE"),
}

class LemonSqueezyManager:
    """Manages Lemon Squeezy billing operations"""

    def __init__(self, api_key: str, webhook_secret: str, db_pool: asyncpg.Pool = None):
        self.api_key = api_key
        self.webhook_secret = webhook_secret
        self.db = db_pool
        self.base_url = "https://api.lemonsqueezy.com/v1"
        self.headers = {
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
            "Authorization": f"Bearer {api_key}"
        }

    async def get_checkout_url(
        self,
        user_id: str,
        tier: PricingTier,
        email: str,
        name: Optional[str] = None
    ) -> str:
        """
        Generate a hosted checkout URL for a specific tier.
        
        Args:
            user_id: Internal user ID to link subscription
            tier: Pricing tier (Starter, Pro, etc.)
            email: Pre-fill user email
            
        Returns:
            Checkout URL string
        """
        variant_id = LS_VARIANT_IDS.get(tier)
        if not variant_id:
            raise ValueError(f"No Lemon Squeezy Variant ID found for tier: {tier}")

        # Lemon Squeezy allows creating custom checkouts via API
        payload = {
            "data": {
                "type": "checkouts",
                "attributes": {
                    "checkout_data": {
                        "email": email,
                        "name": name,
                        "custom": {
                            "user_id": user_id,
                            "tier": tier.value
                        }
                    },
                    "product_options": {
                        "redirect_url": os.getenv("APP_URL", "https://cite-finance-api.herokuapp.com") + "/dashboard?success=true"
                    }
                },
                "relationships": {
                    "store": {
                        "data": {
                            "type": "stores",
                            "id": os.getenv("LS_STORE_ID")
                        }
                    },
                    "variant": {
                        "data": {
                            "type": "variants",
                            "id": str(variant_id)
                        }
                    }
                }
            }
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/checkouts",
                headers=self.headers,
                json=payload
            )
            
            if resp.status_code != 201:
                logger.error("Failed to create LS checkout", status=resp.status_code, response=resp.text)
                raise Exception("Failed to generate checkout link")

            data = resp.json()
            return data["data"]["attributes"]["url"]

    async def cancel_subscription(self, user_id: str) -> bool:
        """Cancel subscription via API"""
        try:
            async with self.db.acquire() as conn:
                user = await conn.fetchrow(
                    "SELECT stripe_subscription_id FROM users WHERE user_id = $1",
                    user_id
                )
            
            # Note: We reuse the 'stripe_subscription_id' column to store LS subscription ID
            sub_id = user.get("stripe_subscription_id")
            if not sub_id:
                return False

            async with httpx.AsyncClient() as client:
                resp = await client.delete(
                    f"{self.base_url}/subscriptions/{sub_id}",
                    headers=self.headers
                )
                
                if resp.status_code not in [200, 204]:
                    logger.error("Failed to cancel LS subscription", status=resp.status_code)
                    return False
            
            # Update DB locally
            async with self.db.acquire() as conn:
                 await conn.execute(
                    "UPDATE users SET status = 'cancelled' WHERE user_id = $1", 
                    user_id
                 )

            return True

        except Exception as e:
            logger.error("Error cancelling subscription", error=str(e))
            return False

    async def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Verify and process Lemon Squeezy webhooks"""
        
        # 1. Verify Signature
        digest = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(digest, signature):
            raise ValueError("Invalid Webhook Signature")

        data = json.loads(payload)
        event_name = data.get("meta", {}).get("event_name")
        logger.info(f"Received LS Webhook: {event_name}")

        if not self.db:
            # If no DB (e.g. during test), just acknowledge
            return {"status": "ok"}

        # 2. Process Events
        if event_name == "subscription_created":
            await self._handle_sub_created(data)
        elif event_name == "subscription_updated":
            await self._handle_sub_updated(data)
        elif event_name == "subscription_cancelled":
            await self._handle_sub_cancelled(data)

        return {"status": "processed"}

    async def _handle_sub_created(self, data):
        attrs = data["data"]["attributes"]
        custom_data = data["meta"]["custom_data"] # Passed from checkout
        
        user_id = custom_data.get("user_id")
        tier_str = custom_data.get("tier")
        sub_id = data["data"]["id"]
        
        if not user_id:
            logger.warning("No user_id in webhook")
            return

        tier = PricingTier(tier_str) if tier_str else PricingTier.STARTER
        
        async with self.db.acquire() as conn:
            await conn.execute(
                """
                UPDATE users
                SET tier = $1,
                    stripe_subscription_id = $2,
                    status = 'active',
                    api_calls_limit = $3,
                    updated_at = NOW()
                WHERE user_id = $4
                """,
                tier.value,
                sub_id,
                TIER_LIMITS[tier]["api_calls_per_month"],
                user_id
            )
            logger.info("Activated subscription", user_id=user_id, tier=tier.value)

    async def _handle_sub_updated(self, data):
        # Update billing dates, etc.
        pass

    async def _handle_sub_cancelled(self, data):
        sub_id = data["data"]["id"]
        async with self.db.acquire() as conn:
            await conn.execute(
                "UPDATE users SET tier='free', status='cancelled', stripe_subscription_id=NULL WHERE stripe_subscription_id = $1",
                str(sub_id)
            )
