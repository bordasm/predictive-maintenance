output "dashboard_url" {
  description = "Public authenticated dashboard URL."
  value       = google_cloud_run_v2_service.web.uri
}

output "api_url" {
  description = "Firebase-authenticated API Gateway URL."
  value       = "https://${google_api_gateway_gateway.inference.default_hostname}"
}

output "identity_project_id" {
  description = "Identity Platform project used by API clients."
  value       = var.project_id
}
