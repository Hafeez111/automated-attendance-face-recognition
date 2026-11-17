param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$Region = "asia-south1",
    [string]$ServiceName = "face-attendance"
)

$ErrorActionPreference = "Stop"
$image = "gcr.io/$ProjectId/$ServiceName"

gcloud config set project $ProjectId
gcloud services enable run.googleapis.com cloudbuild.googleapis.com firestore.googleapis.com

gcloud firestore databases describe --database="(default)" 2>$null
if ($LASTEXITCODE -ne 0) {
    gcloud firestore databases create --location=$Region
}

$projectNumber = gcloud projects describe $ProjectId --format="value(projectNumber)"
$serviceAccount = "$projectNumber-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$serviceAccount" --role="roles/datastore.user"

gcloud builds submit --config cloudbuild.yaml --substitutions="_IMAGE=$image" .
gcloud run deploy $ServiceName --image $image --region $Region --platform managed --allow-unauthenticated --set-env-vars="GOOGLE_CLOUD_PROJECT=$ProjectId"
