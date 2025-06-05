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

# Create necessary directories
echo "Creating required directories..."
#mkdir -p packages
mkdir -p sa_keys

# Copy SA keys
echo "Copying SA keys..."
cp -r "$absolute_path/sa_keys/"* ./sa_keys/

# # Copy required packages
# echo "Copying required packages..."
# for package in $(cat local_requirements.txt); do
#     if [ -f "$absolute_path/packages/$package.py" ]; then
#         echo "Copying $package.py..."
#         cp "$absolute_path/packages/$package.py" packages/
#     else
#         echo "Warning: $package.py not found in source directory"
#     fi
# done

# # Copy any additional JSON files if they exist
# echo "Copying additional JSON files..."
# [ -f "$absolute_path/packages/people.json" ] && cp "$absolute_path/packages/people.json" packages/
# [ -f "$absolute_path/packages/groups.json" ] && cp "$absolute_path/packages/groups.json" packages/

echo "Deploying function $function..."
gcloud functions deploy $function \
  --runtime=python311 \
  --trigger-http \
  --region=europe-west1 \
  --project=digital-africa-rainbow \
  --entry-point=$function \
  --allow-unauthenticated \
  --service-account=puppy-sign@digital-africa-rainbow.iam.gserviceaccount.com

echo "✅ Deployment completed successfully!"