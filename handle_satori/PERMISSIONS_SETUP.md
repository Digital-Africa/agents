# Setting Up Permissions for Satori Handler Cloud Function

This guide shows you how to set up the required permissions for the Satori handler Cloud Function using the generated YAML file.

## Method 1: Using gcloud CLI (Recommended)

### Step 1: Create the Custom Role

```bash
# Create the custom role using the YAML file
gcloud iam roles create satoriHandler \
    --project=digital-africa-fuze \
    --file=satori-handler-role.yaml
```

### Step 2: Create a Service Account (if not exists)

```bash
# Create a dedicated service account for the function
gcloud iam service-accounts create satori-handler-sa \
    --display-name="Satori Handler Service Account" \
    --description="Service account for Satori CSV processing function" \
    --project=digital-africa-fuze
```

### Step 3: Assign the Custom Role to Service Account

```bash
# Assign the custom role to the service account
gcloud projects add-iam-policy-binding digital-africa-fuze \
    --member="serviceAccount:satori-handler-sa@digital-africa-fuze.iam.gserviceaccount.com" \
    --role="projects/digital-africa-fuze/roles/satoriHandler"
```

### Step 4: Grant Cross-Project Access (for Firestore)

Since the function accesses Firestore in `digital-africa-rainbow` project:

```bash
# Grant Firestore access in the rainbow project
gcloud projects add-iam-policy-binding digital-africa-rainbow \
    --member="serviceAccount:satori-handler-sa@digital-africa-fuze.iam.gserviceaccount.com" \
    --role="roles/datastore.user"
```

### Step 5: Deploy Cloud Function with Service Account

```bash
# Deploy the function with the service account
gcloud functions deploy handle-satori \
    --runtime python39 \
    --trigger-event google.storage.object.finalize \
    --trigger-resource fuze-subscriptions \
    --service-account=satori-handler-sa@digital-africa-fuze.iam.gserviceaccount.com \
    --project=digital-africa-fuze \
    --source=. \
    --entry-point=handle_satori
```

## Method 2: Using Google Cloud Console

### Step 1: Create Custom Role via Console

1. Go to **IAM & Admin** > **Roles**
2. Click **Create Role**
3. Copy the contents from `satori-handler-role.yaml`
4. Fill in the form:
   - **Title**: Satori Handler Custom Role
   - **Description**: Custom role for Satori CSV processing function
   - **Permissions**: Add each permission from the YAML file
5. Click **Create**

### Step 2: Create Service Account

1. Go to **IAM & Admin** > **Service Accounts**
2. Click **Create Service Account**
3. Fill in:
   - **Name**: satori-handler-sa
   - **Description**: Service account for Satori CSV processing function
4. Click **Create and Continue**

### Step 3: Assign Roles

1. In the service account details, click **Grant Access**
2. Add the custom role you created
3. Add `roles/datastore.user` for the `digital-africa-rainbow` project
4. Click **Save**

### Step 4: Deploy Function

1. Go to **Cloud Functions**
2. Create new function or update existing one
3. In **Runtime, build, connections and security settings**:
   - Set **Service account** to `satori-handler-sa@digital-africa-fuze.iam.gserviceaccount.com`

## Method 3: Using Terraform

### Create `main.tf`:

```hcl
# Create custom role
resource "google_project_iam_custom_role" "satori_handler" {
  project     = "digital-africa-fuze"
  role_id     = "satoriHandler"
  title       = "Satori Handler Custom Role"
  description = "Custom role for Satori CSV processing function"
  permissions = [
    "datastore.entities.get",
    "datastore.entities.list",
    "datastore.entities.create",
    "datastore.entities.update",
    "datastore.entities.delete",
    "storage.objects.get",
    "storage.objects.list",
    "storage.buckets.get",
    "logging.logEntries.create",
    "logging.logEntries.list",
    "logging.logs.list"
  ]
}

# Create service account
resource "google_service_account" "satori_handler" {
  account_id   = "satori-handler-sa"
  display_name = "Satori Handler Service Account"
  description  = "Service account for Satori CSV processing function"
  project      = "digital-africa-fuze"
}

# Assign custom role to service account
resource "google_project_iam_member" "satori_handler_role" {
  project = "digital-africa-fuze"
  role    = google_project_iam_custom_role.satori_handler.id
  member  = "serviceAccount:${google_service_account.satori_handler.email}"
}

# Grant cross-project Firestore access
resource "google_project_iam_member" "satori_handler_firestore" {
  project = "digital-africa-rainbow"
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.satori_handler.email}"
}
```

## Verification

### Test the Permissions:

```bash
# Test Firestore access
gcloud auth activate-service-account --key-file=path/to/key.json
python -c "
from packages.Firestore import Firestore
db = Firestore(database='memory-bank').client
print('Firestore connection successful')
"

# Test Storage access
python -c "
from packages.storage import GCSStorage
storage = GCSStorage(bucket_name='fuze-subscriptions', project_id='digital-africa-fuze')
files = storage.list_new_files()
print(f'Storage access successful, found {len(files)} files')
"
```

## Troubleshooting

### Common Issues:

1. **Permission Denied Errors**:
   ```bash
   # Check current permissions
   gcloud projects get-iam-policy digital-africa-fuze \
       --flatten="bindings[].members" \
       --format="table(bindings.role)" \
       --filter="bindings.members:satori-handler-sa@digital-africa-fuze.iam.gserviceaccount.com"
   ```

2. **Cross-Project Access Issues**:
   - Ensure the service account has `datastore.user` role in both projects
   - Check that the Firestore database `memory-bank` exists in `digital-africa-rainbow`

3. **Storage Bucket Access**:
   - Verify the bucket `fuze-subscriptions` exists in `digital-africa-fuze`
   - Check bucket permissions and IAM policies

### Logs to Monitor:

```bash
# View function logs
gcloud functions logs read handle-satori --project=digital-africa-fuze

# View IAM audit logs
gcloud logging read "resource.type=gce_instance AND protoPayload.serviceName=iam.googleapis.com" \
    --project=digital-africa-fuze
```

## Security Best Practices

1. **Principle of Least Privilege**: Only grant the minimum required permissions
2. **Service Account Rotation**: Regularly rotate service account keys
3. **Audit Logging**: Enable audit logs to monitor access
4. **Cross-Project Access**: Minimize cross-project permissions when possible
5. **Regular Reviews**: Periodically review and update permissions

## Alternative: Using Predefined Roles

If you prefer to use predefined roles instead of custom roles:

```bash
# Assign predefined roles
gcloud projects add-iam-policy-binding digital-africa-fuze \
    --member="serviceAccount:satori-handler-sa@digital-africa-fuze.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding digital-africa-fuze \
    --member="serviceAccount:satori-handler-sa@digital-africa-fuze.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding digital-africa-fuze \
    --member="serviceAccount:satori-handler-sa@digital-africa-fuze.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter"
```

**Note**: Predefined roles grant broader permissions than the custom role, which may not follow the principle of least privilege. 