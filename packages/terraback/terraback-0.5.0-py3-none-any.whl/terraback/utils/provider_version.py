"""
Provider version detection and compatibility management for Terraform providers.
"""
import re
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from enum import Enum


class Provider(Enum):
    """Supported Terraform providers."""
    AZURERM = "azurerm"
    AWS = "aws"
    GOOGLE = "google"


class ProviderVersionManager:
    """Manages provider version detection and attribute mappings."""
    
    # Attribute mappings for different provider versions
    # Format: {provider: {resource_type: {attribute: {version: name}}}}
    ATTRIBUTE_MAPPINGS = {
        Provider.AZURERM: {
            "azurerm_storage_account": {
                "https_traffic_only": {
                    (2, 0): "enable_https_traffic_only",
                    (3, 0): "https_traffic_only_enabled",
                    (4, 0): "https_traffic_only_enabled",
                },
                "blob_public_access": {
                    (2, 0): "allow_blob_public_access",
                    (3, 0): "allow_nested_items_to_be_public",
                    (4, 0): "allow_nested_items_to_be_public",
                },
                "min_tls_version_default": {
                    (2, 0): "TLS1_0",
                    (3, 0): "TLS1_2",
                    (4, 0): "TLS1_2",
                }
            },
            "azurerm_app_service_plan": {
                "sku_size": {
                    (2, 0): "sku.size",  # Nested in v2
                    (3, 0): "sku_name",   # Flattened in v3+
                    (4, 0): "sku_name",
                }
            },
            "azurerm_kubernetes_cluster": {
                "default_node_pool_name": {
                    (2, 0): "default_node_pool.name",
                    (3, 0): "default_node_pool.name",
                    (4, 0): "default_node_pool.name",
                }
            }
        },
        Provider.AWS: {
            # AWS provider mappings
            "aws_instance": {
                "instance_type": {
                    (3, 0): "instance_type",
                    (4, 0): "instance_type",
                    (5, 0): "instance_type",
                }
            }
        }
    }
    
    def __init__(self, provider: Provider, version: Optional[Tuple[int, int]] = None):
        """
        Initialize the version manager.
        
        Args:
            provider: The provider type
            version: Optional version tuple (major, minor). If None, will detect.
        """
        self.provider = provider
        self.version = version or self.detect_version(provider)
    
    @staticmethod
    def detect_version(provider: Provider, terraform_dir: Path = Path(".")) -> Tuple[int, int]:
        """
        Detect the provider version from terraform configuration or state.
        
        Args:
            provider: The provider to check
            terraform_dir: Directory containing terraform files
            
        Returns:
            Tuple of (major, minor) version numbers
        """
        # Try multiple detection methods
        version = None
        
        # Method 1: Check .terraform.lock.hcl
        lock_file = terraform_dir / ".terraform.lock.hcl"
        if lock_file.exists():
            version = ProviderVersionManager._parse_lock_file(lock_file, provider)
        
        # Method 2: Check provider.tf or versions.tf
        if not version:
            for tf_file in ["provider.tf", "versions.tf", "terraform.tf"]:
                tf_path = terraform_dir / tf_file
                if tf_path.exists():
                    version = ProviderVersionManager._parse_tf_file(tf_path, provider)
                    if version:
                        break
        
        # Method 3: Run terraform version command
        if not version:
            version = ProviderVersionManager._get_version_from_terraform(provider, terraform_dir)
        
        # Default to latest known version if detection fails
        if not version:
            defaults = {
                Provider.AZURERM: (4, 0),
                Provider.AWS: (5, 0),
                Provider.GOOGLE: (5, 0),
            }
            version = defaults.get(provider, (4, 0))
            print(f"Warning: Could not detect {provider.value} version. Using default: {version}")
        
        return version
    
    @staticmethod
    def _parse_lock_file(lock_file: Path, provider: Provider) -> Optional[Tuple[int, int]]:
        """Parse .terraform.lock.hcl for provider version."""
        try:
            content = lock_file.read_text()
            provider_block = re.search(
                rf'provider\s+"registry\.terraform\.io/hashicorp/{provider.value}"\s*{{[^}}]*version\s*=\s*"([^"]+)"',
                content,
                re.DOTALL
            )
            if provider_block:
                version_str = provider_block.group(1)
                return ProviderVersionManager._parse_version_string(version_str)
        except Exception as e:
            print(f"Error parsing lock file: {e}")
        return None
    
    @staticmethod
    def _parse_tf_file(tf_file: Path, provider: Provider) -> Optional[Tuple[int, int]]:
        """Parse terraform file for provider version constraint."""
        try:
            content = tf_file.read_text()
            
            # Look for required_providers block
            pattern = rf'{provider.value}\s*=\s*{{[^}}]*version\s*=\s*"([^"]+)"'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                version_constraint = match.group(1)
                # Parse constraint like "~> 4.0" or ">= 3.0, < 4.0"
                return ProviderVersionManager._parse_version_constraint(version_constraint)
        except Exception as e:
            print(f"Error parsing terraform file: {e}")
        return None
    
    @staticmethod
    def _get_version_from_terraform(provider: Provider, terraform_dir: Path) -> Optional[Tuple[int, int]]:
        """Get provider version by running terraform providers command."""
        try:
            # First ensure terraform is initialized
            result = subprocess.run(
                ["terraform", "providers", "-json"],
                cwd=terraform_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                providers_data = json.loads(result.stdout)
                # Parse the JSON output for provider version
                for p in providers_data.get("provider_selections", {}).values():
                    if provider.value in p.get("source", ""):
                        version_str = p.get("version", "")
                        if version_str:
                            return ProviderVersionManager._parse_version_string(version_str)
        except Exception as e:
            print(f"Error running terraform command: {e}")
        return None
    
    @staticmethod
    def _parse_version_string(version_str: str) -> Tuple[int, int]:
        """Parse a version string like '4.39.0' to (4, 39)."""
        parts = version_str.split('.')
        try:
            major = int(parts[0]) if parts else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            return (major, minor)
        except (ValueError, IndexError):
            return (4, 0)  # Default fallback
    
    @staticmethod
    def _parse_version_constraint(constraint: str) -> Tuple[int, int]:
        """Parse version constraint like '~> 4.0' or '>= 3.0'."""
        # Extract numbers from constraint
        numbers = re.findall(r'\d+', constraint)
        if numbers:
            major = int(numbers[0])
            minor = int(numbers[1]) if len(numbers) > 1 else 0
            return (major, minor)
        return (4, 0)  # Default fallback
    
    def get_attribute_name(self, resource_type: str, attribute_key: str) -> str:
        """
        Get the correct attribute name for a resource type based on provider version.
        
        Args:
            resource_type: The terraform resource type (e.g., 'azurerm_storage_account')
            attribute_key: The logical attribute key (e.g., 'https_traffic_only')
            
        Returns:
            The correct attribute name for the current provider version
        """
        if self.provider not in self.ATTRIBUTE_MAPPINGS:
            return attribute_key
        
        provider_mappings = self.ATTRIBUTE_MAPPINGS[self.provider]
        if resource_type not in provider_mappings:
            return attribute_key
        
        resource_mappings = provider_mappings[resource_type]
        if attribute_key not in resource_mappings:
            return attribute_key
        
        # Find the appropriate version mapping
        version_mappings = resource_mappings[attribute_key]
        
        # Find the closest version match
        closest_version = None
        for version in sorted(version_mappings.keys(), reverse=True):
            if self.version >= version:
                closest_version = version
                break
        
        if closest_version:
            return version_mappings[closest_version]
        
        # Return first available if no match
        return list(version_mappings.values())[0]
    
    def get_resource_attributes(self, resource_type: str, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform attributes for a resource based on provider version.
        
        Args:
            resource_type: The terraform resource type
            attributes: The attributes to transform
            
        Returns:
            Transformed attributes compatible with the provider version
        """
        if self.provider not in self.ATTRIBUTE_MAPPINGS:
            return attributes
        
        if resource_type not in self.ATTRIBUTE_MAPPINGS[self.provider]:
            return attributes
        
        transformed = {}
        for key, value in attributes.items():
            # Check if this attribute needs transformation
            new_key = self.get_attribute_name(resource_type, key)
            transformed[new_key] = value
        
        return transformed
    
    def is_attribute_supported(self, resource_type: str, attribute_key: str) -> bool:
        """
        Check if an attribute is supported in the current provider version.
        
        Args:
            resource_type: The terraform resource type
            attribute_key: The attribute to check
            
        Returns:
            True if the attribute is supported
        """
        # Check if we have specific version requirements for this attribute
        if self.provider in self.ATTRIBUTE_MAPPINGS:
            provider_mappings = self.ATTRIBUTE_MAPPINGS[self.provider]
            if resource_type in provider_mappings:
                if attribute_key in provider_mappings[resource_type]:
                    version_mappings = provider_mappings[resource_type][attribute_key]
                    for version in version_mappings:
                        if self.version >= version:
                            return True
                    return False
        return True  # Assume supported if not in mappings
    
    def get_provider_version_string(self) -> str:
        """Get the version string for terraform configuration."""
        major, minor = self.version
        return f"~> {major}.{minor}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template context."""
        return {
            "provider": self.provider.value,
            "version": self.version,
            "version_string": self.get_provider_version_string(),
            "major": self.version[0],
            "minor": self.version[1],
        }


# Convenience functions for templates
def get_azure_attribute(resource_type: str, attribute_key: str, version: Optional[Tuple[int, int]] = None) -> str:
    """Get Azure resource attribute name for the current or specified version."""
    manager = ProviderVersionManager(Provider.AZURERM, version)
    return manager.get_attribute_name(resource_type, attribute_key)


def detect_provider_version(provider_name: str, terraform_dir: Path = Path(".")) -> Tuple[int, int]:
    """Detect provider version from terraform configuration."""
    try:
        provider = Provider(provider_name.lower())
        return ProviderVersionManager.detect_version(provider, terraform_dir)
    except (ValueError, KeyError):
        print(f"Unknown provider: {provider_name}")
        return (4, 0)  # Default