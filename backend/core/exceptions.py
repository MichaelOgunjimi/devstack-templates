class NotificationServiceNotConfiguredError(Exception):
    """Raised when NOTIFY_URL or NOTIFY_API_KEY are not set in the environment."""


class NotificationServiceError(Exception):
    """Raised when the HTTP call to the Notification Service returns an error."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class StorageNotConfiguredError(Exception):
    """Raised when MinIO environment variables are not set."""
