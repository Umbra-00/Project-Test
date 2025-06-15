from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
import logging
import traceback

# Configure basic logging for the exceptions module
logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CustomException(Exception):
    """Base custom exception for the application."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DatabaseConnectionError(CustomException):
    """Raised when there's a database connection issue."""

    def __init__(self, detail: str = "Database connection failed"):
        super().__init__(detail, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


class AuthenticationError(CustomException):
    """Raised for authentication-related errors."""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(detail, status_code=status.HTTP_401_UNAUTHORIZED)


class ResourceNotFoundError(CustomException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str):
        super().__init__(f"{resource} not found", status_code=status.HTTP_404_NOT_FOUND)


def global_exception_handler(exc: Exception):
    """
    Global exception handler for logging and standardized error responses.

    Args:
        exc (Exception): The caught exception

    Returns:
        dict: Standardized error response
    """
    # Log the full traceback for debugging purposes
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())

    # Handle different types of exceptions with specific status codes and messages
    if isinstance(exc, CustomException):
        return {"error": True, "status_code": exc.status_code, "message": exc.message}
    elif isinstance(exc, HTTPException):
        # FastAPI's HTTPException should be handled separately
        return {"error": True, "status_code": exc.status_code, "message": exc.detail}

    # Default error handling for unexpected exceptions
    return {
        "error": True,
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "message": "An unexpected error occurred",
        "details": str(exc),
    }


# Function to register exception handlers with FastAPI app
def setup_exception_handlers(app):
    """
    Setup global exception handlers for FastAPI application.

    Args:
        app (FastAPI): The FastAPI application instance
    """

    @app.exception_handler(Exception)
    async def catch_all_exception_handler(request, exc):
        """
        Catches all unhandled exceptions and returns a standardized JSON response.
        """
        error_response = global_exception_handler(exc)
        return JSONResponse(
            status_code=error_response["status_code"], content=error_response
        )
