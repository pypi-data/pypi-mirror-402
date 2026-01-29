"""Unit tests for Azure App Services module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from azure.core.exceptions import AzureError

from terraback.cli.azure.compute.app_services import (
    scan_app_service_plans,
    scan_web_apps,
    _get_plan_properties,
    _get_app_configuration,
    _process_app_settings,
    _process_connection_strings,
    _get_auth_settings,
    _get_backup_configuration,
    _get_deployment_slots
)


class TestScanAppServicePlans:
    """Test App Service Plan scanning."""
    
    @patch('terraback.cli.azure.compute.app_services.get_azure_client')
    @patch('terraback.cli.azure.compute.app_services.generate_tf_auto')
    @patch('terraback.cli.azure.compute.app_services.generate_imports_file')
    def test_scan_app_service_plans_success(self, mock_imports, mock_generate, mock_client):
        """Test successful scanning of app service plans."""
        # Mock Azure client and plans
        mock_web_client = Mock()
        mock_client.return_value = mock_web_client
        
        mock_plan = Mock()
        mock_plan.name = "test-plan"
        mock_plan.id = "/subscriptions/123/resourceGroups/test-rg/providers/Microsoft.Web/serverfarms/test-plan"
        mock_plan.location = "eastus"
        mock_plan.sku = Mock(tier="Standard", size="S1", capacity=1)
        mock_plan.kind = "linux"
        mock_plan.reserved = True
        mock_plan.per_site_scaling = False
        mock_plan.maximum_elastic_worker_count = 1
        mock_plan.tags = {"env": "test"}
        mock_plan.as_dict.return_value = {
            "name": "test-plan",
            "id": "/subscriptions/123/resourceGroups/test-rg/providers/Microsoft.Web/serverfarms/test-plan",
            "location": "eastus",
            "tags": {"env": "test"}
        }

        mock_web_client.app_service_plans.list.return_value = [mock_plan]
        
        # Run scan
        output_dir = Path("test_output")
        result = scan_app_service_plans(output_dir, "sub123")
        
        # Verify results
        assert len(result) == 1
        assert result[0]['name'] == "test-plan"
        assert result[0]['resource_group_name'] == "test-rg"
        assert result[0]['os_type'] == "Linux"
        assert result[0]['sku_formatted']['tier'] == "Standard"
        
        # Verify file generation was called
        mock_generate.assert_called_once()
        mock_imports.assert_called_once()
    
    @patch('terraback.cli.azure.compute.app_services.get_azure_client')
    def test_scan_app_service_plans_no_results(self, mock_client):
        """Test scanning when no app service plans found."""
        mock_web_client = Mock()
        mock_client.return_value = mock_web_client
        mock_web_client.app_service_plans.list.return_value = []
        
        result = scan_app_service_plans(Path("test_output"), "sub123")
        
        assert len(result) == 0
    
    @patch('terraback.cli.azure.compute.app_services.get_azure_client')
    def test_scan_app_service_plans_with_resource_group_filter(self, mock_client):
        """Test scanning with resource group filter."""
        mock_web_client = Mock()
        mock_client.return_value = mock_web_client
        
        mock_plan = Mock()
        mock_plan.name = "test-plan"
        mock_plan.id = "/subscriptions/123/resourceGroups/test-rg/providers/Microsoft.Web/serverfarms/test-plan"
        mock_plan.location = "eastus"
        mock_plan.sku = Mock(tier="Standard", size="S1", capacity=1)
        mock_plan.kind = "windows"
        mock_plan.tags = {}
        mock_plan.as_dict.return_value = {
            "name": "test-plan",
            "id": "/subscriptions/123/resourceGroups/test-rg/providers/Microsoft.Web/serverfarms/test-plan",
            "location": "eastus",
            "tags": {}
        }

        mock_web_client.app_service_plans.list_by_resource_group.return_value = [mock_plan]
        
        result = scan_app_service_plans(Path("test_output"), "sub123", "test-rg")
        
        # Verify resource group filter was used
        mock_web_client.app_service_plans.list_by_resource_group.assert_called_with("test-rg")
        assert len(result) == 1
        assert result[0]['os_type'] == "Windows"


class TestScanWebApps:
    """Test Web App scanning."""
    
    @patch('terraback.cli.azure.compute.app_services.get_azure_client')
    @patch('terraback.cli.azure.compute.app_services.generate_tf_auto')
    @patch('terraback.cli.azure.compute.app_services.generate_imports_file')
    def test_scan_web_apps_success(self, mock_imports, mock_generate, mock_client):
        """Test successful scanning of web apps."""
        # Mock Azure client and apps
        mock_web_client = Mock()
        mock_client.return_value = mock_web_client
        
        mock_app = Mock()
        mock_app.name = "test-app"
        mock_app.id = "/subscriptions/123/resourceGroups/test-rg/providers/Microsoft.Web/sites/test-app"
        mock_app.location = "eastus"
        mock_app.kind = "app"  # Regular web app, not function app
        mock_app.tags = {"env": "test"}
        mock_app.as_dict.return_value = {
            "name": "test-app",
            "id": "/subscriptions/123/resourceGroups/test-rg/providers/Microsoft.Web/sites/test-app",
            "location": "eastus",
            "tags": {"env": "test"}
        }

        # Create proper mock app settings
        setting1 = Mock()
        setting1.name = "SETTING1"
        setting1.value = "value1"

        website_setting = Mock()
        website_setting.name = "WEBSITE_NODE_DEFAULT_VERSION"
        website_setting.value = "14.x"

        # Create proper mock connection string
        db_conn = Mock()
        db_conn.name = "DB"
        db_conn.type = "SQLServer"
        db_conn.connection_string = "Server=..."

        mock_config = Mock()
        mock_config.app_settings = [setting1, website_setting]
        mock_config.connection_strings = [db_conn]
        mock_config.as_dict.return_value = {"app_settings": [], "connection_strings": []}
        
        mock_auth = Mock()
        mock_auth.enabled = True
        
        mock_web_client.web_apps.list.return_value = [mock_app]
        mock_web_client.web_apps.get_configuration.return_value = mock_config
        mock_web_client.web_apps.get_auth_settings.return_value = mock_auth
        mock_web_client.web_apps.get_backup_configuration.return_value = None
        mock_web_client.web_apps.list_slots.return_value = []
        
        # Run scan
        output_dir = Path("test_output")
        result = scan_web_apps(output_dir, "sub123")
        
        # Verify results
        assert len(result) == 1
        assert result[0]['name'] == "test-app"
        assert result[0]['resource_group_name'] == "test-rg"
        assert result[0]['app_settings_formatted'] == {"SETTING1": "value1"}  # System setting excluded
        assert len(result[0]['connection_strings_formatted']) == 1
        
        # Verify file generation was called
        mock_generate.assert_called_once()
        mock_imports.assert_called_once()
    
    @patch('terraback.cli.azure.compute.app_services.get_azure_client')
    def test_scan_web_apps_skip_function_apps(self, mock_client):
        """Test that function apps are skipped."""
        mock_web_client = Mock()
        mock_client.return_value = mock_web_client
        
        mock_function_app = Mock()
        mock_function_app.name = "test-func"
        mock_function_app.kind = "functionapp,linux"
        
        mock_web_app = Mock()
        mock_web_app.name = "test-app"
        mock_web_app.id = "/subscriptions/123/resourceGroups/test-rg/providers/Microsoft.Web/sites/test-app"
        mock_web_app.kind = "app"
        mock_web_app.location = "eastus"
        mock_web_app.tags = {}
        mock_web_app.as_dict.return_value = {
            "name": "test-app",
            "id": "/subscriptions/123/resourceGroups/test-rg/providers/Microsoft.Web/sites/test-app",
            "location": "eastus",
            "tags": {}
        }

        mock_config = Mock()
        mock_config.app_settings = []
        mock_config.connection_strings = []
        mock_config.as_dict.return_value = {"app_settings": [], "connection_strings": []}

        mock_web_client.web_apps.list.return_value = [mock_function_app, mock_web_app]
        mock_web_client.web_apps.get_configuration.return_value = mock_config
        mock_web_client.web_apps.get_auth_settings.return_value = None
        mock_web_client.web_apps.get_backup_configuration.return_value = None
        mock_web_client.web_apps.list_slots.return_value = []
        
        result = scan_web_apps(Path("test_output"), "sub123")
        
        # Only web app should be in results
        assert len(result) == 1
        assert result[0]['name'] == "test-app"


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_get_plan_properties(self):
        """Test extraction of plan properties."""
        plan_dict = {}
        plan = Mock()
        plan.reserved = True
        plan.per_site_scaling = True
        plan.maximum_elastic_worker_count = 10
        
        _get_plan_properties(plan_dict, plan)
        
        assert plan_dict['reserved'] == True
        assert plan_dict['per_site_scaling'] == True
        assert plan_dict['maximum_elastic_worker_count'] == 10
    
    def test_process_app_settings(self):
        """Test processing of app settings."""
        app_dict = {}
        config = Mock()

        # Create mock settings with proper name/value attributes
        custom_setting = Mock()
        custom_setting.name = "CUSTOM_SETTING"
        custom_setting.value = "custom_value"

        website_setting = Mock()
        website_setting.name = "WEBSITE_HTTPLOGGING_ENABLED"
        website_setting.value = "true"

        runtime_setting = Mock()
        runtime_setting.name = "FUNCTIONS_WORKER_RUNTIME"
        runtime_setting.value = "python"

        version_setting = Mock()
        version_setting.name = "FUNCTIONS_EXTENSION_VERSION"
        version_setting.value = "~4"

        config.app_settings = [custom_setting, website_setting, runtime_setting, version_setting]

        _process_app_settings(app_dict, config)

        # System settings should be excluded from formatted settings
        assert app_dict['app_settings_formatted'] == {
            "CUSTOM_SETTING": "custom_value",
            "FUNCTIONS_WORKER_RUNTIME": "python",
            "FUNCTIONS_EXTENSION_VERSION": "~4"
        }
    
    def test_process_connection_strings(self):
        """Test processing of connection strings."""
        app_dict = {}
        config = Mock()

        # Create mock connection strings with proper attributes
        db_conn = Mock()
        db_conn.name = "Database"
        db_conn.type = "SQLServer"
        db_conn.connection_string = "Server=localhost;"

        storage_conn = Mock()
        storage_conn.name = "Storage"
        storage_conn.type = "Custom"
        storage_conn.connection_string = "DefaultEndpointsProtocol=https;"

        config.connection_strings = [db_conn, storage_conn]

        _process_connection_strings(app_dict, config)

        assert len(app_dict['connection_strings_formatted']) == 2
        assert app_dict['connection_strings_formatted'][0]['name'] == "Database"
        assert app_dict['connection_strings_formatted'][0]['type'] == "SQLServer"
    
    @patch('terraback.cli.azure.compute.app_services.safe_azure_operation')
    def test_get_app_configuration_error_handling(self, mock_decorator):
        """Test error handling in configuration retrieval."""
        # Mock the decorator to return None on error (as safe_azure_operation does)
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
        mock_client.web_apps.get_configuration.side_effect = AzureError("Access denied")

        app_dict = {'resource_group_name': 'test-rg'}
        result = _get_app_configuration(mock_client, app_dict, 'test-app')

        # Should handle error gracefully
        assert result is None