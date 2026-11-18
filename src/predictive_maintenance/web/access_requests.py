"""Persist and notify the administrator about public access requests."""

from __future__ import annotations

import hashlib
import logging
import os
import smtplib
import ssl
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage

LOGGER = logging.getLogger(__name__)


class AccessRequestRateLimited(Exception):
    """Raised when a visitor exceeds a server-side submission limit."""


@dataclass(frozen=True)
class AccessRequestResult:
    request_id: str
    notification_sent: bool


class AccessRequestService:
    """Store requests in Firestore, apply quotas, and send an SMTP notification."""

    def __init__(self) -> None:
        from google.cloud import firestore

        project_id = os.environ.get("PREDMAINT_FIREBASE_PROJECT_ID") or None
        self._firestore = firestore
        self._client = firestore.Client(project=project_id)
        self._collection = os.environ.get(
            "PREDMAINT_ACCESS_REQUEST_COLLECTION", "access_requests"
        )

    @staticmethod
    def _digest(value: str) -> str:
        return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()

    def submit(
        self,
        *,
        email: str,
        message: str,
        locale: str,
        client_ip: str,
    ) -> AccessRequestResult:
        now = datetime.now(UTC)
        request_ref = self._client.collection(self._collection).document()
        limits = self._client.collection(f"{self._collection}_limits")
        email_ref = limits.document(f"email-{self._digest(email)}")
        ip_ref = limits.document(f"ip-{self._digest(client_ip or 'unknown')}")
        global_ref = limits.document(f"global-{now:%Y-%m-%d}")
        transaction = self._client.transaction()

        @self._firestore.transactional
        def persist(txn):
            email_snapshot = email_ref.get(transaction=txn)
            ip_snapshot = ip_ref.get(transaction=txn)
            global_snapshot = global_ref.get(transaction=txn)

            email_data = email_snapshot.to_dict() or {}
            last_email_request = email_data.get("last_request_at")
            if last_email_request and now - last_email_request < timedelta(hours=24):
                raise AccessRequestRateLimited

            ip_data = ip_snapshot.to_dict() or {}
            ip_window_started = ip_data.get("window_started_at")
            ip_count = int(ip_data.get("count", 0))
            if not ip_window_started or now - ip_window_started >= timedelta(hours=1):
                ip_window_started, ip_count = now, 0
            if ip_count >= 5:
                raise AccessRequestRateLimited

            global_data = global_snapshot.to_dict() or {}
            global_count = int(global_data.get("count", 0))
            if global_count >= 50:
                raise AccessRequestRateLimited

            txn.set(email_ref, {"last_request_at": now})
            txn.set(
                ip_ref,
                {"window_started_at": ip_window_started, "count": ip_count + 1},
            )
            txn.set(global_ref, {"count": global_count + 1, "day": f"{now:%Y-%m-%d}"})
            txn.set(
                request_ref,
                {
                    "email": email,
                    "message": message,
                    "locale": locale,
                    "status": "pending",
                    "notification_sent": False,
                    "created_at": now,
                },
            )

        persist(transaction)

        notification_sent = self._send_notification(
            request_id=request_ref.id,
            email=email,
            message=message,
            locale=locale,
            created_at=now,
        )
        try:
            request_ref.update({"notification_sent": notification_sent})
        except Exception:
            LOGGER.exception(
                "Could not update notification status for access request %s",
                request_ref.id,
            )
        return AccessRequestResult(request_ref.id, notification_sent)

    def _send_notification(
        self,
        *,
        request_id: str,
        email: str,
        message: str,
        locale: str,
        created_at: datetime,
    ) -> bool:
        smtp_user = os.environ.get("PREDMAINT_SMTP_USER", "").strip()
        smtp_password = os.environ.get("PREDMAINT_SMTP_PASSWORD", "")
        recipient = os.environ.get(
            "PREDMAINT_ACCESS_REQUEST_RECIPIENT", "bordas.marton@gmail.com"
        ).strip()
        if not smtp_user or not smtp_password:
            LOGGER.error(
                "Access request %s was stored, but SMTP credentials are not configured",
                request_id,
            )
            return False

        mail = EmailMessage()
        mail["Subject"] = f"RailSense access request – {email}"
        mail["From"] = smtp_user
        mail["To"] = recipient
        mail["Reply-To"] = email
        mail.set_content(
            "A new RailSense access request was submitted.\n\n"
            f"Request ID: {request_id}\n"
            f"Submitted at: {created_at.isoformat()}\n"
            f"Interface language: {locale}\n"
            f"Requester email: {email}\n\n"
            "Message:\n"
            f"{message}\n\n"
            "No password was generated or transmitted. After approval, create the "
            "Firebase account and let the requester set their password through a "
            "Firebase password-reset link."
        )

        host = os.environ.get("PREDMAINT_SMTP_HOST", "smtp.gmail.com")
        port = int(os.environ.get("PREDMAINT_SMTP_PORT", "465"))
        try:
            with smtplib.SMTP_SSL(
                host, port, context=ssl.create_default_context(), timeout=15
            ) as smtp:
                smtp.login(smtp_user, smtp_password)
                smtp.send_message(mail)
        except (OSError, smtplib.SMTPException):
            LOGGER.exception("Could not send notification for access request %s", request_id)
            return False
        return True

