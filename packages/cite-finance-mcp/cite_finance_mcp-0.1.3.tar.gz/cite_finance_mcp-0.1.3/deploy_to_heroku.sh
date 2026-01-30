#!/bin/bash

# Deploy Cite-Finance API to Heroku
APP_NAME="cite-finance-api-prod"

echo "🚀 Starting Deployment for $APP_NAME..."

# 1. Check for Heroku CLI
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI not found. Please install it: 'curl https://cli-assets.heroku.com/install.sh | sh'"
    exit 1
fi

# 2. Login
echo "🔑 Please login to Heroku..."
heroku login

# 3. Create App
if heroku apps:info -a "$APP_NAME" &> /dev/null; then
    echo "✅ App $APP_NAME already exists."
else
    echo "🆕 Creating app $APP_NAME..."
    heroku create "$APP_NAME"
fi

# 4. Add Add-ons (Database & Redis)
echo "📦 Provisioning Database and Redis..."
heroku addons:create heroku-postgresql:mini -a "$APP_NAME"
heroku addons:create heroku-redis:mini -a "$APP_NAME"

# 5. Set Buildpacks
heroku buildpacks:set heroku/python -a "$APP_NAME"

# 6. Deploy Code
echo "pushing to heroku master..."
git push heroku main

echo "✅ Deployment push complete."
echo "⚠️  CRITICAL: You must now run './setup_prod_env.sh' to set your Stripe keys!"
