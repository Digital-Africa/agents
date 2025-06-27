#!/bin/bash

# Default values
project_id="rainbow"
memory=""

# Parse named arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project=*)
            project_id="${1#*=}"
            shift
            ;;
        --project)
            project_id="$2"
            shift 2
            ;;
        --memory=*)
            memory="${1#*=}"
            shift
            ;;
        --memory)
            memory="$2"
            shift 2
            ;;
        -*)
            echo "Unknown option: $1"
            echo "Usage: $0 <function_name> [--project=value] [--memory=value]"
            echo "  function_name: Name of the function to deploy"
            echo "  --project:     Optional project ID (default: rainbow)"
            echo "  --memory:      Optional memory specification (e.g., 512MB, 1GB)"
            exit 1
            ;;
        *)
            function="$1"
            shift
            ;;
    esac
done

# Check if function name is provided
if [ -z "$function" ]; then
    echo "Error: Function name is required"
    echo "Usage: $0 <function_name> [--project=value] [--memory=value]"
    echo "  function_name: Name of the function to deploy"
    echo "  --project:     Optional project ID (default: rainbow)"
    echo "  --memory:      Optional memory specification (e.g., 512MB, 1GB)"
    exit 1
fi

type=agent
lifecycle=dev
absolute_path="/Users/mo/Library/Mobile Documents/com~apple~CloudDocs/cloud_agent/puppy"

# Build gcloud command for Cloud Storage-triggered function (Gen2)
gcloud_cmd="gcloud functions deploy $function \
  --gen2 \
  --runtime python311 \
  --source=. \
  --region=europe-west1 \
  --project=digital-africa-$project_id \
  --entry-point=$function \
  --allow-unauthenticated \
  --service-account=puppy-shakur@digital-africa-fuze.iam.gserviceaccount.com \
  --trigger-event-filters=type=google.cloud.storage.object.v1.finalized \
  --trigger-event-filters=bucket=fuze-subscriptions"

# Add memory parameter if specified
if [ -n "$memory" ]; then
    gcloud_cmd="$gcloud_cmd --memory=$memory"
fi

echo "Deploying function $function to project $project_id..."
if [ -n "$memory" ]; then
    echo "Memory: $memory"
fi

eval $gcloud_cmd

echo "✅ Deployment completed successfully!"