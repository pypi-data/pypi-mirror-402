"""Common utility functions for Azure resource processing."""

from typing import Optional, Dict, Any, List
import logging
from datetime import timedelta
from azure.core.exceptions import AzureError, ResourceNotFoundError

logger = logging.getLogger(__name__)


def timedelta_to_iso8601(td: timedelta) -> str:
    """
    Convert a timedelta object to ISO 8601 duration string.
    
    Args:
        td: The timedelta object to convert
        
    Returns:
        ISO 8601 duration string (e.g., "PT30M" for 30 minutes)
        
    Example:
        >>> timedelta_to_iso8601(timedelta(minutes=30))
        'PT30M'
        >>> timedelta_to_iso8601(timedelta(days=1, hours=2, minutes=30))
        'P1DT2H30M'
    """
    if not isinstance(td, timedelta):
        return str(td)  # Return as-is if not a timedelta
    
    total_seconds = int(td.total_seconds())
    
    # Handle negative durations
    if total_seconds < 0:
        return "PT0S"
    
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    # Build the duration string
    result = "P"
    if days:
        result += f"{days}D"
    
    time_part = ""
    if hours:
        time_part += f"{hours}H"
    if minutes:
        time_part += f"{minutes}M"
    if seconds:
        time_part += f"{seconds}S"
    
    if time_part:
        result += "T" + time_part
    elif not days:
        # If no components, return PT0S
        result = "PT0S"
    
    return result


def extract_resource_group_from_id(resource_id: Optional[str]) -> Optional[str]:
    """
    Extract resource group name from an Azure resource ID.
    
    Azure resource IDs follow the pattern:
    /subscriptions/{subscription}/resourceGroups/{resource-group}/providers/{provider}/{type}/{name}
    
    Args:
        resource_id: The Azure resource ID to parse
        
    Returns:
        The resource group name, or None if the ID is invalid
        
    Example:
        >>> extract_resource_group_from_id("/subscriptions/123/resourceGroups/my-rg/providers/Microsoft.Compute/virtualMachines/vm1")
        'my-rg'
    """
    if not resource_id:
        return None
    
    parts = resource_id.split('/')
    
    # Resource group is typically at index 4
    if len(parts) >= 5 and parts[3].lower() == 'resourcegroups':
        return parts[4]
    
    logger.warning(f"Could not extract resource group from ID: {resource_id}")
    return None


def sanitize_resource_name(name: str) -> str:
    """
    Sanitize a resource name for use as a Terraform resource identifier.
    
    Terraform resource names must:
    - Start with a letter or underscore
    - Contain only letters, digits, underscores, and hyphens
    
    Args:
        name: The resource name to sanitize
        
    Returns:
        A sanitized name suitable for use as a Terraform resource identifier
        
    Example:
        >>> sanitize_resource_name("my-resource.name")
        'my_resource_name'
    """
    if not name:
        return "unnamed"
    
    # Replace common invalid characters
    sanitized = name.replace('-', '_').replace('.', '_').replace(' ', '_')
    
    # Ensure it starts with a letter or underscore
    if sanitized and sanitized[0].isdigit():
        sanitized = f"r_{sanitized}"
    
    # Convert to lowercase for consistency
    return sanitized.lower()


def format_resource_dict(resource: Any, resource_type: str) -> Dict[str, Any]:
    """
    Format a common Azure resource into a dictionary with standard fields.
    
    Args:
        resource: The Azure SDK resource object
        resource_type: The type of resource (e.g., 'virtual_machine')
        
    Returns:
        A dictionary with standardized fields including name_sanitized and resource_group_name
    """
    resource_dict = resource.as_dict() if hasattr(resource, 'as_dict') else {}
    
    # Add sanitized name
    if hasattr(resource, 'name'):
        resource_dict['name'] = resource.name
        resource_dict['name_sanitized'] = sanitize_resource_name(resource.name)
    
    # Extract resource group
    if hasattr(resource, 'id') and resource.id:
        resource_dict['id'] = resource.id
        resource_dict['resource_group_name'] = extract_resource_group_from_id(resource.id)
    
    # Add resource type for tracking
    resource_dict['_resource_type'] = resource_type
    
    return resource_dict


def handle_azure_errors(func):
    """
    Decorator to handle common Azure SDK errors with appropriate logging.
    
    Usage:
        @handle_azure_errors
        def scan_resources():
            # Azure SDK calls here
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ResourceNotFoundError as e:
            logger.error(f"Resource not found in {func.__name__}: {e}")
            raise
        except AzureError as e:
            logger.error(f"Azure API error in {func.__name__}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise
    
    return wrapper


def batch_process_resources(
    resources: List[Any],
    process_func,
    batch_size: int = 50,
    resource_type: str = "resource"
) -> List[Dict[str, Any]]:
    """
    Process Azure resources in batches to avoid API limits.
    
    Args:
        resources: List of resources to process
        process_func: Function to process each resource
        batch_size: Number of resources to process at once
        resource_type: Type of resource for logging
        
    Returns:
        List of processed resource dictionaries
    """
    processed = []
    total = len(list(resources))
    
    for i in range(0, total, batch_size):
        batch = resources[i:i + batch_size]
        logger.info(f"Processing {resource_type} batch {i//batch_size + 1} of {(total + batch_size - 1)//batch_size}")
        
        for resource in batch:
            try:
                result = process_func(resource)
                if result:
                    processed.append(result)
            except Exception as e:
                logger.warning(f"Failed to process {resource_type}: {e}")
                continue
    
    return processed


def normalize_resource_id(resource_id: str) -> str:
    """
    Normalize an Azure resource ID to have consistent casing.
    
    Azure resource IDs should have consistent casing for:
    - /subscriptions/ (lowercase)
    - /resourceGroups/ (camelCase)
    - /providers/Microsoft.XXX (PascalCase for provider name)
    - Resource type segments like dnsZones (camelCase)
    
    Args:
        resource_id: The Azure resource ID to normalize
        
    Returns:
        A normalized resource ID with consistent casing
    """
    if not resource_id:
        return resource_id
    
    # Split the ID into segments
    segments = resource_id.split('/')
    normalized_segments = []
    
    for i, segment in enumerate(segments):
        if i == 0:  # Empty string before leading /
            normalized_segments.append(segment)
        elif i == 1 and segment.lower() == 'subscriptions':
            normalized_segments.append('subscriptions')
        elif i == 3 and segment.lower() == 'resourcegroups':
            normalized_segments.append('resourceGroups')
        elif i == 5 and segment.lower() == 'providers':
            normalized_segments.append('providers')
        elif i == 6 and segment.lower().startswith('microsoft.'):
            # Provider name should be PascalCase (e.g., Microsoft.Network)
            parts = segment.split('.')
            if len(parts) >= 2:
                parts[0] = 'Microsoft'
                # Special case for ManagedIdentity (camelCase in the second part)
                if parts[1].lower() == 'managedidentity':
                    parts[1] = 'ManagedIdentity'
                else:
                    # Capitalize first letter of each service name part
                    for j in range(1, len(parts)):
                        if parts[j]:
                            parts[j] = parts[j][0].upper() + parts[j][1:].lower()
                normalized_segments.append('.'.join(parts))
            else:
                normalized_segments.append(segment)
        elif i > 6 and i % 2 == 1:  # Resource type segments (odd positions after provider)
            # Common resource types that should be camelCase
            resource_type_map = {
                'dnszones': 'dnsZones',
                'virtualnetworks': 'virtualNetworks',
                'virtualmachines': 'virtualMachines',
                'storageaccounts': 'storageAccounts',
                'networkinterfaces': 'networkInterfaces',
                'publicipaddresses': 'publicIPAddresses',
                'networksecuritygroups': 'networkSecurityGroups',
                'loadbalancers': 'loadBalancers',
                'applicationgateways': 'applicationGateways',
                'userassignedidentities': 'userAssignedIdentities',
                'actiongroups': 'actionGroups',
                'loganalyticsworkspaces': 'logAnalyticsWorkspaces',
                'serverfarms': 'serverFarms',
                'sites': 'sites',
                'vaults': 'vaults',
            }
            normalized_segments.append(resource_type_map.get(segment.lower(), segment))
        else:
            # Keep resource names and other segments as-is
            normalized_segments.append(segment)
    
    return '/'.join(normalized_segments)


def filter_system_resources(resources: List[Dict[str, Any]], system_names: List[str] = None) -> List[Dict[str, Any]]:
    """
    Filter out system resources that shouldn't be managed by Terraform.
    
    Args:
        resources: List of resource dictionaries
        system_names: Additional system resource names to filter
        
    Returns:
        Filtered list of resources
    """
    default_system_names = ['master', 'msdb', 'model', 'tempdb', 'default', 'system']
    
    if system_names:
        default_system_names.extend(system_names)
    
    return [
        resource for resource in resources
        if resource.get('name', '').lower() not in default_system_names
    ]