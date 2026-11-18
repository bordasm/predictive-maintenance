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

variable "access_request_email_enabled" {
  description = "Inject the SMTP password secret and send access-request notifications."
  type        = bool
  default     = false
}

variable "access_request_recipient" {
  description = "Administrator address that receives access requests."
  type        = string
  default     = "bordas.marton@gmail.com"
}

variable "smtp_user" {
  description = "SMTP account and From address used for access-request notifications."
  type        = string
  default     = "bordas.marton@gmail.com"
}

variable "smtp_host" {
  description = "TLS-enabled SMTP server."
  type        = string
  default     = "smtp.gmail.com"
}

variable "smtp_port" {
  description = "SMTP-over-TLS port."
  type        = number
  default     = 465
}

variable "smtp_password_secret_id" {
  description = "Existing Secret Manager secret containing the SMTP app password."
  type        = string
  default     = "predmaint-smtp-password"
}
