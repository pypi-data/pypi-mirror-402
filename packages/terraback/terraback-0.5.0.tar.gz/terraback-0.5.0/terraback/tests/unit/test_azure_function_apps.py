"""Unit tests for Azure Function Apps scanning."""

from pathlib import Path
from unittest.mock import Mock, patch

from terraback.cli.azure.compute.function_apps import scan_function_apps


@patch('terraback.core.license.check_feature_access', return_value=True)
@patch('terraback.cli.azure.compute.function_apps.generate_imports_file')
@patch('terraback.cli.azure.compute.function_apps.generate_tf_auto')
@patch('terraback.cli.azure.compute.function_apps.get_azure_client')
def test_scan_function_apps_split_imports_by_os(mock_client, mock_tf, mock_imports, _):
    """Ensure imports are generated separately for Linux and Windows apps."""
    web_client = Mock()
    mock_client.return_value = web_client

    # Mock Linux function app
    linux_app = Mock()
    linux_app.name = 'lin-app'
    linux_app.id = '/subscriptions/123/resourceGroups/rg/providers/Microsoft.Web/sites/lin-app'
    linux_app.kind = 'functionapp,linux'
    linux_app.location = 'eastus'
    linux_app.server_farm_id = '/subscriptions/123/resourceGroups/rg/providers/Microsoft.Web/serverfarms/plan1'
    linux_app.tags = {}
    linux_app.as_dict.return_value = {
        'kind': 'functionapp,linux',
        'location': 'eastus',
        'server_farm_id': linux_app.server_farm_id,
        'tags': {}
    }

    # Mock Windows function app
    windows_app = Mock()
    windows_app.name = 'win-app'
    windows_app.id = '/subscriptions/123/resourceGroups/rg/providers/Microsoft.Web/sites/win-app'
    windows_app.kind = 'functionapp'
    windows_app.location = 'westus'
    windows_app.server_farm_id = '/subscriptions/123/resourceGroups/rg/providers/Microsoft.Web/serverfarms/plan2'
    windows_app.tags = {}
    windows_app.as_dict.return_value = {
        'kind': 'functionapp',
        'location': 'westus',
        'server_farm_id': windows_app.server_farm_id,
        'tags': {}
    }

    # Create proper mock configuration
    linux_config = Mock()
    linux_config.app_settings = []
    linux_config.connection_strings = []
    linux_config.linux_fx_version = "PYTHON|3.9"  # Proper format for Linux function app
    linux_config.as_dict.return_value = {
        "app_settings": [],
        "connection_strings": [],
        "linux_fx_version": "PYTHON|3.9"
    }

    windows_config = Mock()
    windows_config.app_settings = []
    windows_config.connection_strings = []
    windows_config.linux_fx_version = None  # Windows doesn't have this
    windows_config.as_dict.return_value = {
        "app_settings": [],
        "connection_strings": []
    }

    def get_config_side_effect(resource_group_name, name):
        if name == 'lin-app':
            return linux_config
        return windows_config

    web_client.web_apps.list.return_value = [linux_app, windows_app]
    web_client.web_apps.get_configuration.side_effect = get_config_side_effect
    web_client.web_apps.get_auth_settings.return_value = None
    web_client.web_apps.get_backup_configuration.return_value = None
    web_client.web_apps.get_source_control.return_value = None

    output_dir = Path('out')
    result = scan_function_apps(output_dir, 'sub123')

    assert len(result) == 2
    assert {app['os_type'] for app in result} == {'linux', 'windows'}

    # ensure generate_imports_file called separately for each OS
    assert mock_imports.call_count == 2
    resource_types = {call.args[0] for call in mock_imports.call_args_list}
    assert resource_types == {'azure_linux_function_app', 'azure_windows_function_app'}
    for call in mock_imports.call_args_list:
        apps = call.args[1]
        if call.args[0] == 'azure_linux_function_app':
            assert all(app['os_type'] == 'linux' for app in apps)
        if call.args[0] == 'azure_windows_function_app':
            assert all(app['os_type'] == 'windows' for app in apps)
