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
gcloud functions deploy handle-satori-input \                          
  --gen2 \
  --runtime=python310 \
  --region=europe-west1 \
  --trigger-event=google.cloud.storage.object.v1.finalized \
  --trigger-resource=gs://fuze-subscriptions \
  --entry-point=handle_satori_input \
  --memory=256Mi \
  --project=digital-africa-fuze

echo "✅ Deployment completed successfully!"

