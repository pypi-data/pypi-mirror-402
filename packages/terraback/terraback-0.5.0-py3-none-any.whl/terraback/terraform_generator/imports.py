import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from .filters import to_terraform_resource_name, strip_id_prefix


def flatten_azure_resource_properties(resource: Dict[str, Any], resource_type: str) -> Dict[str, Any]:
    """
    Transform Azure resource data to match the structure expected by templates.
    This flattens nested properties similar to how it's done during scanning.
    """
    if not resource or 'properties' not in resource:
        return resource
    
    # Create a copy to avoid mutating the original
    flattened = resource.copy()
    properties = resource.get('properties', {})
    
    # Apply resource-specific transformations based on scanning logic
    if resource_type == 'azure_key_vault':
        # From terraback/cli/azure/security/key_vaults.py:100-106
        if 'enabled_for_deployment' in properties:
            flattened['enabled_for_deployment'] = properties['enabled_for_deployment']
        if 'enabled_for_disk_encryption' in properties:
            flattened['enabled_for_disk_encryption'] = properties['enabled_for_disk_encryption']
        if 'enabled_for_template_deployment' in properties:
            flattened['enabled_for_template_deployment'] = properties['enabled_for_template_deployment']
        if 'enable_rbac_authorization' in properties:
            flattened['enable_rbac_authorization'] = properties['enable_rbac_authorization']
        if 'soft_delete_retention_in_days' in properties:
            flattened['soft_delete_retention_days'] = properties['soft_delete_retention_in_days']
        if 'enable_purge_protection' in properties:
            flattened['purge_protection_enabled'] = properties['enable_purge_protection']
        if 'public_network_access' in properties:
            flattened['public_network_access_enabled'] = properties['public_network_access'] != 'Disabled'
    
    elif resource_type == 'azure_storage_account':
        # From terraback/cli/azure/storage/storage_accounts.py property mappings
        # These are mapped in _format_template_attributes()
        if 'enable_https_traffic_only' in properties:
            flattened['https_traffic_only_enabled'] = properties['enable_https_traffic_only']
        if 'minimum_tls_version' in properties:
            flattened['min_tls_version'] = properties['minimum_tls_version']
        if 'allow_blob_public_access' in properties:
            flattened['allow_nested_items_to_be_public'] = properties['allow_blob_public_access']
        if 'access_tier' in properties:
            flattened['access_tier'] = properties['access_tier']
        if 'is_hns_enabled' in properties:
            flattened['is_hns_enabled'] = properties['is_hns_enabled']
        
        # Handle encryption settings
        if 'encryption' in properties and properties['encryption']:
            encryption = properties['encryption']
            if 'require_infrastructure_encryption' in encryption:
                flattened['infrastructure_encryption_enabled'] = encryption['require_infrastructure_encryption']
    
    elif resource_type in ['azure_virtual_machine', 'azure_linux_virtual_machine', 'azure_windows_virtual_machine']:
        # VM properties are handled differently in the scanning code but we can add common ones
        # Most VM properties are already at the top level or handled by complex nested logic
        # For now, focus on basic properties that might be nested
        pass
    
    # Add more resource types as needed based on their scanning logic
    
    return flattened


def detect_provider_from_resource_type(resource_type: str) -> str:
    """Detect cloud provider from resource type.

    Raises:
        ValueError: If the provider cannot be determined from ``resource_type``.
    """
    lower = resource_type.lower()
    # Check for explicit provider prefixes first (highest priority)
    if any(lower.startswith(prefix) for prefix in ['azure_', 'azurerm_']):
        return "azure"
    elif any(lower.startswith(prefix) for prefix in ['aws_', 'gcp_', 'google_']):
        if lower.startswith('aws_'):
            return "aws"
        else:
            return "gcp"
    # Check for provider-specific keywords (lower priority)
    elif any(prefix in lower for prefix in ['microsoft']):
        return "azure"
    elif any(prefix in lower for prefix in ['amazon', 'ec2', 's3', 'iam', 'lambda', 'api_gateway', 'route53', 'cloudfront', 'elb', 'eip', 'elasticache', 'rds', 'vpc', 'subnet', 'security_group', 'internet_gateway', 'route_table', 'network_interface', 'volume', 'snapshot', 'ami', 'launch', 'autoscaling', 'sns', 'sqs', 'cloudwatch', 'acm', 'ecr', 'ecs', 'efs', 'secretsmanager', 'ssm', 'kms', 'backup', 'cloudtrail', 'guardduty', 'kinesis', 'msk', 'opensearch', 'sfn', 'stepfunctions', 'dynamodb', 'eventbridge']):
        return "aws"
    elif any(prefix in lower for prefix in ['compute']):
        return "gcp"
    else:
        raise ValueError(
            f"Unable to detect provider from resource type '{resource_type}'. Please specify the provider explicitly."
        )


def normalize_terraform_resource_type(resource_type: str, provider: Optional[str] = None) -> str:
    """
    Convert short resource type names to full Terraform resource type names.
    
    Args:
        resource_type: Short name like 'api_gateway_deployment' or full name like 'aws_api_gateway_deployment'
        provider: Optional provider override ('aws', 'azure', 'gcp')
    
    Returns:
        Full Terraform resource type like 'aws_api_gateway_deployment'
    """
    # If already has provider prefix, return as-is
    if any(resource_type.startswith(prefix) for prefix in ['aws_', 'azurerm_', 'google_']):
        return resource_type
    
    # Detect provider if not provided
    if not provider:
        provider = detect_provider_from_resource_type(resource_type)
    
    # AWS resource type mappings
    aws_mappings = {
        # API Gateway
        'api_gateway_deployment': 'aws_api_gateway_deployment',
        'api_gateway_method': 'aws_api_gateway_method',
        'api_gateway_resource': 'aws_api_gateway_resource',
        'api_gateway_rest_api': 'aws_api_gateway_rest_api',
        'api_gateway_stage': 'aws_api_gateway_stage',
        'api_gateway_integration': 'aws_api_gateway_integration',
        
        # Compute
        'ec2': 'aws_instance',
        'ec2_instance': 'aws_instance',
        'instance': 'aws_instance',
        'instances': 'aws_instance',
        'launch_configuration': 'aws_launch_configuration',
        'autoscaling_group': 'aws_autoscaling_group',
        'autoscaling_policy': 'aws_autoscaling_policy',
        'lambda_function': 'aws_lambda_function',
        'lambda_layer_version': 'aws_lambda_layer_version',
        'lambda_permission': 'aws_lambda_permission',
        
        # Storage
        's3_bucket': 'aws_s3_bucket',
        'bucket': 'aws_s3_bucket',
        'buckets': 'aws_s3_bucket',
        'ebs_volume': 'aws_ebs_volume',
        'volume': 'aws_ebs_volume',
        'volumes': 'aws_ebs_volume',
        'ebs_snapshot': 'aws_ebs_snapshot',
        'efs_file_system': 'aws_efs_file_system',
        'efs_mount_target': 'aws_efs_mount_target',
        'efs_access_point': 'aws_efs_access_point',
        
        # Networking
        'vpc': 'aws_vpc',
        'vpcs': 'aws_vpc',
        'subnet': 'aws_subnet',
        'subnets': 'aws_subnet',
        'security_group': 'aws_security_group',
        'security_groups': 'aws_security_group',
        'internet_gateway': 'aws_internet_gateway',
        'nat_gateway': 'aws_nat_gateway',
        'route_table': 'aws_route_table',
        'network_interface': 'aws_network_interface',
        'network_interfaces': 'aws_network_interface',
        'eip': 'aws_eip',
        'eips': 'aws_eip',
        'vpc_endpoint': 'aws_vpc_endpoint',
        
        # Load Balancing
        'classic_load_balancer': 'aws_elb',
        'elbv2_load_balancer': 'aws_lb',
        'elbv2_target_group': 'aws_lb_target_group',
        'elbv2_listener': 'aws_lb_listener',
        'elbv2_listener_rule': 'aws_lb_listener_rule',
        'elbv2_target_group_attachments': 'aws_lb_target_group_attachment',
        
        # Database
        'rds_instance': 'aws_db_instance',
        'rds_parameter_group': 'aws_db_parameter_group',
        'rds_subnet_group': 'aws_db_subnet_group',
        
        # Caching
        'elasticache_redis_cluster': 'aws_elasticache_cluster',
        'elasticache_memcached_cluster': 'aws_elasticache_cluster',
        'elasticache_replication_group': 'aws_elasticache_replication_group',
        'elasticache_parameter_group': 'aws_elasticache_parameter_group',
        'elasticache_subnet_group': 'aws_elasticache_subnet_group',
        
        # Security & Identity
        'iam_role': 'aws_iam_role',
        'iam_roles': 'aws_iam_role',
        'iam_policy': 'aws_iam_policy',
        'iam_policies': 'aws_iam_policy',
        'key_pair': 'aws_key_pair',
        'key_pairs': 'aws_key_pair',
        'acm_certificate': 'aws_acm_certificate',
        'secretsmanager_secret': 'aws_secretsmanager_secret',
        'secretsmanager_secret_version': 'aws_secretsmanager_secret_version',
        
        # DNS
        'route53_zone': 'aws_route53_zone',
        'route53_record': 'aws_route53_record',
        
        # CDN
        'cloudfront_distribution': 'aws_cloudfront_distribution',
        'cloudfront_cache_policy': 'aws_cloudfront_cache_policy',
        'cloudfront_origin_request_policy': 'aws_cloudfront_origin_request_policy',
        'cloudfront_origin_access_control': 'aws_cloudfront_origin_access_control',
        
        # Monitoring
        'cloudwatch_alarm': 'aws_cloudwatch_metric_alarm',
        'cloudwatch_dashboard': 'aws_cloudwatch_dashboard',
        'cloudwatch_log_group': 'aws_cloudwatch_log_group',
        
        # Messaging
        'sns_topic': 'aws_sns_topic',
        'sns_subscription': 'aws_sns_topic_subscription',
        'sqs_queue': 'aws_sqs_queue',

        # EventBridge (uses cloudwatch_event_rule in Terraform)
        'eventbridge_rule': 'aws_cloudwatch_event_rule',
        'eventbridge_target': 'aws_cloudwatch_event_target',
        
        # Management
        'ssm_parameter': 'aws_ssm_parameter',
        'ssm_document': 'aws_ssm_document',
        'ssm_maintenance_window': 'aws_ssm_maintenance_window',
        
        # Container
        'ecr_repository': 'aws_ecr_repository',
        'ecs_cluster': 'aws_ecs_cluster',
        'ecs_service': 'aws_ecs_service',
        'ecs_task_definition': 'aws_ecs_task_definition',
    }
    
    # Azure resource type mappings
    azure_mappings = {
        'azure_virtual_machine': 'azurerm_linux_virtual_machine',  # Default to Linux, template handles OS detection
        'azure_function_app': 'azurerm_linux_function_app',  # Default to Linux, template handles OS detection
        'azure_linux_function_app': 'azurerm_linux_function_app',
        'azure_windows_function_app': 'azurerm_windows_function_app',
        'azure_vmss': 'azurerm_linux_virtual_machine_scale_set',  # Default to Linux
        'azure_web_app': 'azurerm_linux_web_app',  # Default to Linux
        'azure_linux_web_app': 'azurerm_linux_web_app',
        'azure_windows_web_app': 'azurerm_windows_web_app',
        'azure_app_service_plan': 'azurerm_service_plan',  # Updated resource type
        'azure_managed_disk': 'azurerm_managed_disk',
        'azure_virtual_network': 'azurerm_virtual_network',
        'azure_subnet': 'azurerm_subnet',
        'azure_network_security_group': 'azurerm_network_security_group',
        'azure_network_interface': 'azurerm_network_interface',
        'azure_storage_account': 'azurerm_storage_account',
        'azure_resource_group': 'azurerm_resource_group',
        'azure_lb': 'azurerm_lb',

        # DNS
        'azure_dns_zone': 'azurerm_dns_zone',
        'azure_dns_a_record': 'azurerm_dns_a_record',
        'azure_dns_cname_record': 'azurerm_dns_cname_record',
        'azure_dns_txt_record': 'azurerm_dns_txt_record',
        'azure_dns_mx_record': 'azurerm_dns_mx_record',
        'azure_dns_ns_record': 'azurerm_dns_ns_record',
        'azure_dns_srv_record': 'azurerm_dns_srv_record',
        'azure_dns_ptr_record': 'azurerm_dns_ptr_record',

        # Service Bus
        'azure_servicebus_namespace': 'azurerm_servicebus_namespace',
        'azure_servicebus_queue': 'azurerm_servicebus_queue',
        'azure_servicebus_topic': 'azurerm_servicebus_topic',
        'azure_servicebus_subscription': 'azurerm_servicebus_subscription',

        # Event Hub
        'azure_eventhub_namespace': 'azurerm_eventhub_namespace',
        'azure_eventhub': 'azurerm_eventhub',
        'azure_eventhub_consumer_group': 'azurerm_eventhub_consumer_group',

        # Log Analytics
        'azure_log_analytics_workspace': 'azurerm_log_analytics_workspace',

        # Monitor
        'azure_monitor_action_group': 'azurerm_monitor_action_group',

        # Identity & Access
        'azure_role_assignment': 'azurerm_role_assignment',
        'azure_user_assigned_identity': 'azurerm_user_assigned_identity',

        # Compute & Web
        'azure_availability_set': 'azurerm_availability_set',
        'azure_image': 'azurerm_image',
        'azure_snapshot': 'azurerm_snapshot',
        'azure_kubernetes_cluster': 'azurerm_kubernetes_cluster',
        'azure_kubernetes_cluster_node_pool': 'azurerm_kubernetes_cluster_node_pool',
        'azure_container_registry': 'azurerm_container_registry',
        'azure_application_gateway': 'azurerm_application_gateway',

        # Networking
        'azure_public_ip': 'azurerm_public_ip',
        'azure_nat_gateway': 'azurerm_nat_gateway',
        'azure_route_table': 'azurerm_route_table',

        # Caching
        'azure_redis_cache': 'azurerm_redis_cache',

        # Monitoring
        'azure_monitor_metric_alert': 'azurerm_monitor_metric_alert',
        'azure_portal_dashboard': 'azurerm_portal_dashboard',

        # Identity & Security
        'azure_key_vault': 'azurerm_key_vault',
        'azure_key_vault_secret': 'azurerm_key_vault_secret',
        'azure_key_vault_key': 'azurerm_key_vault_key',
        'azure_key_vault_certificate': 'azurerm_key_vault_certificate',
        'azure_role_definition': 'azurerm_role_definition',
        'azure_ssh_key': 'azurerm_ssh_public_key',
        'azure_ssh_public_key': 'azurerm_ssh_public_key',

        # Automation
        'azure_automation_account': 'azurerm_automation_account',
        'azure_automation_runbook': 'azurerm_automation_runbook',

        # API Management
        'azure_api_management': 'azurerm_api_management',
        'azure_api_management_api': 'azurerm_api_management_api',

        # CDN & Storage
        'azure_cdn_profile': 'azurerm_cdn_profile',
        'azure_cdn_endpoint': 'azurerm_cdn_endpoint',
        'azure_storage_share': 'azurerm_storage_share',

        # Databases
        'azure_sql_server': 'azurerm_mssql_server',
        'azure_sql_database': 'azurerm_mssql_database',
        'azure_sql_elastic_pool': 'azurerm_mssql_elasticpool',

        # Short names
        'vm': 'azurerm_linux_virtual_machine',
        'vms': 'azurerm_linux_virtual_machine',
        'disk': 'azurerm_managed_disk',
        'disks': 'azurerm_managed_disk',
        'vnet': 'azurerm_virtual_network',
        'vnets': 'azurerm_virtual_network',
        'nsg': 'azurerm_network_security_group',
        'nsgs': 'azurerm_network_security_group',
    }
    
    # GCP resource type mappings
    gcp_mappings = {
        'gcp_instance': 'google_compute_instance',
        'gcp_disk': 'google_compute_disk',
        'gcp_network': 'google_compute_network',
        'gcp_subnet': 'google_compute_subnetwork',
        'gcp_firewall': 'google_compute_firewall',
        'gcp_bucket': 'google_storage_bucket',
        'gcp_backend_service': 'google_compute_backend_service',
        'gcp_url_map': 'google_compute_url_map',
        'gcp_target_https_proxy': 'google_compute_target_https_proxy',
        'gcp_global_forwarding_rule': 'google_compute_global_forwarding_rule',
        'gcp_gke_cluster': 'google_container_cluster',
        'gcp_gke_node_pool': 'google_container_node_pool',
        'gcp_pubsub_topic': 'google_pubsub_topic',
        'gcp_pubsub_subscription': 'google_pubsub_subscription',
        'gcp_secret': 'google_secret_manager_secret',
        'gcp_sql_instance': 'google_sql_database_instance',
        'gcp_sql_database': 'google_sql_database',
        'gcp_cloud_run_service': 'google_cloud_run_service',
        'gcp_memorystore_redis': 'google_redis_instance',
        'gcp_memorystore_memcached': 'google_memcache_instance',
        'gcp_backend_buckets': 'google_compute_backend_bucket',
        'gcp_api_gateway_api': 'google_api_gateway_api',
        'gcp_certificate': 'google_certificate_manager_certificate',
        'gcp_certificate_map': 'google_certificate_manager_certificate_map',
        'gcp_certificate_manager_certificate': 'google_certificate_manager_certificate',
        'gcp_certificate_manager_certificate_map': 'google_certificate_manager_certificate_map',
        'gcp_cloud_function': 'google_cloudfunctions_function',
        'gcp_cloudfunctions_function': 'google_cloudfunctions_function',
        'gcp_cloud_tasks_queue': 'google_cloud_tasks_queue',
        'gcp_container_registry': 'google_container_registry',
        'gcp_container_registries': 'google_container_registry',
        'gcp_dns_managed_zones': 'google_dns_managed_zone',
        'gcp_eventarc_trigger': 'google_eventarc_trigger',
        'gcp_firestore_database': 'google_firestore_database',
        'gcp_health_check': 'google_compute_health_check',
        'gcp_image': 'google_compute_image',
        'gcp_instance_group': 'google_compute_instance_group',
        'gcp_instance_template': 'google_compute_instance_template',
        'gcp_kms_crypto_key': 'google_kms_crypto_key',
        'gcp_kms_key_ring': 'google_kms_key_ring',
        'gcp_monitoring_alert_policies': 'google_monitoring_alert_policy',
        'gcp_router': 'google_compute_router',
        'gcp_service_account': 'google_service_account',
        'gcp_service_accounts': 'google_service_account',
        'gcp_snapshot': 'google_compute_snapshot',
        'gcp_spanner_instance': 'google_spanner_instance',
        'gcp_vpn_gateway': 'google_compute_vpn_gateway',
        'gcp_workflows_workflow': 'google_workflows_workflow',
        'gcp_workflows': 'google_workflows_workflow',
        'gcp_bucket_iam_binding': 'google_storage_bucket_iam_binding',
        'gcp_bigtable_instance': 'google_bigtable_instance',
        'gcp_binary_authorization_policy': 'google_binary_authorization_policy',
        'gcp_certificate_authority': 'google_privateca_certificate_authority',
        'gcp_iam_roles': 'google_project_iam_custom_role',
        
        # Short names for GCP
        'instance': 'google_compute_instance',
        'disk': 'google_compute_disk',
        'network': 'google_compute_network',
        'firewall': 'google_compute_firewall',
        'bucket': 'google_storage_bucket',
    }
    
    # Apply mappings based on provider
    if provider == "aws":
        return aws_mappings.get(resource_type, f"aws_{resource_type}")
    elif provider == "azure":
        stripped = resource_type[6:] if resource_type.startswith("azure_") else resource_type
        return azure_mappings.get(resource_type, f"azurerm_{stripped}")
    elif provider == "gcp":
        return gcp_mappings.get(resource_type, f"google_{resource_type}")
    else:
        # Default to AWS if provider detection fails
        return aws_mappings.get(resource_type, f"aws_{resource_type}")


def derive_resource_name(resource_type: str, resource: Dict[str, Any], remote_id: str) -> str:
    """Generate a Terraform-safe name based on provider and resource info."""
    provider = detect_provider_from_resource_type(resource_type)

    # Prefer precomputed sanitized names if available
    if isinstance(resource, dict):
        pre_sanitized = resource.get("name_sanitized") or resource.get("domain_sanitized")
        if pre_sanitized:
            # Use the same name that .tf templates use, preserving case
            return str(pre_sanitized)

    base = str(remote_id)

    if provider == "aws":
        normalized_type = normalize_terraform_resource_type(resource_type, provider)

        if normalized_type == "aws_route53_record":
            # remote_id format: ZONEID_name_type[_setidentifier]
            # Include the zone identifier in the sanitized name
            if "_" in base:
                zone_id, rest = base.split("_", 1)
                zone_id = to_terraform_resource_name(zone_id)
                base = f"{zone_id}_{rest}"

        elif normalized_type == "aws_api_gateway_deployment":
            # remote_id format: restApiId/deploymentId
            if "/" in base:
                api_id, deploy_id = base.split("/", 1)
                base = f"{api_id}_deployment_{deploy_id}"
            else:
                base = strip_id_prefix(base)

        elif normalized_type == "aws_acm_certificate":
            domain = resource.get("DomainName") or resource.get("domain_name")
            if domain:
                base = f"certificate_{domain}"
            else:
                base = f"certificate_{strip_id_prefix(base)}"

        else:
            base = strip_id_prefix(base)

    elif provider in ("azure", "gcp"):
        base = resource.get("name") or base

    if "/" in base:
        base = base.replace("/", "_")

    return to_terraform_resource_name(base)


def generate_imports_file(
    resource_type: str,
    resources: List[Dict[str, Any]],
    remote_resource_id_key: str,
    output_dir: Path,
    composite_keys: Optional[List[str]] = None,
    provider: Optional[str] = None,
    provider_metadata: Optional[Dict[str, Any]] = None,
):
    """
    Generates a .json file containing the necessary data for terraform import commands.

    Args:
        resource_type: The resource type (can be short name like 'api_gateway_deployment' 
                      or full name like 'aws_api_gateway_deployment').
        resources: The list of resource dictionaries from the cloud provider API.
        remote_resource_id_key: The key in the resource dict that holds the unique ID.
        output_dir: The directory to save the file in.
        composite_keys (optional): A list of keys to join with '/' to form a composite ID,
                                   required for some resources like API Gateway methods.
        provider (optional): Cloud provider ('aws', 'azure', 'gcp'). Auto-detected if not provided.
        provider_metadata (optional): Additional metadata (e.g. account ID and region)
            associated with the scanned resources.
    """
    # Normalize the resource type to full Terraform resource type
    terraform_resource_type = normalize_terraform_resource_type(resource_type, provider)
    
    import_data = []
    for resource in resources:
        # Special handling for Lambda permissions
        if resource_type == 'lambda_permission' or terraform_resource_type == 'aws_lambda_permission':
            # Skip if no valid statement_id
            if not resource.get('statement_id'):
                print(f"Warning: Lambda permission without statement_id. Skipping.")
                continue
                
            # Build the import ID with qualifier if present
            function_name = resource.get('function_name', '')
            statement_id = resource.get('statement_id', '')
            qualifier = resource.get('qualifier')
            
            if qualifier:
                remote_id = f"{function_name}:{qualifier}/{statement_id}"
            else:
                remote_id = f"{function_name}/{statement_id}"
                
        elif composite_keys:
            # Build the ID from multiple keys, e.g., "api_id/resource_id/method".
            # This is necessary for many API Gateway resources.
            try:
                remote_id = "/".join([str(resource[key]) for key in composite_keys])
            except KeyError as e:
                print(f"Warning: Missing key {e} when building composite ID for a {terraform_resource_type}. Skipping.")
                continue
        else:
            remote_id = resource.get(remote_resource_id_key)

        if not remote_id:
            print(f"Warning: Could not determine remote ID for a {terraform_resource_type} using key '{remote_resource_id_key}'. Skipping.")
            continue

        # Create a sanitized, unique name for the resource in the Terraform state
        sanitized_name = derive_resource_name(resource_type, resource, remote_id)
        
        # Transform resource data to match template expectations (flatten Azure properties)
        processed_resource_data = flatten_azure_resource_properties(resource, resource_type)
        
        entry = {
            "resource_type": terraform_resource_type,  # Now uses full Terraform resource type
            "resource_name": sanitized_name,
            "remote_id": remote_id,
            "resource_data": processed_resource_data,
        }
        # Store the original scanned resource for later use by helper commands
        entry["scanned_data"] = resource
        if provider_metadata is not None:
            entry["provider_metadata"] = provider_metadata

        import_data.append(entry)
    
    # Skip file generation if no resources
    if not import_data:
        print(f"Skipping import file generation for {resource_type} - no resources found")
        return

    # Use AWS-style naming: strip provider prefix for consistency with .tf files
    from .writer import get_terraform_filename
    tf_filename = get_terraform_filename(resource_type)
    base_name = tf_filename.replace('.tf', '')  # container_registry from container_registry.tf

    # Create import subdirectory for cleaner organization
    import_dir = output_dir / "import"
    import_dir.mkdir(exist_ok=True)
    import_file = import_dir / f"{base_name}_import.json"

    try:
        with open(import_file, "w", encoding="utf-8") as f:
            # Use default=str so datetime and other objects are serialised
            # rather than causing a TypeError when dumps encounters them.
            json.dump(import_data, f, indent=2, default=str)
        print(f"Generated import file: {import_file} with {len(import_data)} resources")
    except IOError as e:
        print(f"Error writing import file {import_file}: {e}")


def read_import_file(import_file: Path) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Read and validate an import file.

    Returns:
        A tuple ``(entries, error)`` where ``entries`` is the list of import
        definitions and ``error`` contains any non JSON-decode related problem.

    Raises:
        ValueError: If the file contains invalid JSON.
    """

    try:
        with open(import_file, "r") as f:
            import_data = json.load(f)
    except json.JSONDecodeError as e:
        # Surface JSON errors to the caller so the filename can be reported
        raise ValueError(f"Invalid JSON: {e}") from e
    except IOError as e:
        return [], str(e)

    # Ensure all entries have proper resource types
    normalized_data: List[Dict[str, Any]] = []
    for entry in import_data:
        if isinstance(entry, dict):
            resource_type = entry.get("resource_type", "")
            normalized_type = normalize_terraform_resource_type(resource_type)

            normalized_entry = dict(entry)
            normalized_entry["resource_type"] = normalized_type
            # Preserve any scanned resource information for downstream helpers
            if "scanned_data" in entry:
                normalized_entry["scanned_data"] = entry["scanned_data"]
            normalized_data.append(normalized_entry)
        else:
            normalized_data.append(entry)

    return normalized_data, None


def validate_import_file(import_file: Path) -> List[str]:
    """
    Validate an import file for common issues.
    
    Returns:
        List of validation errors.
    """
    errors = []
    
    try:
        import_data, error = read_import_file(import_file)
        if error:
            errors.append(f"Failed to read file: {error}")
            return errors
    
        for i, entry in enumerate(import_data):
            if not isinstance(entry, dict):
                errors.append(f"Entry {i}: Not a dictionary")
                continue
            
            # Check required fields
            required_fields = ['resource_type', 'resource_name', 'remote_id']
            for field in required_fields:
                if field not in entry:
                    errors.append(f"Entry {i}: Missing required field '{field}'")
                elif not entry[field]:
                    errors.append(f"Entry {i}: Empty value for field '{field}'")
            
            # Validate resource type format
            resource_type = entry.get('resource_type', '')
            if resource_type and not any(resource_type.startswith(p) for p in ['aws_', 'azurerm_', 'google_']):
                errors.append(f"Entry {i}: Resource type '{resource_type}' should have provider prefix")
            
            # Validate resource name format (Terraform identifier rules)
            resource_name = entry.get('resource_name', '')
            if resource_name and not re.match(r'^[a-zA-Z_][a-zA-Z0-9_-]*$', resource_name):
                errors.append(f"Entry {i}: Invalid resource name '{resource_name}' (must match Terraform identifier rules)")
    
    except Exception as e:
        errors.append(f"Failed to validate file: {e}")

    return errors


def _parse_tf_resources(output_dir: Path) -> Dict[str, str]:
    """
    Parse all .tf files to extract resource definitions.

    Returns:
        Dict mapping (resource_type:identifier_value) -> resource_name
        where identifier_value is the identifying attribute or extracted from resource name
    """
    # Map of resource type to the attribute that identifies it
    IDENTIFIER_ATTRS = {
        "aws_dynamodb_table": "name",
        "aws_lambda_function": "function_name",
        "aws_s3_bucket": "bucket",
        "aws_iam_role": "name",
        "aws_iam_policy": "name",
        "aws_ecs_cluster": "name",
        "aws_ecr_repository": "name",
        "aws_sns_topic": "name",
        "aws_acm_certificate": "domain_name",
        "aws_cloudfront_origin_access_control": "name",
        "aws_cloudwatch_log_group": "name",
        "aws_cloudwatch_metric_alarm": "alarm_name",
        "aws_route53_zone": "name",
        "aws_kms_alias": "name",
        "aws_secretsmanager_secret": "name",
        "aws_db_subnet_group": "name",
        "aws_backup_vault": "name",
        "aws_cloudtrail": "name",
        "aws_kinesis_stream": "name",
        "aws_cloudwatch_event_rule": "name",
        "aws_sfn_state_machine": "name",
        "aws_s3_bucket_versioning": "bucket",
        "aws_s3_bucket_public_access_block": "bucket",
        "aws_key_pair": "key_name",
    }

    # Resources where the identifier is embedded in the resource name
    # Pattern: resource_name contains the ID we need to match
    NAME_BASED_RESOURCES = {
        "aws_api_gateway_deployment",
        "aws_api_gateway_resource",
        "aws_api_gateway_method",
        "aws_api_gateway_integration",
        "aws_api_gateway_rest_api",
        "aws_route53_record",
        "aws_lambda_permission",
        "aws_sns_topic_subscription",
        "aws_kms_key",
        "aws_guardduty_detector",
        "aws_cloudfront_distribution",
        "aws_cloudfront_origin_access_control",
        "aws_instance",
        "aws_vpc",
        "aws_subnet",
        "aws_security_group",
        "aws_internet_gateway",
        "aws_route_table",
        "aws_ebs_volume",
        "aws_network_interface",
        "aws_secretsmanager_secret_version",
        "aws_s3_bucket_versioning",
        "aws_s3_bucket_public_access_block",
        "aws_eventbridge_rule",
    }

    resources: Dict[str, str] = {}

    # Parse resource blocks from .tf files
    resource_pattern = re.compile(
        r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{',
        re.MULTILINE
    )
    # Pattern to extract attribute values
    attr_pattern = re.compile(r'^\s*(\w+)\s*=\s*"([^"]*)"', re.MULTILINE)

    for tf_file in output_dir.glob("*.tf"):
        if tf_file.name in ("imports.tf", "provider.tf", "variables.tf", "outputs.tf"):
            continue

        try:
            content = tf_file.read_text()

            for match in resource_pattern.finditer(content):
                resource_type = match.group(1)
                resource_name = match.group(2)

                # Find the block content
                start = match.end()
                brace_depth = 1
                end = start
                while end < len(content) and brace_depth > 0:
                    if content[end] == "{":
                        brace_depth += 1
                    elif content[end] == "}":
                        brace_depth -= 1
                    end += 1

                block_content = content[start:end]

                # For name-based resources, store the resource name itself as key
                if resource_type in NAME_BASED_RESOURCES:
                    key = f"{resource_type}:name:{resource_name}"
                    resources[key] = resource_name

                # Also try to extract identifier attribute
                identifier_attr = IDENTIFIER_ATTRS.get(resource_type)
                if identifier_attr:
                    for attr_match in attr_pattern.finditer(block_content):
                        if attr_match.group(1) == identifier_attr:
                            identifier_value = attr_match.group(2)
                            key = f"{resource_type}:{identifier_value}"
                            resources[key] = resource_name
                            break

        except Exception as e:
            print(f"Warning: Error parsing {tf_file.name}: {e}")
            continue

    return resources


def generate_imports_tf(output_dir: Path) -> Optional[Path]:
    """
    Generate imports.tf file by matching import JSON data with actual .tf resources.

    Creates Terraform 1.5+ native import blocks for direct state import.

    Args:
        output_dir: The output directory containing .tf files and import/ subdirectory

    Returns:
        Path to the generated imports.tf file, or None if no imports found
    """
    import_dir = output_dir / "import"
    if not import_dir.exists():
        return None

    # Map alternative resource type names to canonical Terraform types
    TYPE_ALIASES = {
        "aws_eventbridge_rule": "aws_cloudwatch_event_rule",
    }

    # Parse actual resource names from .tf files
    tf_resources = _parse_tf_resources(output_dir)

    imports = []
    imports.append("# Terraform import blocks")
    imports.append("# Generated by terraback")
    imports.append("# Terraform 1.5+ required")
    imports.append("#")
    imports.append("# Run: terraform plan to preview imports")
    imports.append("# Run: terraform apply to import resources into state\n")

    import_count = 0
    skipped_count = 0

    # Track used resource addresses to avoid duplicate imports
    used_addresses = set()

    # Process all import JSON files
    for json_file in sorted(import_dir.glob("*_import.json")):
        try:
            entries, error = read_import_file(json_file)
            if error:
                print(f"Warning: Could not read {json_file.name}: {error}")
                continue

            if not entries:
                continue

            # Add comment for this resource type
            resource_type = entries[0].get("resource_type", "unknown") if entries else "unknown"
            imports.append(f"# {resource_type}")

            for entry in entries:
                resource_type = entry.get("resource_type", "")
                remote_id = entry.get("remote_id", "")

                if not all([resource_type, remote_id]):
                    continue

                # Map to canonical type if needed
                canonical_type = TYPE_ALIASES.get(resource_type, resource_type)

                # Try to find matching resource in .tf files
                resource_name = _find_tf_resource_name(
                    canonical_type, remote_id, entry, tf_resources
                )

                if not resource_name:
                    skipped_count += 1
                    continue

                # Handle duplicate resource names by trying suffixed versions
                base_address = f"{canonical_type}.{resource_name}"
                address = base_address
                suffix = 2
                while address in used_addresses:
                    address = f"{canonical_type}.{resource_name}_{suffix}"
                    # Verify the suffixed version exists in .tf files
                    if f"{canonical_type}:name:{resource_name}_{suffix}" not in tf_resources:
                        # Check if it exists as a parsed resource
                        found_in_tf = False
                        for key in tf_resources:
                            if key.endswith(f":{resource_name}_{suffix}"):
                                found_in_tf = True
                                break
                        if not found_in_tf:
                            suffix += 1
                            continue
                    suffix += 1

                used_addresses.add(address)

                # Escape any quotes in the remote_id
                escaped_id = remote_id.replace('"', '\\"')

                # Extract the final resource name from the address
                final_resource_name = address.split(".")[-1]

                import_block = f'''import {{
  to = {canonical_type}.{final_resource_name}
  id = "{escaped_id}"
}}'''
                imports.append(import_block)
                import_count += 1

            imports.append("")  # Blank line between resource types

        except Exception as e:
            print(f"Warning: Error processing {json_file.name}: {e}")
            continue

    if import_count == 0:
        return None

    # Write the imports.tf file (ensure trailing newline)
    imports_tf_path = output_dir / "imports.tf"
    content = "\n".join(imports)
    if not content.endswith('\n'):
        content += '\n'
    imports_tf_path.write_text(content)
    print(f"Generated imports.tf with {import_count} import blocks")
    if skipped_count > 0:
        print(f"  Skipped {skipped_count} resources (no matching .tf resource found)")

    return imports_tf_path


def _find_tf_resource_name(
    resource_type: str,
    remote_id: str,
    entry: Dict[str, Any],
    tf_resources: Dict[str, str]
) -> Optional[str]:
    """Find the matching resource name in .tf files for an import entry."""

    # Build possible identifier values to search for
    resource_data = entry.get("resource_data", {})
    scanned_data = entry.get("scanned_data", {})
    json_resource_name = entry.get("resource_name", "")

    # First, try direct name-based lookup using the JSON resource_name
    # This works for resources where we store name:resource_name in the tf_resources
    name_key = f"{resource_type}:name:{json_resource_name}"
    if name_key in tf_resources:
        return tf_resources[name_key]

    # Try lowercase version (templates often lowercase resource names)
    name_key_lower = f"{resource_type}:name:{json_resource_name.lower()}"
    if name_key_lower in tf_resources:
        return tf_resources[name_key_lower]

    # Try with hyphens converted to underscores (Terraform naming convention)
    name_normalized = json_resource_name.replace("-", "_")
    name_key_normalized = f"{resource_type}:name:{name_normalized}"
    if name_key_normalized in tf_resources:
        return tf_resources[name_key_normalized]

    # Try lowercase + normalized
    name_key_lower_normalized = f"{resource_type}:name:{name_normalized.lower()}"
    if name_key_lower_normalized in tf_resources:
        return tf_resources[name_key_lower_normalized]

    # Try different identifier values based on resource type
    identifier_values = []

    # Common patterns for identifier extraction
    if resource_type == "aws_dynamodb_table":
        identifier_values.append(resource_data.get("TableName"))
        identifier_values.append(scanned_data.get("TableName"))
        identifier_values.append(remote_id)
    elif resource_type == "aws_lambda_function":
        identifier_values.append(resource_data.get("FunctionName"))
        identifier_values.append(scanned_data.get("FunctionName"))
        identifier_values.append(remote_id)
    elif resource_type == "aws_s3_bucket":
        identifier_values.append(resource_data.get("Name"))
        identifier_values.append(scanned_data.get("Name"))
        identifier_values.append(remote_id)
    elif resource_type == "aws_iam_role":
        identifier_values.append(resource_data.get("RoleName"))
        identifier_values.append(scanned_data.get("RoleName"))
    elif resource_type == "aws_iam_policy":
        identifier_values.append(resource_data.get("PolicyName"))
        identifier_values.append(scanned_data.get("PolicyName"))
    elif resource_type == "aws_ecs_cluster":
        identifier_values.append(resource_data.get("clusterName"))
        identifier_values.append(scanned_data.get("clusterName"))
    elif resource_type == "aws_ecr_repository":
        identifier_values.append(resource_data.get("repositoryName"))
        identifier_values.append(scanned_data.get("repositoryName"))
    elif resource_type == "aws_cloudwatch_log_group":
        identifier_values.append(resource_data.get("logGroupName"))
        identifier_values.append(scanned_data.get("logGroupName"))
    elif resource_type == "aws_cloudwatch_metric_alarm":
        identifier_values.append(resource_data.get("AlarmName"))
        identifier_values.append(scanned_data.get("AlarmName"))
    elif resource_type == "aws_acm_certificate":
        identifier_values.append(resource_data.get("DomainName"))
        identifier_values.append(scanned_data.get("DomainName"))
    elif resource_type == "aws_route53_zone":
        identifier_values.append(resource_data.get("Name"))
        identifier_values.append(scanned_data.get("Name"))
    elif resource_type == "aws_sns_topic":
        topic_arn = resource_data.get("TopicArn") or scanned_data.get("TopicArn")
        if topic_arn:
            identifier_values.append(topic_arn.split(":")[-1])
    elif resource_type in ("aws_s3_bucket_versioning", "aws_s3_bucket_public_access_block"):
        # These use the bucket name which is stored in the resource name (name_sanitized)
        # The template uses the same resource name as the S3 bucket
        identifier_values.append(resource_data.get("Name"))
        identifier_values.append(scanned_data.get("Name"))
        identifier_values.append(resource_data.get("name_sanitized"))
    elif resource_type == "aws_key_pair":
        identifier_values.append(resource_data.get("KeyName"))
        identifier_values.append(scanned_data.get("KeyName"))
    else:
        # Generic: try Name, name, id
        identifier_values.append(resource_data.get("Name"))
        identifier_values.append(resource_data.get("name"))
        identifier_values.append(scanned_data.get("Name"))
        identifier_values.append(scanned_data.get("name"))
        identifier_values.append(remote_id)

    # Search for matching resource by identifier
    for identifier in identifier_values:
        if not identifier:
            continue
        key = f"{resource_type}:{identifier}"
        if key in tf_resources:
            return tf_resources[key]

    return None
