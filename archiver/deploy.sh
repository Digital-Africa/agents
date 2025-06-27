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

# Copy required package files from main source directory before deployment
echo "Copying required package files from main source directory..."
main_source="/Users/mo/Library/Mobile Documents/com~apple~CloudDocs/cloud_agent/puppy/packages"
while IFS= read -r package; do
    if [ -n "$package" ]; then
        src="${main_source}/${package}.py"
        dest="packages/${package}.py"
        if [ -f "$src" ]; then
            cp "$src" "$dest"
            echo "Copied ${package}.py from main source to $dest"
        else
            echo "Warning: ${src} does not exist in main source directory!"
        fi
    fi
done < local_requirements.txt

echo "Deploying function $function..."
# gcloud functions deploy $function \
#   --runtime=python311 \
#   --trigger-http \
#   --region=europe-west1 \
#   --project=digital-africa-rainbow \
#   --entry-point=$function \
#   --allow-unauthenticated \
#   --service-account=puppy-sign@digital-africa-rainbow.iam.gserviceaccount.com

echo "✅ Deployment completed successfully!"