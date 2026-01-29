"""Custom exceptions with user-friendly messages."""


class AzEnvsError(Exception):
    """Base exception for az-envs."""

    pass


class AuthenticationError(AzEnvsError):
    """Raised when Azure authentication fails."""

    def __init__(self, original_error: Exception | None = None):
        message = (
            "Azure authentication failed.\n"
            "Please ensure you are logged in with: az login\n"
            "Then verify your session with: az account show"
        )
        if original_error:
            message += f"\n\nOriginal error: {original_error}"
        super().__init__(message)


class PermissionError(AzEnvsError):
    """Raised when user lacks permissions."""

    def __init__(self, resource: str, operation: str, original_error: Exception | None = None):
        message = (
            f"Permission denied: cannot {operation} on '{resource}'.\n\n"
            "To fix this, you need one of the following:\n"
            "  1. Key Vault access policy: Grant 'Get' and 'List' secret permissions\n"
            "  2. Azure RBAC: Assign 'Key Vault Secrets User' role\n\n"
            "Ask your Azure administrator to grant access, or verify you're using\n"
            "the correct subscription: az account show"
        )
        if original_error:
            message += f"\n\nOriginal error: {original_error}"
        super().__init__(message)


class ResourceNotFoundError(AzEnvsError):
    """Raised when a resource is not found."""

    def __init__(self, resource_type: str, resource_name: str, original_error: Exception | None = None):
        message = (
            f"{resource_type} '{resource_name}' not found.\n\n"
            "Please verify:\n"
            "  1. The name is spelled correctly\n"
            "  2. The resource exists in your current subscription\n"
            "  3. Check your subscription with: az account show"
        )
        if original_error:
            message += f"\n\nOriginal error: {original_error}"
        super().__init__(message)
