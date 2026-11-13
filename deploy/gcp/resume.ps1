[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Region = "europe-west1"
)

$ErrorActionPreference = "Stop"
foreach ($service in @("predmaint-api", "predmaint-dashboard")) {
    & gcloud run services update $service --project $ProjectId --region $Region --scaling=auto --min=0 --max=1 --quiet
    if ($LASTEXITCODE -ne 0) { throw "Unable to resume $service." }
}
Write-Output "Cloud Run API and dashboard restored with scale-to-zero and max one instance."
