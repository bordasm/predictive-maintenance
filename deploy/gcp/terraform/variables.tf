variable "project_id" {
  description = "Existing billing-enabled Google Cloud project ID."
  type        = string
}

variable "region" {
  description = "Region for Cloud Run, API Gateway, and Artifact Registry."
  type        = string
  default     = "europe-west1"
}

variable "firestore_location" {
  description = "Firestore database location."
  type        = string
  default     = "europe-west1"
}

variable "api_image" {
  description = "Immutable Artifact Registry image URL for the inference API."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "web_image" {
  description = "Immutable Artifact Registry image URL for the dashboard."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}
