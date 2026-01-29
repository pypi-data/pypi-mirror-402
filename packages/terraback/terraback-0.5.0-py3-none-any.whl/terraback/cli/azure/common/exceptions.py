"""Azure-specific exception handling utilities."""

from typing import Optional, Callable, Any
import logging
from functools import wraps
from azure.core.exceptions import (
    AzureError, 
    ResourceNotFoundError,
    ClientAuthenticationError,
    HttpResponseError,
    ResourceExistsError,
    ResourceModifiedError
)

logger = logging.getLogger(__name__)


class AzureScanError(Exception):
    """Base exception for Azure scanning operations."""
    pass


class AzureAuthenticationError(AzureScanError):
    """Raised when Azure authentication fails."""
    pass


class AzureResourceAccessError(AzureScanError):
    """Raised when access to a specific resource is denied."""
    pass


def safe_azure_operation(
    operation_name: str,
    default_return: Any = None,
    raise_on_error: bool = False,
    log_level: str = "warning"
) -> Callable:
    """
    Decorator for safe Azure SDK operations with comprehensive error handling.
    
    Args:
        operation_name: Name of the operation for logging
        default_return: Value to return if operation fails
        raise_on_error: Whether to re-raise exceptions
        log_level: Logging level for errors (debug, info, warning, error)
        
    Usage:
        @safe_azure_operation("list key vault secrets", default_return=[])
        def list_secrets(vault_name):
            return client.list_secrets(vault_name)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ClientAuthenticationError as e:
                logger.error(f"Authentication failed for {operation_name}: {e}")
                if raise_on_error:
                    raise AzureAuthenticationError(f"Authentication failed: {e}") from e
                return default_return
            except ResourceNotFoundError as e:
                getattr(logger, log_level)(f"Resource not found in {operation_name}: {e}")
                if raise_on_error:
                    raise
                return default_return
            except HttpResponseError as e:
                if e.status_code == 403:
                    logger.warning(f"Access denied for {operation_name}: {e}")
                    if raise_on_error:
                        raise AzureResourceAccessError(f"Access denied: {e}") from e
                else:
                    logger.error(f"HTTP error in {operation_name}: {e}")
                    if raise_on_error:
                        raise
                return default_return
            except AzureError as e:
                logger.error(f"Azure API error in {operation_name}: {e}")
                if raise_on_error:
                    raise AzureScanError(f"Azure operation failed: {e}") from e
                return default_return
            except Exception as e:
                logger.error(f"Unexpected error in {operation_name}: {e}", exc_info=True)
                if raise_on_error:
                    raise
                return default_return
        
        return wrapper
    return decorator


def handle_resource_access(resource_name: str, resource_type: str = "resource"):
    """
    Context manager for handling resource access with proper error messages.
    
    Usage:
        with handle_resource_access("my-keyvault", "Key Vault"):
            # Access resource
    """
    class ResourceAccessHandler:
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                return False
            
            if isinstance(exc_val, ClientAuthenticationError):
                logger.error(f"Authentication failed accessing {resource_type} '{resource_name}'")
            elif isinstance(exc_val, ResourceNotFoundError):
                logger.warning(f"{resource_type} '{resource_name}' not found")
            elif isinstance(exc_val, HttpResponseError) and exc_val.status_code == 403:
                logger.warning(f"Access denied to {resource_type} '{resource_name}'")
            elif isinstance(exc_val, AzureError):
                logger.error(f"Azure error accessing {resource_type} '{resource_name}': {exc_val}")
            else:
                logger.error(f"Unexpected error accessing {resource_type} '{resource_name}': {exc_val}")
            
            # Don't suppress the exception
            return False
    
    return ResourceAccessHandler()