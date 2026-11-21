import uuid
import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List
from app.config import Config
from app.repositories import get_repository


class BaseNotificationProvider(ABC):
    """Abstract interface defining email and alert dispatch contracts."""

    @abstractmethod
    def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        recipient_user_id: str,
        request_id: Optional[str] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Dispatches an email notification.
        Returns (success, message, notification_record).
        """
        pass


class ConsoleNotificationProvider(BaseNotificationProvider):
    """
    Local notification simulator.
    Outputs realistic email envelopes to the backend terminal console and
    stores persistent records in the notifications table without requiring AWS credentials.
    """

    def __init__(self):
        self.repo = get_repository()

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        recipient_user_id: str,
        request_id: Optional[str] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        notification_id = str(uuid.uuid4())

        # Construct database record
        notification_data = {
            "notification_id": notification_id,
            "recipient_user_id": recipient_user_id,
            "request_id": request_id,
            "channel": "console_simulator",
            "subject": subject,
            "message_body": body_text,
            "status": "delivered",
            "created_at": now
        }

        # Save to database
        self.repo.create_notification(notification_data)

        # Output email envelope to console
        border = "=" * 75
        divider = "-" * 75
        print(f"\n{border}")
        print(" [LOCAL NOTIFICATION SIMULATOR - OUTBOUND EMAIL]")
        print(f"{divider}")
        print(f" NOTIFICATION ID : {notification_id}")
        print(f" TIMESTAMP       : {now}")
        print(f" TO              : {to_email} (User ID: {recipient_user_id})")
        print(f" SUBJECT         : {subject}")
        if request_id:
            print(f" RELATED REQUEST : {request_id}")
        print(f"{divider}")
        print(body_text.strip())
        print(f"{border}\n", flush=True)

        return True, "Simulated email printed to console and stored.", notification_data


class SESNotificationProvider(BaseNotificationProvider):
    """Placeholder for Stage 2 AWS SES integration."""

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        recipient_user_id: str,
        request_id: Optional[str] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        raise NotImplementedError(
            "Amazon SES provider will be activated during Stage 2 in AWS Learner Lab."
        )


_notification_instance: Optional[BaseNotificationProvider] = None


def get_notification_provider() -> BaseNotificationProvider:
    """
    Factory function returning the configured notification provider.
    Stage 1: returns ConsoleNotificationProvider.
    Stage 2: returns SESNotificationProvider.
    """
    global _notification_instance
    if _notification_instance is None:
        if Config.EMAIL_BACKEND == "console":
            _notification_instance = ConsoleNotificationProvider()
        elif Config.EMAIL_BACKEND == "ses":
            _notification_instance = SESNotificationProvider()
        else:
            raise ValueError(f"Unsupported EMAIL_BACKEND: {Config.EMAIL_BACKEND}")
    return _notification_instance