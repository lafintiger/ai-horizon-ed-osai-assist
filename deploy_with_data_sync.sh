#!/bin/bash

# Deploy with Data Sync - AI-Horizon Ed Platform
# This script deploys code and syncs local data to production

echo "🚀 Starting deployment with data sync..."

# Step 1: Export local data
echo "📦 Exporting local data..."
python sync_data_to_production.py export
if [ $? -ne 0 ]; then
    echo "❌ Failed to export data"
    exit 1
fi

# Get the latest export file
EXPORT_FILE=$(ls -t production_sync_data_*.json | head -1)
echo "📄 Using export file: $EXPORT_FILE"

# Step 2: Commit and push
echo "🔄 Committing and pushing to Heroku..."
git add .
git commit -m "Deploy with data sync - $(date)"
git push heroku heroku-deployment:main

if [ $? -ne 0 ]; then
    echo "❌ Failed to push to Heroku"
    exit 1
fi

# Step 3: Import data to production
echo "📥 Importing data to production..."
heroku run python sync_data_to_production.py import $EXPORT_FILE --app ai-horizon-ed

if [ $? -ne 0 ]; then
    echo "❌ Failed to import data"
    exit 1
fi

# Step 4: Verify sync
echo "✅ Verifying sync..."
LOCAL_SKILLS=$(python -c "from app import app, db, EmergingSkill; app.app_context().push(); print(len(EmergingSkill.query.all()))")
REMOTE_SKILLS=$(curl -s https://ai-horizon-ed-3daa7ad9b5a9.herokuapp.com/api/skills | jq 'length')

echo "📊 Skills count - Local: $LOCAL_SKILLS, Remote: $REMOTE_SKILLS"

if [ "$LOCAL_SKILLS" -eq "$REMOTE_SKILLS" ]; then
    echo "🎉 Data sync successful! Local and remote are in sync."
else
    echo "⚠️  Data sync may have issues. Manual verification needed."
fi

echo "🌐 Production URL: https://ai-horizon-ed-3daa7ad9b5a9.herokuapp.com/"
echo "🏠 Local URL: http://localhost:9000/"
echo "✨ Deployment complete!" 