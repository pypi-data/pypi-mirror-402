#!/bin/bash

# Setup Production Environment Variables
APP_NAME="cite-finance-api-prod"

echo "🔐 Setting up Production Secrets for $APP_NAME..."
echo "Enter the values when prompted (Output will be hidden)"

read -sp "Lemon Squeezy API Key: " LS_API_KEY
echo ""
read -sp "Lemon Squeezy Webhook Secret: " LS_WEBHOOK_SECRET
echo ""
read -p "LS Store ID: " LS_STORE_ID
read -p "LS Variant ID (Starter): " LS_VARIANT_STARTER
read -p "LS Variant ID (Pro): " LS_VARIANT_PRO
read -p "LS Variant ID (Enterprise): " LS_VARIANT_ENTERPRISE

echo "⚙️  Configuring Heroku..."

heroku config:set \
    LS_API_KEY="$LS_API_KEY" \
    LS_WEBHOOK_SECRET="$LS_WEBHOOK_SECRET" \
    LS_STORE_ID="$LS_STORE_ID" \
    LS_VARIANT_STARTER="$LS_VARIANT_STARTER" \
    LS_VARIANT_PRO="$LS_VARIANT_PRO" \
    LS_VARIANT_ENTERPRISE="$LS_VARIANT_ENTERPRISE" \
    PYTHON_ENV="production" \
    LOG_LEVEL="info" \
    -a "$APP_NAME"

echo "✅ Secrets set!"
echo "🔄 Restarting application..."
heroku ps:restart -a "$APP_NAME"
echo "🚀 Application is LIVE!"