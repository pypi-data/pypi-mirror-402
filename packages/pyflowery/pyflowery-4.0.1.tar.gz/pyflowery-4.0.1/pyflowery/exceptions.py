from pyflowery.models import Result

__all__ = [
    "HttpException",
    "RetryableException",
    "ResponseError",
    "InternalServerError",
    "ClientError",
    "TooManyRequests",
    "RetryLimitExceeded",
]


class HttpException(Exception):
    def __init__(self, message: str, result: Result) -> None:
        super().__init__(message)
        self.message: str = message
        self.result: Result = result


class RetryableException(HttpException):
    """Class for exceptions which should be retryable. Never raise this yourself."""


class ResponseError(HttpException):
    """Raised when an API response is empty or has an unexpected format."""

    def __init__(self, message: str, result: Result) -> None:
        super().__init__(message, result)
        self.message: str = "Invalid response from Flowery API: " + message


class InternalServerError(RetryableException):
    """Raised when the API returns a 5xx status code."""


class ClientError(HttpException):
    """Raised when the API returns a 4xx status code."""


class TooManyRequests(RetryableException):
    """Raised when the API returns a 429 status code."""

    def __init__(self, message: str, result: Result) -> None:
        super().__init__(message, result)


class RetryLimitExceeded(HttpException):
    """Raised when the retry limit is exceeded."""
