"""Unit tests for Azure Container Registry module."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from terraback.cli.azure.container.container_registries import (
    scan_container_registries,
    _format_sku,
    _format_network_rules,
    _format_policies,
    _format_encryption,
    _get_webhooks,
    _get_replications
)


class TestScanContainerRegistries:
    """Test Container Registry scanning."""
    
    @patch('terraback.cli.azure.container.container_registries.get_azure_client')
    @patch('terraback.cli.azure.container.container_registries.generate_tf_auto')
    @patch('terraback.cli.azure.container.container_registries.generate_imports_file')
    def test_scan_container_registries_success(self, mock_imports, mock_generate, mock_client):
        """Test successful scanning of container registries."""
        # Mock Azure client and registries
        mock_acr_client = Mock()
        mock_client.return_value = mock_acr_client
        
        mock_registry = Mock()
        mock_registry.name = "testregistry"
        mock_registry.id = "/subscriptions/123/resourceGroups/test-rg/providers/Microsoft.ContainerRegistry/registries/testregistry"
        mock_registry.location = "eastus"

        # Create proper SKU mock
        mock_sku = Mock()
        mock_sku.name = "Premium"
        mock_sku.tier = "Premium"
        mock_registry.sku = mock_sku

        mock_registry.tags = {"env": "test"}
        mock_registry.as_dict.return_value = {
            "name": "testregistry",
            "id": "/subscriptions/123/resourceGroups/test-rg/providers/Microsoft.ContainerRegistry/registries/testregistry",
            "location": "eastus",
            "tags": {"env": "test"}
        }

        # Mock IP rule
        ip_rule = Mock()
        ip_rule.value = "10.0.0.1/32"

        # Mock VNet rule
        vnet_rule = Mock()
        vnet_rule.virtual_network_resource_id = "/subscriptions/123/vnet"

        # Mock network rules
        mock_registry.network_rule_set = Mock(
            default_action="Deny",
            ip_rules=[ip_rule],
            virtual_network_rules=[vnet_rule]
        )

        # Mock policies
        mock_registry.policies = Mock(
            retention_policy=Mock(status="enabled", days=30),
            trust_policy=Mock(status="enabled")
        )

        # Mock encryption
        mock_registry.encryption = Mock(
            status="enabled",
            key_vault_properties=Mock(key_identifier="https://vault.azure.net/keys/key1")
        )

        mock_acr_client.registries.list.return_value = [mock_registry]
        
        # Mock webhooks
        mock_webhook = Mock()
        mock_webhook.name = "webhook1"
        mock_webhook.config = Mock(service_uri="https://example.com", actions=["push"])
        mock_webhook.status = "enabled"
        mock_webhook.scope = "repository:*:*"
        mock_acr_client.webhooks.list.return_value = [mock_webhook]

        # Mock replications
        mock_replication = Mock()
        mock_replication.location = "westus"
        mock_replication.tags = {"purpose": "dr"}
        mock_acr_client.replications.list.return_value = [mock_replication]
        
        # Run scan
        output_dir = Path("test_output")
        result = scan_container_registries(output_dir, "sub123")
        
        # Verify results
        assert len(result) == 1
        assert result[0]['name'] == "testregistry"
        assert result[0]['resource_group_name'] == "test-rg"
        assert result[0]['sku'] == "Premium"
        assert result[0]['network_rule_set_formatted']['default_action'] == "Deny"
        assert len(result[0]['webhooks']) == 1
        assert len(result[0]['georeplications']) == 1
        
        # Verify file generation was called
        mock_generate.assert_called_once()
        mock_imports.assert_called_once()
    
    @patch('terraback.cli.azure.container.container_registries.get_azure_client')
    def test_scan_container_registries_with_resource_group_filter(self, mock_client):
        """Test scanning with resource group filter."""
        mock_acr_client = Mock()
        mock_client.return_value = mock_acr_client
        
        mock_registry = Mock()
        mock_registry.name = "testregistry"
        mock_registry.id = "/subscriptions/123/resourceGroups/test-rg/providers/Microsoft.ContainerRegistry/registries/testregistry"
        mock_registry.location = "eastus"

        # Create proper SKU mock
        mock_sku = Mock()
        mock_sku.name = "Basic"
        mock_sku.tier = "Basic"
        mock_registry.sku = mock_sku

        mock_registry.tags = {}
        mock_registry.as_dict.return_value = {
            "name": "testregistry",
            "id": "/subscriptions/123/resourceGroups/test-rg/providers/Microsoft.ContainerRegistry/registries/testregistry",
            "location": "eastus",
            "tags": {}
        }

        # Set optional attributes to None to avoid formatting errors
        mock_registry.network_rule_set = None
        mock_registry.policies = None
        mock_registry.encryption = None

        mock_acr_client.registries.list_by_resource_group.return_value = [mock_registry]
        mock_acr_client.webhooks.list.return_value = []
        mock_acr_client.replications.list.return_value = []
        
        result = scan_container_registries(Path("test_output"), "sub123", "test-rg")
        
        # Verify resource group filter was used
        mock_acr_client.registries.list_by_resource_group.assert_called_with("test-rg")
        assert len(result) == 1


class TestFormatFunctions:
    """Test formatting helper functions."""
    
    def test_format_sku(self):
        """Test SKU formatting."""
        registry_dict = {}
        registry = Mock()

        # Create proper SKU mock with attributes
        mock_sku = Mock()
        mock_sku.name = "Premium"
        mock_sku.tier = "Premium"
        registry.sku = mock_sku

        _format_sku(registry_dict, registry)

        assert registry_dict['sku'] == "Premium"
        assert registry_dict['sku_tier'] == "Premium"
    
    def test_format_network_rules(self):
        """Test network rules formatting."""
        registry_dict = {}
        registry = Mock()
        registry.network_rule_set = Mock(
            default_action="Allow",
            ip_rules=[
                Mock(value="192.168.1.0/24"),
                Mock(value="10.0.0.0/8")
            ],
            virtual_network_rules=[
                Mock(virtual_network_resource_id="/subscriptions/123/vnet1"),
                Mock(virtual_network_resource_id="/subscriptions/123/vnet2")
            ]
        )
        
        _format_network_rules(registry_dict, registry)
        
        assert registry_dict['network_rule_set_formatted']['default_action'] == "Allow"
        assert len(registry_dict['network_rule_set_formatted']['ip_rules']) == 2
        assert len(registry_dict['network_rule_set_formatted']['virtual_network_rules']) == 2
    
    def test_format_network_rules_none(self):
        """Test network rules formatting when not present."""
        registry_dict = {}
        registry = Mock()
        registry.network_rule_set = None
        
        _format_network_rules(registry_dict, registry)
        
        assert 'network_rule_set_formatted' not in registry_dict
    
    def test_format_policies(self):
        """Test policies formatting."""
        registry_dict = {}
        registry = Mock()
        registry.policies = Mock(
            retention_policy=Mock(status="enabled", days=7),
            trust_policy=Mock(status="disabled")
        )
        
        _format_policies(registry_dict, registry)
        
        assert registry_dict['retention_policy_formatted']['enabled'] == True
        assert registry_dict['retention_policy_formatted']['days'] == 7
        assert registry_dict['trust_policy_formatted']['enabled'] == False
    
    def test_format_encryption(self):
        """Test encryption formatting."""
        registry_dict = {}
        registry = Mock()
        registry.encryption = Mock(
            status="enabled",
            key_vault_properties=Mock(key_identifier="https://keyvault.vault.azure.net/keys/key1/version1")
        )
        
        _format_encryption(registry_dict, registry)
        
        assert registry_dict['encryption_formatted']['enabled'] == True
        assert registry_dict['encryption_formatted']['key_vault_key_id'] == "https://keyvault.vault.azure.net/keys/key1/version1"
    
    def test_format_encryption_disabled(self):
        """Test encryption formatting when disabled."""
        registry_dict = {}
        registry = Mock()
        registry.encryption = Mock(
            status="disabled",
            key_vault_properties=None
        )
        
        _format_encryption(registry_dict, registry)
        
        assert registry_dict['encryption_formatted']['enabled'] == False
        assert registry_dict['encryption_formatted']['key_vault_key_id'] is None


class TestGetFunctions:
    """Test data retrieval helper functions."""
    
    @patch('terraback.cli.azure.container.container_registries.safe_azure_operation')
    def test_get_webhooks(self, mock_decorator):
        """Test webhook retrieval."""
        # Mock the decorator to apply the actual function
        mock_decorator.return_value = lambda f: f

        mock_client = Mock()

        # Create proper webhook mocks with attributes
        mock_webhook1 = Mock()
        mock_webhook1.name = "webhook1"
        mock_webhook1.config = Mock(service_uri="https://hook1.com", actions=["push", "delete"])
        mock_webhook1.status = "enabled"
        mock_webhook1.scope = "repository:myrepo:*"

        mock_webhook2 = Mock()
        mock_webhook2.name = "webhook2"
        mock_webhook2.config = None  # Test handling of missing config
        mock_webhook2.status = "disabled"
        mock_webhook2.scope = None

        mock_client.webhooks.list.return_value = [mock_webhook1, mock_webhook2]

        registry_dict = {'resource_group_name': 'test-rg'}
        result = _get_webhooks(mock_client, registry_dict, 'testregistry')

        assert len(result) == 2
        assert result[0]['name'] == "webhook1"
        assert result[0]['service_uri'] == "https://hook1.com"
        assert result[0]['actions'] == ["push", "delete"]
        assert result[1]['service_uri'] is None
        assert result[1]['actions'] == []
    
    @patch('terraback.cli.azure.container.container_registries.safe_azure_operation')
    def test_get_replications(self, mock_decorator):
        """Test replication retrieval."""
        # Mock the decorator to apply the actual function
        mock_decorator.return_value = lambda f: f
        
        mock_client = Mock()
        mock_replication1 = Mock(location="westus", tags={"purpose": "dr"})
        mock_replication2 = Mock(location="eastus", tags={})  # Home location
        mock_replication3 = Mock(location="northeurope", tags={"region": "eu"})
        
        mock_client.replications.list.return_value = [
            mock_replication1,
            mock_replication2,
            mock_replication3
        ]
        
        registry_dict = {'resource_group_name': 'test-rg'}
        result = _get_replications(mock_client, registry_dict, 'testregistry', 'eastus')
        
        # Should exclude home location (eastus)
        assert len(result) == 2
        assert result[0]['location'] == "westus"
        assert result[1]['location'] == "northeurope"
    
    @patch('terraback.cli.azure.container.container_registries.safe_azure_operation')
    def test_get_webhooks_error_handling(self, mock_decorator):
        """Test webhook retrieval error handling."""
        # Mock the decorator to return empty list on error
        def mock_safe_operation(op_name, default_return):
            def decorator(func):
                def wrapper(*args, **kwargs):
                    try:
                        return func(*args, **kwargs)
                    except Exception:
                        return default_return
                return wrapper
            return decorator
        
        mock_decorator.side_effect = mock_safe_operation
        
        mock_client = Mock()
        mock_client.webhooks.list.side_effect = Exception("Access denied")
        
        registry_dict = {'resource_group_name': 'test-rg'}
        result = _get_webhooks(mock_client, registry_dict, 'testregistry')
        
        # Should return empty list on error
        assert result == []