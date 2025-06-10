#!/bin/bash

# Check if function name is provided
if [ $# -eq 0 ]; then
    echo "Error: Function name is required"
    echo "Usage: $0 <function_name>"
    exit 1
fi

function=$1
type=agent
lifecycle=dev
absolute_path="/Users/mo/Library/Mobile Documents/com~apple~CloudDocs/cloud_agent/puppy"

echo "Deploying function $function..."
gcloud functions deploy $function \
  --runtime=python311 \
  --trigger-http \
  --region=europe-west1 \
  --project=digital-africa-rainbow \
  --entry-point=$function \
  --allow-unauthenticated \
  --service-account=puppy-sign@digital-africa-rainbow.iam.gserviceaccount.com \
  --memory=512Mi \

echo "✅ Deployment completed successfully!"