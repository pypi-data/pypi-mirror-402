"""
Notification Service Module

Provides system notifications using persistent platform-specific tools.
Currently supports verify-send (Linux).
"""

import shutil

from app.logging_config import get_logger

logger = get_logger(__name__)


class NotificationService:
    """Service for sending system notifications."""

    def __init__(self) -> None:
        self._notify_send = shutil.which("notify-send")
        if not self._notify_send:
            logger.warning("notify-send not found. Notifications will be disabled.")

    async def send_notification(self, title: str, message: str, urgency: str = "normal") -> bool:
        """
        Send a desktop notification.

        Args:
            title: Notification title
            message: Notification body
            urgency: low, normal, critical

        Returns:
            bool: True if sent successfully
        """
        if not self._notify_send:
            logger.debug(f"Skipping notification (notify-send missing): {title}")
            return False

        try:
            # Run in a separate thread/process to avoid blocking async loop?
            # Subprocess.run is blocking.
            # However, notify-send usually returns immediately.
            # For strict async, we should use asyncio.create_subprocess_exec

            import asyncio

            process = await asyncio.create_subprocess_exec(
                self._notify_send,
                "-u",
                urgency,
                "-a",
                "MCP Bridge",
                title,
                message,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await process.wait()
            return process.returncode == 0

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False


_service: NotificationService | None = None


def get_notification_service() -> NotificationService:
    """Get the singleton NotificationService instance."""
    global _service
    if _service is None:
        _service = NotificationService()
    return _service
