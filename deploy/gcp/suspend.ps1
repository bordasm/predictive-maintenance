[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Region = "europe-west1"
)

$ErrorActionPreference = "Stop"
foreach ($service in @("predmaint-api", "predmaint-dashboard")) {
    & gcloud run services update $service --project $ProjectId --region $Region --scaling=0 --quiet
    if ($LASTEXITCODE -ne 0) { throw "Unable to suspend $service." }
}
Write-Output "Cloud Run API and dashboard suspended. Their URLs now reject requests."
