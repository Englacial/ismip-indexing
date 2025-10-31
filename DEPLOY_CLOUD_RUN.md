# Deploying ISMIP6 Comparison Tool to Google Cloud Run

This guide explains how to deploy the Panel web application to Google Cloud Run using the GitHub Actions workflow.

## Prerequisites

- Google Cloud project with billing enabled
- **Required IAM permissions** on the project:
  - `roles/owner` or `roles/editor` (to enable APIs and create resources)
  - Minimum: `roles/serviceusage.serviceUsageAdmin` + `roles/iam.serviceAccountAdmin` + `roles/resourcemanager.projectIamAdmin`
  - OR have a project admin run the setup commands for you
- GitHub repository with Actions enabled
- `gcloud` CLI installed (for local setup steps)

## Google Cloud Setup

### 1. Enable Required APIs

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Verify you have permissions
gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[].members" --filter="bindings.members:user:$(gcloud config get-value account)"

# Enable required APIs (requires Owner, Editor, or Service Usage Admin role)
gcloud services enable \
  cloudrun.googleapis.com \
  artifactregistry.googleapis.com \
  iamcredentials.googleapis.com
```

**If you get a permission error:**
- You need `roles/owner`, `roles/editor`, or `roles/serviceusage.serviceUsageAdmin`
- Ask your project admin to run these commands
- Or request the necessary IAM role for your account

### 2. Create Artifact Registry Repository

```bash
# Create a Docker repository in Artifact Registry
export REGION="us-west1"
gcloud artifacts repositories create docker \
  --repository-format=docker \
  --location=$REGION \
  --description="Docker images for ISMIP6 Comparison Tool"
```

### 3. Set Up Workload Identity Federation

This allows GitHub Actions to authenticate to Google Cloud without storing service account keys.

```bash
# Create a service account for GitHub Actions
gcloud iam service-accounts create github-actions-deployer \
  --display-name="GitHub Actions Deployer"

export SERVICE_ACCOUNT_EMAIL="github-actions-deployer@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant necessary permissions to the service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/iam.serviceAccountUser"

# Create Workload Identity Pool
gcloud iam workload-identity-pools create github-pool \
  --location="global" \
  --display-name="GitHub Actions Pool"

# Create Workload Identity Provider
export REPO_OWNER="englacial"
export REPO_NAME="ismip-indexing"

gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --attribute-condition="assertion.repository_owner == '${REPO_OWNER}'" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Get the Workload Identity Provider resource name (for GitHub secrets)
export WORKLOAD_IDENTITY_PROVIDER=$(gcloud iam workload-identity-pools providers describe github-provider \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --format="value(name)")

echo "Workload Identity Provider: $WORKLOAD_IDENTITY_PROVIDER"

# Get the Workload Identity Pool ID (for service account binding)
export WORKLOAD_IDENTITY_POOL_ID=$(gcloud iam workload-identity-pools describe github-pool \
  --location="global" \
  --format="value(name)")

# Allow GitHub Actions from your repository owner to impersonate the service account
gcloud iam service-accounts add-iam-policy-binding $SERVICE_ACCOUNT_EMAIL \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${WORKLOAD_IDENTITY_POOL_ID}/attribute.repository_owner/${REPO_OWNER}/${REPO_NAME}"
```

## GitHub Secrets Configuration

Add the following secrets to your GitHub repository (Settings → Secrets and variables → Actions):

### Required Secrets

1. **`GCP_PROJECT_ID`**
   - Your Google Cloud project ID
   - Example: `my-project-123456`

2. **`GCP_WORKLOAD_IDENTITY_PROVIDER`**
   - The full resource name of your Workload Identity Provider
   - Get it with:
     ```bash
     gcloud iam workload-identity-pools providers describe github-provider \
       --location="global" \
       --workload-identity-pool="github-pool" \
       --format="value(name)"
     ```
   - Format: `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider`

3. **`GCP_SERVICE_ACCOUNT`**
   - The service account email
   - Format: `github-actions-deployer@PROJECT_ID.iam.gserviceaccount.com`

### Optional Secrets

4. **`GCP_ARTIFACT_REGISTRY`** (optional)
   - Name of your Artifact Registry repository
   - Default: `docker`

## Deploying the Application

### Via GitHub Actions (Recommended)

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Select **Deploy to Google Cloud Run** workflow
4. Click **Run workflow**
5. (Optional) Customize region and service name
6. Click **Run workflow** button

The workflow will:
- Build the Docker image
- Push to Artifact Registry
- Deploy to Cloud Run
- Display the service URL in the summary

### Testing Locally with Docker

Before deploying, you can test the Docker image locally:

```bash
# Build the image
docker build -t ismip6-comparison-tool .

# Run locally
docker run -p 8080:8080 ismip6-comparison-tool

# Visit http://localhost:8080/app
```

## Post-Deployment

### Access Your Application

After deployment, the service URL will be displayed in the GitHub Actions summary. It will look like:

```
https://ismip6-comparison-tool-xxxxx-uc.a.run.app
```

The app will be accessible at:
```
https://ismip6-comparison-tool-xxxxx-uc.a.run.app/app
```

### Monitor Your Service

```bash
# View logs
gcloud run services logs read ismip6-comparison-tool \
  --region=us-west1 \
  --limit=50

# Get service details
gcloud run services describe ismip6-comparison-tool \
  --region=us-west1

# List all revisions
gcloud run revisions list \
  --service=ismip6-comparison-tool \
  --region=us-west1
```

### Update Deployment Settings

To change memory, CPU, or other settings, update the `gcloud run deploy` command in [.github/workflows/deploy-cloud-run.yml](.github/workflows/deploy-cloud-run.yml).

Common adjustments:

```yaml
# For larger datasets
--memory 4Gi \
--cpu 4 \

# For private access only
--no-allow-unauthenticated \

# For faster cold starts
--min-instances 1 \
```

## Clean Up

To delete the deployment:

```bash
# Delete Cloud Run service
gcloud run services delete ismip6-comparison-tool \
  --region=us-central1

# Delete Docker images
gcloud artifacts docker images delete \
  us-central1-docker.pkg.dev/$PROJECT_ID/docker/ismip6-comparison-tool

# Delete Artifact Registry repository (optional)
gcloud artifacts repositories delete docker \
  --location=us-central1
```

## Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [Panel Deployment Guide](https://panel.holoviz.org/how_to/deployment/index.html)
- [Google Cloud Pricing Calculator](https://cloud.google.com/products/calculator)
