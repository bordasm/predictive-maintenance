locals {
  services = toset([
    "apigateway.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "firebase.googleapis.com",
    "firestore.googleapis.com",
    "identitytoolkit.googleapis.com",
    "run.googleapis.com",
    "servicecontrol.googleapis.com",
    "servicemanagement.googleapis.com",
  ])
}

data "google_project" "current" {
  project_id = var.project_id
}

resource "google_project_service" "required" {
  for_each           = local.services
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "images" {
  project       = var.project_id
  location      = var.region
  repository_id = "predmaint"
  format         = "DOCKER"
  description    = "Predictive-maintenance API and dashboard images"
  depends_on     = [google_project_service.required]
}

resource "google_project_iam_member" "cloud_build_artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${data.google_project.current.number}@cloudbuild.gserviceaccount.com"
  depends_on = [
    google_project_service.required,
    google_artifact_registry_repository.images,
  ]
}

# Newer Google Cloud projects run Cloud Build with the Compute Engine default
# service account. It needs to read the uploaded build context and push images.
resource "google_project_iam_member" "cloud_build_compute_storage_reader" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com"
  depends_on = [
    google_project_service.required,
  ]
}

resource "google_project_iam_member" "cloud_build_compute_artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com"
  depends_on = [
    google_project_service.required,
    google_artifact_registry_repository.images,
  ]
}

resource "google_firebase_project" "default" {
  provider   = google-beta
  project    = var.project_id
  depends_on = [google_project_service.required]
}

resource "google_identity_platform_config" "auth" {
  provider = google-beta
  project  = var.project_id
  sign_in {
    allow_duplicate_emails = false
    email {
      enabled           = true
      password_required = true
    }
  }
  client {
    permissions {
      disabled_user_signup   = true
      disabled_user_deletion = true
    }
  }
  authorized_domains = ["localhost"]
  depends_on         = [google_firebase_project.default]
}

resource "google_firestore_database" "predictions" {
  project                     = var.project_id
  name                        = "(default)"
  location_id                 = var.firestore_location
  type                        = "FIRESTORE_NATIVE"
  delete_protection_state     = "DELETE_PROTECTION_DISABLED"
  deletion_policy             = "DELETE"
  app_engine_integration_mode = "DISABLED"
  depends_on                  = [google_project_service.required]
}

resource "google_service_account" "api" {
  project      = var.project_id
  account_id   = "predmaint-api"
  display_name = "Predictive maintenance inference API"
}

resource "google_project_iam_member" "api_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_cloud_run_v2_service" "api" {
  project             = var.project_id
  name                = "predmaint-api"
  location            = var.region
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_ALL"

  template {
    service_account                  = google_service_account.api.email
    max_instance_request_concurrency = 8
    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }
    containers {
      image = var.api_image
      ports { container_port = 8080 }
      resources {
        limits = { cpu = "1", memory = "1Gi" }
      }
      env {
        name  = "PREDMAINT_FIREBASE_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "PREDMAINT_PREDICTION_BACKEND"
        value = "firestore"
      }
      env {
        name  = "PREDMAINT_FIRESTORE_COLLECTION"
        value = "predictions"
      }
      env {
        name  = "PREDMAINT_ALLOWED_ORIGINS"
        value = "*"
      }
      startup_probe {
        initial_delay_seconds = 0
        timeout_seconds       = 5
        period_seconds        = 5
        failure_threshold     = 24
        http_get {
          path = "/health"
          port = 8080
        }
      }
    }
  }
  depends_on = [google_project_service.required, google_firestore_database.predictions]
}

resource "google_service_account" "gateway" {
  project      = var.project_id
  account_id   = "predmaint-gateway"
  display_name = "Predictive maintenance API Gateway backend identity"
}

resource "google_project_service_identity" "api_gateway" {
  provider = google-beta
  project  = var.project_id
  service  = "apigateway.googleapis.com"
  depends_on = [google_project_service.required]
}

resource "google_service_account_iam_member" "gateway_token_creator" {
  service_account_id = google_service_account.gateway.name
  role               = "roles/iam.serviceAccountTokenCreator"
  # The google-beta provider can return a null email for the API Gateway
  # service identity even after creating it. Its documented address is stable.
  member = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-apigateway.iam.gserviceaccount.com"

  depends_on = [google_project_service_identity.api_gateway]
}

resource "google_cloud_run_v2_service_iam_member" "gateway_invoker" {
  project  = var.project_id
  location = google_cloud_run_v2_service.api.location
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.gateway.email}"
}

resource "google_api_gateway_api" "inference" {
  provider     = google-beta
  project      = var.project_id
  api_id       = "predmaint-inference"
  display_name = "Predictive maintenance inference API"
  depends_on   = [google_project_service.required]
}

resource "google_api_gateway_api_config" "inference" {
  provider             = google-beta
  project              = var.project_id
  api                   = google_api_gateway_api.inference.api_id
  api_config_id_prefix  = "predmaint-"
  display_name          = "Firebase authenticated inference API"
  gateway_config {
    backend_config {
      google_service_account = google_service_account.gateway.email
    }
  }
  openapi_documents {
    document {
      path = "openapi.yaml"
      contents = base64encode(templatefile("${path.module}/openapi.yaml.tftpl", {
        backend_url = google_cloud_run_v2_service.api.uri
        project_id  = var.project_id
      }))
    }
  }
  lifecycle { create_before_destroy = true }
  depends_on = [
    google_cloud_run_v2_service_iam_member.gateway_invoker,
    google_service_account_iam_member.gateway_token_creator,
  ]
}

resource "google_api_gateway_gateway" "inference" {
  provider     = google-beta
  project      = var.project_id
  region       = var.region
  gateway_id   = "predmaint-gateway"
  display_name = "Predictive maintenance gateway"
  api_config   = google_api_gateway_api_config.inference.id
}

resource "google_cloud_run_v2_service" "web" {
  project             = var.project_id
  name                = "predmaint-dashboard"
  location            = var.region
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_ALL"

  scaling {
    min_instance_count = 0
    max_instance_count = 1
  }
  template {
    max_instance_request_concurrency = 20
    containers {
      image = var.web_image
      ports { container_port = 8080 }
      resources {
        limits = { cpu = "1", memory = "512Mi" }
      }
      env {
        name  = "PREDMAINT_API_URL"
        value = "https://${google_api_gateway_gateway.inference.default_hostname}"
      }
      env {
        name  = "PREDMAINT_FIREBASE_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "PREDMAINT_FIREBASE_API_KEY"
        value = google_identity_platform_config.auth.client[0].api_key
      }
      startup_probe {
        timeout_seconds   = 3
        period_seconds    = 5
        failure_threshold = 12
        http_get {
          path = "/health"
          port = 8080
        }
      }
    }
  }
  depends_on = [google_api_gateway_gateway.inference]
}

resource "google_cloud_run_v2_service_iam_member" "public_web" {
  project  = var.project_id
  location = google_cloud_run_v2_service.web.location
  name     = google_cloud_run_v2_service.web.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
