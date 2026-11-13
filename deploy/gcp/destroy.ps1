[CmdletBinding(SupportsShouldProcess, ConfirmImpact = "High")]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Region = "europe-west1"
)

if (-not $PSCmdlet.ShouldProcess($ProjectId, "Destroy predictive-maintenance GCP resources")) {
    return
}
$terraformRoot = Join-Path $PSScriptRoot "terraform"
Push-Location $terraformRoot
try {
    & terraform destroy -var="project_id=$ProjectId" -var="region=$Region"
    if ($LASTEXITCODE -ne 0) { throw "Terraform destroy failed." }
}
finally {
    Pop-Location
}
