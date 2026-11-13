[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Region = "europe-west1",
    [switch]$AutoApprove
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
$terraformRoot = Join-Path $PSScriptRoot "terraform"
$buildRoot = Join-Path $projectRoot ".gcp-build"
$revision = (& git -C $projectRoot rev-parse --short=12 HEAD).Trim()
if (-not $revision) { throw "Unable to determine the Git revision." }

foreach ($command in @("gcloud", "terraform", "uv")) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "$command is required. Run this script in Google Cloud Shell or install it locally."
    }
}

& gcloud config set project $ProjectId
if ($LASTEXITCODE -ne 0) { throw "Unable to select Google Cloud project $ProjectId." }

Push-Location $terraformRoot
try {
    & terraform init
    if ($LASTEXITCODE -ne 0) { throw "terraform init failed." }
    & terraform apply `
        -target='google_project_service.required' `
        -target='google_artifact_registry_repository.images' `
        -target='google_project_iam_member.cloud_build_artifact_writer' `
        -target='google_project_iam_member.cloud_build_compute_storage_reader' `
        -target='google_project_iam_member.cloud_build_compute_artifact_writer' `
        -var="project_id=$ProjectId" `
        -var="region=$Region" `
        -auto-approve
    if ($LASTEXITCODE -ne 0) { throw "Infrastructure bootstrap failed." }
}
finally {
    Pop-Location
}

$env:UV_PROJECT_ENVIRONMENT = ".predmaint"
$env:UV_CACHE_DIR = ".uv-cache"
Push-Location $projectRoot
try {
    & uv run python scripts/export_demo_data.py
    if ($LASTEXITCODE -ne 0) { throw "Held-out demo-data export failed." }
    & uv run python deploy/gcp/prepare_build_context.py
    if ($LASTEXITCODE -ne 0) { throw "Cloud Build context preparation failed." }
}
finally {
    Pop-Location
}

$registry = "$Region-docker.pkg.dev/$ProjectId/predmaint"
$apiImage = "$registry/api:$revision"
$webImage = "$registry/dashboard:$revision"
& gcloud builds submit (Join-Path $buildRoot "api") --tag $apiImage --project $ProjectId
if ($LASTEXITCODE -ne 0) { throw "API image build failed." }
& gcloud builds submit (Join-Path $buildRoot "web") --tag $webImage --project $ProjectId
if ($LASTEXITCODE -ne 0) { throw "Dashboard image build failed." }

$applyArguments = @(
    "apply",
    "-var=project_id=$ProjectId",
    "-var=region=$Region",
    "-var=api_image=$apiImage",
    "-var=web_image=$webImage"
)
if ($AutoApprove) { $applyArguments += "-auto-approve" }

Push-Location $terraformRoot
try {
    & terraform @applyArguments
    if ($LASTEXITCODE -ne 0) { throw "Terraform deployment failed." }
    & terraform output
}
finally {
    Pop-Location
}
