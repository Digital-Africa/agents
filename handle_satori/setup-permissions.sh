#!/bin/bash

# Setup Permissions for Satori Handler Cloud Function
# This script automates the permission setup process

set -e  # Exit on any error

# Configuration
PROJECT_FUZE="digital-africa-fuze"
PROJECT_RAINBOW="digital-africa-rainbow"
SERVICE_ACCOUNT_NAME="puppy-shakur"
ROLE_NAME="Handler"
FUNCTION_NAME="handle-satori"
BUCKET_NAME="fuze-subscriptions"

echo "🚀 Setting up permissions for Satori Handler Cloud Function"
echo "Project (Fuze): $PROJECT_FUZE"
echo "Project (Rainbow): $PROJECT_RAINBOW"
echo "Service Account: $SERVICE_ACCOUNT_NAME"
echo ""

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Error: gcloud is not authenticated. Please run 'gcloud auth login' first."
    exit 1
fi

# Check if YAML file exists
if [ ! -f "satori-handler-role.yaml" ]; then
    echo "❌ Error: satori-handler-role.yaml not found in current directory"
    exit 1
fi

echo "📋 Step 1: Creating custom IAM role..."
gcloud iam roles create $ROLE_NAME \
    --project=$PROJECT_FUZE \
    --file=satori-handler-role.yaml

echo "✅ Custom role created successfully"

echo ""
echo "🔧 Step 2: Creating service account..."
# Check if service account already exists
if gcloud iam service-accounts describe $SERVICE_ACCOUNT_NAME@$PROJECT_FUZE.iam.gserviceaccount.com --project=$PROJECT_FUZE >/dev/null 2>&1; then
    echo "⚠️  Service account already exists, skipping creation"
else
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="Satori Handler Service Account" \
        --description="Service account for Satori CSV processing function" \
        --project=$PROJECT_FUZE
    echo "✅ Service account created successfully"
fi

echo ""
echo "🔐 Step 3: Assigning custom role to service account..."
gcloud projects add-iam-policy-binding $PROJECT_FUZE \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_FUZE.iam.gserviceaccount.com" \
    --role="projects/$PROJECT_FUZE/roles/$ROLE_NAME"

echo "✅ Custom role assigned successfully"

echo ""
echo "🌉 Step 4: Granting cross-project Firestore access..."
gcloud projects add-iam-policy-binding $PROJECT_RAINBOW \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_FUZE.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

echo "✅ Cross-project Firestore access granted"

echo ""
echo "📊 Step 5: Verifying permissions..."
echo "Current permissions for service account:"
gcloud projects get-iam-policy $PROJECT_FUZE \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:$SERVICE_ACCOUNT_NAME@$PROJECT_FUZE.iam.gserviceaccount.com"

echo ""
echo "🎉 Permission setup completed successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Deploy your Cloud Function with the service account:"
echo "   gcloud functions deploy $FUNCTION_NAME \\"
echo "       --runtime python39 \\"
echo "       --trigger-event google.storage.object.finalize \\"
echo "       --trigger-resource $BUCKET_NAME \\"
echo "       --service-account=$SERVICE_ACCOUNT_NAME@$PROJECT_FUZE.iam.gserviceaccount.com \\"
echo "       --project=$PROJECT_FUZE \\"
echo "       --source=. \\"
echo "       --entry-point=handle_satori"
echo ""
echo "2. Test the function by uploading a CSV file to the $BUCKET_NAME bucket"
echo ""
echo "3. Monitor logs:"
echo "   gcloud functions logs read $FUNCTION_NAME --project=$PROJECT_FUZE" 