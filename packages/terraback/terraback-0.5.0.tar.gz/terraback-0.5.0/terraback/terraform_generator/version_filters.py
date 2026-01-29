"""
Jinja2 filters for handling provider version compatibility.
"""
from typing import Any, Dict, Optional, Tuple
from pathlib import Path
from terraback.utils.provider_version import ProviderVersionManager, Provider


class VersionAwareFilters:
    """Jinja2 filters for version-aware template rendering."""
    
    def __init__(self, provider: Provider = Provider.AZURERM, version: Optional[Tuple[int, int]] = None, terraform_dir: Path = Path(".")):
        """Initialize with provider and version."""
        self.manager = ProviderVersionManager(provider, version)
        if not version:
            # Try to detect version from terraform directory
            self.manager.version = ProviderVersionManager.detect_version(provider, terraform_dir)
    
    def get_filters(self) -> Dict[str, Any]:
        """Get all filters for Jinja2 environment."""
        return {
            'azure_attr': self.azure_attribute_filter,
            'version_gte': self.version_greater_equal,
            'version_lt': self.version_less_than,
            'get_provider_version': self.get_provider_version,
            'is_v3_plus': self.is_version_3_plus,
            'is_v4_plus': self.is_version_4_plus,
        }
    
    def azure_attribute_filter(self, attribute_key: str, resource_type: str = None) -> str:
        """
        Filter to get the correct attribute name based on Azure provider version.
        
        Usage in template:
            {{ 'https_traffic_only' | azure_attr('azurerm_storage_account') }}
        """
        if not resource_type:
            # Try to infer from context if possible
            resource_type = "azurerm_storage_account"  # Default for common use
        
        return self.manager.get_attribute_name(resource_type, attribute_key)
    
    def version_greater_equal(self, major: int, minor: int = 0) -> bool:
        """Check if current version >= specified version."""
        return self.manager.version >= (major, minor)
    
    def version_less_than(self, major: int, minor: int = 0) -> bool:
        """Check if current version < specified version."""
        return self.manager.version < (major, minor)
    
    def get_provider_version(self) -> Tuple[int, int]:
        """Get the current provider version."""
        return self.manager.version
    
    def is_version_3_plus(self) -> bool:
        """Check if using Azure provider v3.x or higher."""
        return self.manager.version[0] >= 3
    
    def is_version_4_plus(self) -> bool:
        """Check if using Azure provider v4.x or higher."""
        return self.manager.version[0] >= 4


def create_version_aware_filters(output_dir: Path = Path("."), provider: Optional[Provider] = None) -> Dict[str, Any]:
    """
    Create version-aware filters for the output directory.
    
    This function detects the provider version from the output directory
    and returns appropriate filters.
    """
    # If no provider specified, try to detect from files or default to Azure for backwards compatibility
    if provider is None:
        # Check if there are any AWS-specific files to determine provider
        aws_files = list(output_dir.glob("**/aws_*.tf")) + list(output_dir.glob("**/s3_*.tf")) + list(output_dir.glob("**/ec2*.tf"))
        azure_files = list(output_dir.glob("**/azurerm_*.tf")) + list(output_dir.glob("**/azure_*.tf"))
        
        if aws_files and not azure_files:
            provider = Provider.AWS
        else:
            provider = Provider.AZURERM  # Default to Azure for backwards compatibility
    
    # Only detect version if we're using the Azure provider to avoid unnecessary warnings
    if provider == Provider.AZURERM:
        version = ProviderVersionManager.detect_version(provider, output_dir)
    else:
        # For non-Azure providers, use a default version to avoid detection warnings
        version = (5, 0) if provider == Provider.AWS else (4, 0)
    
    filters = VersionAwareFilters(provider, version, output_dir)
    return filters.get_filters()