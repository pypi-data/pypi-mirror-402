"""Unit tests for Azure common utilities."""

import pytest
from unittest.mock import Mock, patch
from azure.core.exceptions import AzureError, ResourceNotFoundError

from terraback.cli.azure.common.utils import (
    extract_resource_group_from_id,
    sanitize_resource_name,
    format_resource_dict,
    handle_azure_errors,
    batch_process_resources,
    filter_system_resources
)


class TestExtractResourceGroup:
    """Test resource group extraction from Azure resource IDs."""
    
    def test_valid_resource_id(self):
        """Test extraction from valid resource ID."""
        resource_id = "/subscriptions/123/resourceGroups/my-rg/providers/Microsoft.Compute/virtualMachines/vm1"
        assert extract_resource_group_from_id(resource_id) == "my-rg"
    
    def test_invalid_resource_id(self):
        """Test extraction from invalid resource ID."""
        assert extract_resource_group_from_id("/invalid/id") is None
        assert extract_resource_group_from_id("") is None
        assert extract_resource_group_from_id(None) is None
    
    def test_different_casing(self):
        """Test extraction with different casing of resourceGroups."""
        resource_id = "/subscriptions/123/resourcegroups/my-rg/providers/Microsoft.Compute/virtualMachines/vm1"
        assert extract_resource_group_from_id(resource_id) == "my-rg"


class TestSanitizeResourceName:
    """Test resource name sanitization."""
    
    def test_basic_sanitization(self):
        """Test basic character replacement."""
        assert sanitize_resource_name("my-resource") == "my_resource"
        assert sanitize_resource_name("my.resource") == "my_resource"
        assert sanitize_resource_name("my resource") == "my_resource"
    
    def test_numeric_prefix(self):
        """Test handling of names starting with numbers."""
        assert sanitize_resource_name("123-resource") == "r_123_resource"
    
    def test_empty_name(self):
        """Test handling of empty names."""
        assert sanitize_resource_name("") == "unnamed"
    
    def test_lowercase_conversion(self):
        """Test conversion to lowercase."""
        assert sanitize_resource_name("MyResource") == "myresource"


class TestFormatResourceDict:
    """Test resource dictionary formatting."""
    
    def test_basic_formatting(self):
        """Test basic resource formatting."""
        resource = Mock()
        resource.name = "test-resource"
        resource.id = "/subscriptions/123/resourceGroups/test-rg/providers/Microsoft.Compute/virtualMachines/vm1"
        resource.as_dict.return_value = {"name": "test-resource"}
        
        result = format_resource_dict(resource, "virtual_machine")
        
        assert result["name"] == "test-resource"
        assert result["name_sanitized"] == "test_resource"
        assert result["resource_group_name"] == "test-rg"
        assert result["_resource_type"] == "virtual_machine"
    
    def test_no_as_dict_method(self):
        """Test handling of resources without as_dict method."""
        resource = Mock(spec=[])
        resource.name = "test"
        resource.id = "/subscriptions/123/resourceGroups/rg/providers/Test/test"
        
        result = format_resource_dict(resource, "test")
        
        assert result["name"] == "test"
        assert result["name_sanitized"] == "test"


class TestHandleAzureErrors:
    """Test Azure error handling decorator."""
    
    def test_successful_function(self):
        """Test decorator with successful function."""
        @handle_azure_errors
        def successful_func():
            return "success"
        
        assert successful_func() == "success"
    
    def test_resource_not_found_error(self):
        """Test handling of ResourceNotFoundError."""
        @handle_azure_errors
        def failing_func():
            raise ResourceNotFoundError("Resource not found")
        
        with pytest.raises(ResourceNotFoundError):
            failing_func()
    
    def test_azure_error(self):
        """Test handling of generic AzureError."""
        @handle_azure_errors
        def failing_func():
            raise AzureError("Azure error")
        
        with pytest.raises(AzureError):
            failing_func()
    
    def test_unexpected_error(self):
        """Test handling of unexpected errors."""
        @handle_azure_errors
        def failing_func():
            raise ValueError("Unexpected error")
        
        with pytest.raises(ValueError):
            failing_func()


class TestBatchProcessResources:
    """Test batch processing of resources."""
    
    def test_basic_batch_processing(self):
        """Test basic batch processing."""
        # Create mocks with explicit name property set
        resources = []
        for i in range(5):
            resource = Mock()
            resource.name = f"resource{i}"
            resources.append(resource)

        def process_func(resource):
            return {"name": resource.name}

        results = batch_process_resources(resources, process_func, batch_size=2)

        assert len(results) == 5
        assert all(r["name"] == f"resource{i}" for i, r in enumerate(results))
    
    def test_error_handling_in_batch(self):
        """Test error handling during batch processing."""
        # Create mocks with explicit name property set
        resources = []
        for i in range(3):
            resource = Mock()
            resource.name = f"resource{i}"
            resources.append(resource)

        def process_func(resource):
            if resource.name == "resource1":
                raise ValueError("Processing error")
            return {"name": resource.name}

        results = batch_process_resources(resources, process_func)

        assert len(results) == 2  # One failed
        assert results[0]["name"] == "resource0"
        assert results[1]["name"] == "resource2"


class TestFilterSystemResources:
    """Test system resource filtering."""
    
    def test_default_filtering(self):
        """Test filtering with default system names."""
        resources = [
            {"name": "master"},
            {"name": "user-resource"},
            {"name": "system"},
            {"name": "my-app"}
        ]
        
        filtered = filter_system_resources(resources)
        
        assert len(filtered) == 2
        assert filtered[0]["name"] == "user-resource"
        assert filtered[1]["name"] == "my-app"
    
    def test_custom_filtering(self):
        """Test filtering with custom system names."""
        resources = [
            {"name": "default"},
            {"name": "custom-system"},
            {"name": "user-resource"}
        ]
        
        filtered = filter_system_resources(resources, ["custom-system"])
        
        assert len(filtered) == 1
        assert filtered[0]["name"] == "user-resource"
    
    def test_case_insensitive_filtering(self):
        """Test case-insensitive filtering."""
        resources = [
            {"name": "Master"},
            {"name": "SYSTEM"},
            {"name": "user-resource"}
        ]
        
        filtered = filter_system_resources(resources)
        
        assert len(filtered) == 1
        assert filtered[0]["name"] == "user-resource"