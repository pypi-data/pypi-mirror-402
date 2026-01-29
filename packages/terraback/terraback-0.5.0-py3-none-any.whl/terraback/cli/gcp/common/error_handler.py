"""Common error handling utilities for GCP operations."""

import logging
from google.api_core import exceptions
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

def handle_gcp_api_error(e, service_name: str, project_id: str) -> bool:
    """
    Handle common GCP API errors gracefully.
    
    Args:
        e: The exception that was raised
        service_name: Name of the GCP service (e.g., 'Redis', 'Cloud Tasks')
        project_id: GCP project ID
    
    Returns:
        bool: True if error was handled gracefully (continue), False if critical error
    """
    if isinstance(e, HttpError):
        error_details = e.error_details or []
        
        # Check if it's a service disabled error
        for detail in error_details:
            if detail.get('@type') == 'type.googleapis.com/google.rpc.ErrorInfo':
                reason = detail.get('reason')
                if reason == 'SERVICE_DISABLED':
                    print(f"Note: {service_name} API is not enabled in project {project_id}")
                    print(f"      Resources will be skipped. Enable the API to scan {service_name} resources.")
                    return True
        
        # Check for permission denied
        if e.resp.status == 403:
            if 'SERVICE_DISABLED' in str(e) or 'API has not been used' in str(e):
                print(f"Note: {service_name} API is not enabled in project {project_id}")
                return True
            else:
                print(f"Warning: Permission denied accessing {service_name} in project {project_id}")
                print(f"         Check IAM permissions for the service account.")
                return True
    
    elif isinstance(e, exceptions.PermissionDenied):
        print(f"Warning: Permission denied accessing {service_name} in project {project_id}")
        return True
    
    elif isinstance(e, exceptions.NotFound):
        print(f"Note: No {service_name} resources found in project {project_id}")
        return True
    
    # For other errors, log and continue
    logger.warning(f"Error scanning {service_name}: {str(e)[:200]}")
    return True

def safe_gcp_operation(operation_func, service_name: str, project_id: str):
    """
    Safely execute a GCP operation with common error handling.
    
    Args:
        operation_func: Function to execute
        service_name: Name of the GCP service
        project_id: GCP project ID
    
    Returns:
        Result of operation_func or empty list if error occurred
    """
    try:
        return operation_func()
    except Exception as e:
        if handle_gcp_api_error(e, service_name, project_id):
            return []
        else:
            raise