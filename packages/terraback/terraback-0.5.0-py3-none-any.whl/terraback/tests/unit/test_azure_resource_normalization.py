from terraback.terraform_generator.imports import normalize_terraform_resource_type
import pytest


def test_azure_dns_zone_normalization():
    assert normalize_terraform_resource_type('azure_dns_zone') == 'azurerm_dns_zone'


def test_azure_dns_a_record_normalization():
    assert normalize_terraform_resource_type('azure_dns_a_record') == 'azurerm_dns_a_record'


def test_azure_servicebus_namespace_normalization():
    assert normalize_terraform_resource_type('azure_servicebus_namespace') == 'azurerm_servicebus_namespace'


def test_azure_eventhub_normalization():
    assert normalize_terraform_resource_type('azure_eventhub') == 'azurerm_eventhub'


def test_azure_log_analytics_workspace_normalization():
    assert normalize_terraform_resource_type('azure_log_analytics_workspace') == 'azurerm_log_analytics_workspace'


def test_azure_role_assignment_normalization():
    assert normalize_terraform_resource_type('azure_role_assignment') == 'azurerm_role_assignment'


def test_azure_user_assigned_identity_normalization():
    assert normalize_terraform_resource_type('azure_user_assigned_identity') == 'azurerm_user_assigned_identity'


def test_azure_unknown_resource_fallback():
    assert normalize_terraform_resource_type('azure_custom_resource') == 'azurerm_custom_resource'


def test_azure_service_plan_and_function_app_modern_types():
    assert normalize_terraform_resource_type('azure_app_service_plan') == 'azurerm_service_plan'
    assert normalize_terraform_resource_type('azure_function_app') == 'azurerm_linux_function_app'
    assert normalize_terraform_resource_type('azure_linux_function_app') == 'azurerm_linux_function_app'
    assert normalize_terraform_resource_type('azure_windows_function_app') == 'azurerm_windows_function_app'


def test_azure_web_app_normalization():
    assert normalize_terraform_resource_type('azure_web_app') == 'azurerm_linux_web_app'


@pytest.mark.parametrize(
    "resource_type,expected",
    [
        ("azure_app_service_plan", "azurerm_service_plan"),
        ("azure_web_app", "azurerm_linux_web_app"),
        ("azure_function_app", "azurerm_linux_function_app"),
        ("azure_linux_function_app", "azurerm_linux_function_app"),
        ("azure_windows_function_app", "azurerm_windows_function_app"),
        ("azure_monitor_action_group", "azurerm_monitor_action_group"),
        ("azure_public_ip", "azurerm_public_ip"),
        ("azure_nat_gateway", "azurerm_nat_gateway"),
        ("azure_route_table", "azurerm_route_table"),
        ("azure_redis_cache", "azurerm_redis_cache"),
        ("azure_monitor_metric_alert", "azurerm_monitor_metric_alert"),
        ("azure_portal_dashboard", "azurerm_portal_dashboard"),
        ("azure_key_vault", "azurerm_key_vault"),
        ("azure_key_vault_secret", "azurerm_key_vault_secret"),
        ("azure_key_vault_key", "azurerm_key_vault_key"),
        ("azure_key_vault_certificate", "azurerm_key_vault_certificate"),
        ("azure_role_definition", "azurerm_role_definition"),
        ("azure_api_management", "azurerm_api_management"),
        ("azure_api_management_api", "azurerm_api_management_api"),
        ("azure_cdn_profile", "azurerm_cdn_profile"),
        ("azure_cdn_endpoint", "azurerm_cdn_endpoint"),
        ("azure_storage_share", "azurerm_storage_share"),
        ("azure_automation_account", "azurerm_automation_account"),
        ("azure_automation_runbook", "azurerm_automation_runbook"),
        ("azure_sql_server", "azurerm_mssql_server"),
        ("azure_sql_database", "azurerm_mssql_database"),
        ("azure_sql_elastic_pool", "azurerm_mssql_elasticpool"),
        ("azure_kubernetes_cluster", "azurerm_kubernetes_cluster"),
        ("azure_kubernetes_cluster_node_pool", "azurerm_kubernetes_cluster_node_pool"),
        ("azure_container_registry", "azurerm_container_registry"),
        ("azure_application_gateway", "azurerm_application_gateway"),
        ("azure_availability_set", "azurerm_availability_set"),
        ("azure_image", "azurerm_image"),
        ("azure_snapshot", "azurerm_snapshot"),
        ("azure_ssh_key", "azurerm_ssh_public_key"),
        ("azure_ssh_public_key", "azurerm_ssh_public_key"),
    ],
)
def test_additional_azure_resource_normalization(resource_type, expected):
    assert normalize_terraform_resource_type(resource_type) == expected
