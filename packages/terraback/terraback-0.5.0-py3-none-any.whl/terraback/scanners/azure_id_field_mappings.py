"""Azure Service ID field mappings for accurate resource identification."""

# Mapping of Azure resources to their primary identifier field names
# Used by scanners and resource processors to consistently extract
# resource identifiers and names.
AZURE_ID_FIELD_MAPPINGS = {
    # Core resources
    'azure_resource_group': 'name',
    'azure_storage_account': 'name',
    'azure_storage_share': 'name',
    'azure_virtual_network': 'name',
    'azure_subnet': 'name',
    'azure_network_security_group': 'name',
    'azure_network_interface': 'name',
    'azure_public_ip': 'name',
    'azure_nat_gateway': 'name',
    'azure_route_table': 'name',
    'azure_virtual_machine': 'name',
    'azure_managed_disk': 'name',
    'azure_ssh_public_key': 'name',
    'azure_vmss': 'name',
    'azure_app_service_plan': 'name',
    'azure_web_app': 'name',
    'azure_function_app': 'name',
    'azure_lb': 'name',
    'azure_application_gateway': 'name',
    'azure_container_registry': 'name',
    'azure_kubernetes_cluster': 'name',
    'azure_kubernetes_cluster_node_pool': 'name',
    # Databases
    'azure_sql_server': 'name',
    'azure_sql_database': 'name',
    'azure_sql_elastic_pool': 'name',
    # Messaging
    'azure_eventhub_namespace': 'name',
    'azure_eventhub': 'name',
    'azure_eventhub_consumer_group': 'name',
    'azure_servicebus_namespace': 'name',
    'azure_servicebus_queue': 'name',
    'azure_servicebus_topic': 'name',
    'azure_servicebus_subscription': 'name',
    # Caching & CDN
    'azure_redis_cache': 'name',
    'azure_cdn_profile': 'name',
    'azure_cdn_endpoint': 'name',
    # DNS
    'azure_dns_zone': 'name',
    'azure_dns_record': 'name',
    # Security
    'azure_key_vault': 'name',
    'azure_key_vault_secret': 'name',
    'azure_key_vault_key': 'name',
    'azure_key_vault_certificate': 'name',
    'azure_user_assigned_identity': 'name',
    'azure_role_assignment': 'name',
    'azure_role_definition': 'name',
    # Monitoring
    'azure_portal_dashboard': 'name',
    'azure_action_group': 'name',
    'azure_monitor_action_group': 'name',
    'azure_metric_alert': 'name',
    'azure_monitor_metric_alert': 'name',
    'azure_log_analytics_workspace': 'name',
    # Automation
    'azure_automation_account': 'name',
    'azure_automation_runbook': 'name',
}

# Patterns identifying Azure-managed resources that should be filtered out
AZURE_MANAGED_RESOURCE_PATTERNS = {
    'azure_resource_group': ['cloud-shell-storage', 'Default', 'NetworkWatcherRG'],
    'azure_subnet': ['AzureBastionSubnet', 'GatewaySubnet'],
    'azure_network_security_group': ['default'],
    'azure_route_table': ['default'],
    'azure_public_ip': ['default'],
}

def get_id_field(resource_type: str) -> str:
    """Return the primary identifier field for a resource type."""
    return AZURE_ID_FIELD_MAPPINGS.get(resource_type, 'name')

def should_filter_resource(resource_type: str, resource_data: dict) -> bool:
    """Determine if a resource should be filtered out as Azure-managed."""
    patterns = AZURE_MANAGED_RESOURCE_PATTERNS.get(resource_type)
    if not patterns:
        return False
    id_field = get_id_field(resource_type)
    resource_id = resource_data.get(id_field, '')
    for pattern in patterns:
        if pattern in str(resource_id):
            return True
    return False
