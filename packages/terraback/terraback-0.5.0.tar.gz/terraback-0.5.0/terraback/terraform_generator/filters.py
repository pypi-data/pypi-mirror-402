# terraback/terraform_generator/filters.py

import json
import re

def sanitize_for_terraform(value):
    """
    A general-purpose sanitizer for Terraform resource names.
    
    Terraform resource names must:
    - Contain only letters, numbers, underscores, and hyphens
    - Start with a letter or underscore
    - Be unique within their resource type
    """
    if not isinstance(value, str):
        value = str(value)
    
    # Replace dots and other special characters with underscores
    value = re.sub(r'[^a-zA-Z0-9_-]', '_', value)
    
    # Replace multiple consecutive underscores with a single underscore
    value = re.sub(r'_{2,}', '_', value)
    
    # Remove leading/trailing underscores or hyphens
    value = value.strip('_-')
    
    # Ensure it starts with a letter or underscore (not a number)
    if value and value[0].isdigit():
        value = 'resource_' + value
    
    # Ensure we have a valid name
    if not value:
        value = "unnamed_resource"
    
    return value


def is_gcp_computed_field(field_name: str) -> bool:
    """
    Check if a field is computed-only in GCP resources and should not be
    included in ignore_changes blocks as it causes terraform warnings.

    Based on Terraform Google Provider documentation for common resource types.
    """
    computed_fields = {
        # Universal computed fields (present on most resources)
        'id', 'self_link', 'url', 'creation_timestamp', 'time_created',
        'updated', 'fingerprint', 'etag', 'project', 'zone', 'region',
        'kind', 'name', 'terraform_labels', 'effective_labels',

        # google_storage_bucket computed fields
        'bucket_policy_only', 'metageneration', 'md5_hash', 'crc32c',
        'media_link', 'output_name', 'public_access_prevention',

        # google_compute_instance computed fields
        'instance_id', 'machine_type', 'status', 'cpu_platform',
        'label_fingerprint', 'metadata_fingerprint', 'tags_fingerprint',
        'current_status', 'min_cpu_platform', 'nat_ip', 'network_ip',
        'access_config', 'guest_accelerator', 'effective_labels',

        # google_compute_disk computed fields
        'source_image_id', 'source_snapshot_id', 'users', 'disk_id',
        'source_disk_id', 'last_attach_timestamp', 'last_detach_timestamp',

        # google_compute_network computed fields
        'gateway_ipv4', 'internal_ipv6_range', 'numeric_id',

        # google_compute_subnetwork computed fields
        'gateway_address', 'ipv4_range', 'network_id', 'subnetwork_id',
        'internal_ipv6_prefix', 'ipv6_cidr_range', 'external_ipv6_prefix',

        # google_sql_database_instance computed fields
        'connection_name', 'first_ip_address', 'public_ip_address',
        'private_ip_address', 'server_ca_cert', 'service_account_email_address',
        'psc_service_attachment_link', 'dns_name', 'available_maintenance_versions',

        # google_container_cluster (GKE) computed fields
        'endpoint', 'master_version', 'services_ipv4_cidr', 'cluster_ipv4_cidr',
        'tpu_ipv4_cidr_block', 'operation', 'master_auth', 'node_version',
        'services_ipv6_cidr_block', 'cluster_ipv6_cidr_block',

        # google_container_node_pool computed fields
        'instance_group_urls', 'managed_instance_group_urls', 'version',

        # google_cloud_run_service computed fields
        'status', 'traffic', 'latest_created_revision_name',
        'latest_ready_revision_name', 'observed_generation',

        # google_pubsub_topic computed fields
        'message_storage_policy',

        # google_pubsub_subscription computed fields
        'effective_labels',

        # google_compute_firewall computed fields
        'creation_timestamp',

        # google_compute_address computed fields
        'address', 'users', 'status', 'label_fingerprint',

        # google_project_service computed fields
        'state',

        # google_service_account computed fields
        'email', 'unique_id', 'member',

        # google_kms_crypto_key computed fields
        'primary',

        # google_bigquery_dataset computed fields
        'last_modified_time', 'creation_time', 'default_encryption_configuration',

        # google_bigquery_table computed fields
        'last_modified_time', 'creation_time', 'num_bytes', 'num_long_term_bytes',
        'num_rows', 'type', 'external_data_configuration',

        # google_dns_managed_zone computed fields
        'name_servers', 'managed_zone_id', 'creation_time',

        # google_dns_record_set computed fields
        'routing_policy',

        # google_secret_manager_secret computed fields
        'create_time', 'name',

        # google_secret_manager_secret_version computed fields
        'create_time', 'destroy_time', 'name', 'version',

        # google_cloudfunctions_function computed fields
        'https_trigger_url', 'https_trigger_security_level', 'status',
        'version_id', 'update_time', 'effective_labels',

        # google_cloudfunctions2_function computed fields
        'state', 'update_time', 'url', 'environment', 'effective_labels',

        # google_compute_instance_template computed fields
        'metadata_fingerprint', 'self_link_unique', 'tags_fingerprint',

        # google_compute_region_instance_group_manager computed fields
        'instance_group', 'status', 'fingerprint', 'self_link',

        # google_compute_instance_group_manager computed fields
        'instance_group', 'status', 'fingerprint', 'self_link',

        # google_logging_project_sink computed fields
        'writer_identity',

        # google_monitoring_alert_policy computed fields
        'creation_record', 'name',

        # google_redis_instance computed fields
        'host', 'port', 'current_location_id', 'create_time',
        'persistence_iam_identity', 'server_ca_certs', 'nodes',

        # google_spanner_instance computed fields
        'state',

        # google_spanner_database computed fields
        'state',

        # google_filestore_instance computed fields
        'create_time', 'etag', 'networks', 'state',

        # google_memcache_instance computed fields
        'discovery_endpoint', 'memcache_nodes', 'create_time', 'state',

        # google_dataproc_cluster computed fields
        'cluster_uuid',

        # google_composer_environment computed fields
        'config', 'state',
    }

    # Convert field name to lowercase for comparison
    field_lower = field_name.lower().strip().strip('"').strip("'")

    # Direct match
    if field_lower in computed_fields:
        return True

    # Pattern-based matching for common computed suffixes/patterns
    computed_patterns = [
        'fingerprint',      # All *_fingerprint fields
        'timestamp',        # All *_timestamp fields
        '_link',            # All *_link fields (self_link, etc.)
        '_url',             # All *_url fields
        '_id',              # Most *_id fields are computed
        '_time',            # All *_time fields
        '_date',            # All *_date fields
        'effective_',       # effective_labels, effective_annotations
        '_identity',        # service account identities
        '_version',         # version fields
        'num_',             # num_rows, num_bytes, etc.
    ]

    return any(pattern in field_lower for pattern in computed_patterns)


def filter_computed_fields_from_ignore_changes(ignore_fields: list, provider: str = 'gcp') -> list:
    """
    Filter out computed-only fields from ignore_changes lists to prevent
    terraform warnings during plan/apply operations.
    """
    if provider == 'gcp':
        return [field for field in ignore_fields if not is_gcp_computed_field(field)]
    
    # For other providers, return as-is for now
    return ignore_fields


def to_terraform_resource_name(value: str) -> str:
    """Return a string safe to use as a Terraform resource name."""
    if not value:
        return "unnamed_resource"

    name = str(value)

    # If an ARN or path-like string is provided, grab the last segment
    if name.startswith("arn:"):
        name = name.split(":")[-1]
    if "/" in name:
        name = name.split("/")[-1]

    # Replace invalid characters with underscores
    name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    
    name = name.replace("-", "_")
    
    name = re.sub(r"_{2,}", "_", name)
    name = name.strip("_-")

    if name and name[0].isdigit():
        name = f"resource_{name}"

    if not name:
        name = "unnamed_resource"

    return name.lower()

# Enhanced conditional filters that prevent empty assignments
def has_value(value):
    """Check if a value exists and is not empty/None/whitespace."""
    if value is None:
        return False
    if isinstance(value, str) and value.strip() == "":
        return False
    if isinstance(value, (list, dict)) and len(value) == 0:
        return False
    # Handle boolean False as having value (important for Terraform)
    if isinstance(value, bool):
        return True
    return True

def is_defined(value):
    """Check if value is defined (not None)"""
    return value is not None

def is_not_none(value):
    """Check if value is not None"""
    return value is not None

def safe_get(obj, key, default=None):
    """Safely get a value from a dict, handling None objects"""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default

def default_if_empty(value, default=""):
    """Return default if value is None or empty"""
    if not has_value(value):
        return default
    return value

def safe_int(value, default=0):
    """Safely convert to int with default and better error handling."""
    if value is None:
        return default
    try:
        if isinstance(value, str) and value.strip() == "":
            return default
        # Handle string floats like "3.0"
        return int(float(value))
    except (ValueError, TypeError):
        return default

def safe_bool(value, default=False):
    """Safely convert to boolean string for Terraform with proper lowercase output."""
    if value is None:
        return str(default).lower()
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, str):
        return "true" if value.lower() in ['true', 'yes', '1', 'on', 'enabled'] else "false"
    return str(bool(value)).lower()

def terraform_bool(value):
    """Convert Python boolean to Terraform boolean string - enhanced version."""
    if value is None:
        return "false"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, str):
        # Handle various string representations
        if value.lower() in ['true', 'yes', '1', 'on', 'enabled']:
            return "true"
        elif value.lower() in ['false', 'no', '0', 'off', 'disabled']:
            return "false"
        else:
            # Try to parse as boolean
            try:
                return str(bool(value)).lower()
            except Exception:
                return "false"
    return str(bool(value)).lower()

# JSON handling with better None/empty support
def tojson(value):
    """Formats a Python value as JSON for use in Terraform templates."""
    if value is None:
        return "null"
    
    if isinstance(value, bool):
        return str(value).lower()  # Ensure terraform-style booleans
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        return json.dumps(value)
    elif isinstance(value, (list, dict)):
        return json.dumps(value, indent=2, default=str)
    else:
        return json.dumps(str(value))

def to_terraform_collection(value, collection_type='list'):
    """Convert a value to proper Terraform collection type (list or map).
    Handles empty strings by converting them to empty collections."""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        if collection_type == 'map' or collection_type == 'dict':
            return "{}"
        else:
            return "[]"
    
    if isinstance(value, str):
        # If it's already a valid JSON collection string, return it
        try:
            parsed = json.loads(value)
            if isinstance(parsed, (list, dict)):
                return json.dumps(parsed, indent=2, default=str)
        except:
            pass
        # Otherwise treat as single-item list/map
        if collection_type == 'map' or collection_type == 'dict':
            return "{}"
        else:
            return json.dumps([value])
    
    if isinstance(value, (list, dict)):
        return json.dumps(value, indent=2, default=str)
    
    # Default behavior
    if collection_type == 'map' or collection_type == 'dict':
        return "{}"
    else:
        return "[]"

# AWS ID prefix removal with better handling
AWS_ID_PREFIXES = [
    "vpc-", "subnet-", "sg-", "i-", "ami-", "vol-", "lt-", "lc-", 
    "eni-", "rtb-", "acl-", "igw-", "snap-", "eipalloc-", "eipassoc-", 
    "pcx-", "lb-", "tg-", "natgw-", "vpce-", "rtbassoc-"
]

def strip_id_prefix(id_str: str) -> str:
    """Remove common AWS ID prefixes and ARN prefixes from a string."""
    if not isinstance(id_str, str):
        return str(id_str) if id_str is not None else "unknown"

    val = str(id_str)

    if val.startswith("arn:"):
        val = val.split(":")[-1]
        val = val.split("/")[-1]

    for prefix in AWS_ID_PREFIXES:
        if val.startswith(prefix):
            val = val[len(prefix):]
            break

    # Remove common IAM path prefixes
    for p in ("role/", "policy/", "user/"):
        if val.startswith(p):
            val = val[len(p):]
            break

    # Ensure we return something valid
    if not val:
        val = "unknown"

    return val

# Enhanced Terraform type converters that never generate empty assignments
def to_terraform_string(value):
    """Formats a Python string into a Terraform-safe string."""
    if value is None:
        return None  # Return None so template can skip the assignment
    return json.dumps(str(value))

def to_terraform_list(value):
    """Formats a Python list into a Terraform list."""
    if value is None or (isinstance(value, list) and len(value) == 0):
        return None  # Return None so template can skip the assignment
    if not isinstance(value, list):
        value = [value]
    return json.dumps(value)

def to_terraform_map(value):
    """Formats a Python dictionary into a Terraform map."""
    if value is None or (isinstance(value, dict) and len(value) == 0):
        return None  # Return None so template can skip the assignment
    if not isinstance(value, dict):
        return None
    return json.dumps(value)

def to_terraform_bool(value):
    """Formats a Python boolean into a Terraform boolean."""
    if value is None:
        return None  # Return None so template can skip the assignment
    return terraform_bool(value)

def to_terraform_int(value):
    """Formats a Python integer into a Terraform number."""
    if value is None:
        return None  # Return None so template can skip the assignment
    try:
        return str(int(value))
    except (ValueError, TypeError):
        return None

def to_terraform_float(value):
    """Formats a Python float into a Terraform number."""
    if value is None:
        return None  # Return None so template can skip the assignment
    try:
        return str(float(value))
    except (ValueError, TypeError):
        return None

# Resource name generator with guaranteed valid output
def generate_resource_name(resource_data, fallback_prefix="resource"):
    """Generate a valid Terraform resource name from resource data"""
    
    # Try various fields that might contain a name
    name_candidates = []
    
    if isinstance(resource_data, dict):
        # Common name fields
        for field in ['Name', 'name', 'ResourceName', 'FunctionName', 'AlarmName', 
                     'PolicyName', 'RoleName', 'LoadBalancerName', 'TargetGroupName',
                     'ClusterName', 'TableName', 'BucketName']:
            if field in resource_data and resource_data[field]:
                name_candidates.append(str(resource_data[field]))
        
        # Try ID fields as fallback
        for field in ['Id', 'id', 'ResourceId', 'InstanceId', 'VolumeId']:
            if field in resource_data and resource_data[field]:
                name_candidates.append(str(resource_data[field]))
    
    # Use the first valid candidate
    for candidate in name_candidates:
        sanitized = to_terraform_resource_name(candidate)
        if sanitized != "unnamed_resource":
            return sanitized
    
    # Ultimate fallback
    return f"{fallback_prefix}_resource"

# String manipulation filters with enhanced null safety
def escape_quotes(value):
    """Escape quotes in strings for Terraform with better null handling."""
    if value is None:
        return ""
    return str(value).replace('"', '\\"').replace("'", "\\'")

def strip_whitespace(value):
    """Strip whitespace from strings"""
    if value is None:
        return ""
    return str(value).strip()

def sanitize_public_key(value):
    """Collapse whitespace in an SSH public key to a single line."""
    if not value:
        return value
    return " ".join(str(value).split())

def quote_txt_value(value: str) -> str:
    """Return TXT record value quoted exactly once."""
    if value is None:
        return '""'
    val = str(value)
    val_strip = val.strip()
    if val_strip.startswith('"') and val_strip.endswith('"'):
        return val_strip
    return f'"{val_strip}"'

def terraform_name(value):
    """Comprehensive name sanitization for Terraform identifiers - enhanced version."""
    if not value:
        return "unnamed_resource"
    
    # Convert to string and handle various input types
    name = str(value)
    
    # Extract meaningful part from ARNs, paths, etc.
    if ":" in name:
        name = name.split(":")[-1]
    if "/" in name:
        name = name.split("/")[-1]
    
    # Remove or replace invalid characters
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    name = name.replace('-', '_')  # Terraform resource names cannot contain hyphens
    name = re.sub(r'_+', '_', name)  # Replace multiple underscores
    name = name.strip('_-')
    
    # Ensure it starts with letter or underscore
    if name and name[0].isdigit():
        name = f"res_{name}"
    
    # Ensure minimum length and validity
    if not name or len(name) < 1:
        name = "unnamed_resource"
    
    return name.lower()

def terraform_sanitize_name(value):
    """Alias for terraform_name for backward compatibility."""
    return terraform_name(value)

# Template-specific helpers with enhanced functionality
def format_tags(tags_dict):
    """Format tags dictionary for Terraform with proper escaping"""
    if not tags_dict or not isinstance(tags_dict, dict):
        return None
    
    formatted = {}
    for key, value in tags_dict.items():
        if key and value is not None:
            # Handle various value types
            if isinstance(value, bool):
                formatted[str(key)] = str(value).lower()
            else:
                formatted[str(key)] = str(value)
    
    return formatted if formatted else None

def format_cidr_blocks(cidr_list):
    """Format CIDR blocks list for Terraform"""
    if not cidr_list:
        return None
    
    if isinstance(cidr_list, str):
        return [cidr_list]
    
    if isinstance(cidr_list, list):
        return [str(cidr) for cidr in cidr_list if cidr]
    
    return None

def format_security_groups(sg_list):
    """Format security groups list for Terraform"""
    if not sg_list:
        return None
    
    if isinstance(sg_list, str):
        return [sg_list]
    
    if isinstance(sg_list, list):
        formatted = []
        for sg in sg_list:
            if isinstance(sg, dict) and 'GroupId' in sg:
                formatted.append(sg['GroupId'])
            elif isinstance(sg, str):
                formatted.append(sg)
        return formatted if formatted else None
    
    return None

def format_resource_reference(resource_type, resource_name):
    """Format a Terraform resource reference properly."""
    safe_type = terraform_name(resource_type)
    safe_name = terraform_name(resource_name)
    return f"{safe_type}.{safe_name}"

def conditional_block(condition, content):
    """Only render content block if condition is true and content exists."""
    if not condition or not content:
        return ""
    return content

def strip_empty_lines(text):
    """Remove excessive empty lines from generated content."""
    if not text:
        return ""
    # Replace multiple consecutive newlines with double newline
    cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    # Strip but preserve trailing newline for proper file formatting
    cleaned = cleaned.strip()
    return cleaned + '\n' if cleaned else ""

def join_with_commas(items, quote=True):
    """Join items with commas, optionally quoting strings."""
    if not items:
        return ""
    
    if quote:
        quoted_items = [f'"{item}"' for item in items]
        return ", ".join(quoted_items)
    else:
        return ", ".join(str(item) for item in items)

def indent_text(text, spaces=2):
    """Indent text by specified number of spaces."""
    if not text:
        return ""
    
    indent = " " * spaces
    lines = text.split('\n')
    return '\n'.join(indent + line if line.strip() else line for line in lines)

# Enhanced validation filters
def validate_port(port, default=80):
    """Validate and return a valid port number."""
    try:
        port_num = int(port)
        if 1 <= port_num <= 65535:
            return port_num
        return default
    except (ValueError, TypeError):
        return default

def validate_cidr(cidr, default="0.0.0.0/0"):
    """Basic CIDR validation."""
    if not cidr or not isinstance(cidr, str):
        return default
    
    # Basic regex for CIDR format
    cidr_pattern = r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$'
    if re.match(cidr_pattern, cidr.strip()):
        return cidr.strip()
    return default

def validate_arn(arn):
    """Basic ARN validation."""
    if not arn or not isinstance(arn, str):
        return False
    return arn.startswith('arn:aws:')

# Standard string filters with null safety - enhanced versions
def safe_lower(value):
    """Safely convert to lowercase."""
    return str(value).lower() if value is not None else ''

def safe_upper(value):
    """Safely convert to uppercase.""" 
    return str(value).upper() if value is not None else ''

def safe_replace(value, old, new):
    """Safely replace substrings."""
    return str(value).replace(old, new) if value is not None else ''

def safe_default(value, default=''):
    """Safely provide default value."""
    return value if value is not None else default

def safe_split(value, delimiter=','):
    """Safely split string into list."""
    if not value:
        return []
    return str(value).split(delimiter)

def safe_join(value, delimiter=', '):
    """Safely join list into string."""
    if not value or not isinstance(value, (list, tuple)):
        return ""
    return delimiter.join(str(item) for item in value)

# Special AWS filters
def extract_region_from_arn(arn):
    """Extract AWS region from ARN."""
    if not arn or not isinstance(arn, str):
        return ""
    
    parts = arn.split(':')
    if len(parts) >= 4:
        return parts[3]  # Region is the 4th component
    return ""

def extract_account_from_arn(arn):
    """Extract AWS account ID from ARN."""
    if not arn or not isinstance(arn, str):
        return ""
    
    parts = arn.split(':')
    if len(parts) >= 5:
        return parts[4]  # Account is the 5th component
    return ""

def extract_resource_from_arn(arn):
    """Extract resource name from ARN."""
    if not arn or not isinstance(arn, str):
        return ""
    
    parts = arn.split(':')
    if len(parts) >= 6:
        resource_part = parts[5]
        # Handle resource-type/resource-name format
        if '/' in resource_part:
            return resource_part.split('/')[-1]
        return resource_part
    return ""

# Collection manipulation filters
def group_by_key(items, key):
    """Group list of dicts by a specific key."""
    if not items or not isinstance(items, list):
        return {}
    
    grouped = {}
    for item in items:
        if isinstance(item, dict) and key in item:
            group_key = item[key]
            if group_key not in grouped:
                grouped[group_key] = []
            grouped[group_key].append(item)
    
    return grouped

def unique_values(items):
    """Get unique values from a list while preserving order."""
    if not items:
        return []
    
    seen = set()
    unique = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    
    return unique

def filter_by_key(items, key, value):
    """Filter list of dicts by key-value pair."""
    if not items or not isinstance(items, list):
        return []
    
    return [item for item in items 
            if isinstance(item, dict) and item.get(key) == value]

def sort_by_key(items, key, reverse=False):
    """Sort list of dicts by a specific key."""
    if not items or not isinstance(items, list):
        return items
    
    return sorted(items, 
                 key=lambda x: x.get(key, '') if isinstance(x, dict) else str(x),
                 reverse=reverse)

def find_storage_account_reference(storage_account_name: str, storage_accounts: dict) -> str:
    """Find a storage account by name and return its Terraform resource reference."""
    if not storage_account_name or not isinstance(storage_accounts, dict):
        return f'var.storage_account_key'
    
    # Look for storage account with matching name
    for item_id, item_data in storage_accounts.items():
        sa_data = item_data.get('data', {})
        if sa_data.get('name') == storage_account_name:
            # Generate terraform resource name for this storage account
            sa_terraform_name = terraform_name(sa_data.get('name_sanitized', sa_data.get('name', item_id)))
            return f'azurerm_storage_account.{sa_terraform_name}.primary_access_key'
    
    # If not found, fall back to variable
    return f'var.storage_account_key'

def find_resource_reference(resource_name: str, resource_type: str, attribute: str, all_resources: dict, fallback_var: str = None) -> str:
    """Universal function to find cross-resource references and generate Terraform resource references.
    
    Args:
        resource_name: Name of the resource to find
        resource_type: Type of resource (e.g., 'azure_storage_account', 'azure_key_vault')  
        attribute: Resource attribute to reference (e.g., 'primary_access_key', 'vault_uri')
        all_resources: Dictionary containing all scanned resources
        fallback_var: Variable name to use if resource not found
    
    Returns:
        Terraform resource reference or variable reference
    """
    if not resource_name or not isinstance(all_resources, dict):
        return f'var.{fallback_var or "resource_value"}'
    
    resources_of_type = all_resources.get(resource_type, {})
    
    # Look for resource with matching name
    for item_id, item_data in resources_of_type.items():
        resource_data = item_data.get('data', {})
        if resource_data.get('name') == resource_name:
            # Generate terraform resource name
            tf_resource_name = terraform_name(resource_data.get('name_sanitized', resource_data.get('name', item_id)))
            tf_resource_type = resource_type.replace('azure_', 'azurerm_').replace('aws_', 'aws_').replace('gcp_', 'google_')
            return f'{tf_resource_type}.{tf_resource_name}.{attribute}'
    
    # If not found, fall back to variable
    return f'var.{fallback_var or "resource_value"}'

def render_gcp_labels(resource: dict, indent: int = 2) -> str:
    """
    Render GCP resource labels in Terraform format with proper indentation.
    
    Args:
        resource: Resource dictionary containing labels
        indent: Number of spaces to indent the labels block
        
    Returns:
        Formatted labels block or empty string if no labels
    """
    labels = resource.get('labels', {})
    if not labels or not isinstance(labels, dict):
        return ""
    
    # Filter out empty labels
    filtered_labels = {k: v for k, v in labels.items() if k and v is not None}
    if not filtered_labels:
        return ""
    
    indent_str = " " * indent
    lines = [f"{indent_str}labels = {{"]
    
    for key, value in filtered_labels.items():
        # Sanitize key and value for Terraform
        tf_key = str(key).strip()
        tf_value = str(value).strip()
        
        # Ensure key is valid Terraform identifier
        tf_key = re.sub(r'[^a-zA-Z0-9_-]', '_', tf_key)
        
        lines.append(f'{indent_str}  "{tf_key}" = "{tf_value}"')
    
    lines.append(f"{indent_str}}}")
    return "\n".join(lines)


def normalize_location(location: str, provider: str = None) -> str:
    """
    Normalize cloud provider location from display name to canonical name.
    
    Different cloud providers use different formats:
    - Azure API returns display names like "East US", Terraform expects "eastus"
    - AWS uses consistent region names like "us-east-1" 
    - GCP uses consistent region names like "us-central1"
    
    Args:
        location: The location display name
        provider: Cloud provider ('azure', 'aws', 'gcp') - auto-detected if not provided
        
    Returns:
        The normalized location name
    """
    if not location or not isinstance(location, str):
        return location
    
    # Auto-detect provider if not specified
    if not provider:
        if any(keyword in location.lower() for keyword in ['us-', 'eu-', 'ap-', 'ca-', 'sa-']):
            if 'central1' in location.lower() or 'west1' in location.lower() or 'east1' in location.lower():
                provider = 'gcp'
            else:
                provider = 'aws'
        else:
            provider = 'azure'  # Default to Azure for display names
    
    # Azure location normalization
    if provider == 'azure':
        azure_location_map = {
            'East US': 'eastus',
            'East US 2': 'eastus2',
            'West US': 'westus',
            'West US 2': 'westus2',
            'West US 3': 'westus3',
            'Central US': 'centralus',
            'North Central US': 'northcentralus',
            'South Central US': 'southcentralus',
            'West Central US': 'westcentralus',
            'Canada Central': 'canadacentral',
            'Canada East': 'canadaeast',
            'Brazil South': 'brazilsouth',
            'North Europe': 'northeurope',
            'West Europe': 'westeurope',
            'UK South': 'uksouth',
            'UK West': 'ukwest',
            'France Central': 'francecentral',
            'France South': 'francesouth',
            'Germany West Central': 'germanywestcentral',
            'Germany North': 'germanynorth',
            'Norway East': 'norwayeast',
            'Norway West': 'norwaywest',
            'Switzerland North': 'switzerlandnorth',
            'Switzerland West': 'switzerlandwest',
            'Southeast Asia': 'southeastasia',
            'East Asia': 'eastasia',
            'Australia East': 'australiaeast',
            'Australia Southeast': 'australiasoutheast',
            'Australia Central': 'australiacentral',
            'Australia Central 2': 'australiacentral2',
            'Japan East': 'japaneast',
            'Japan West': 'japanwest',
            'Korea Central': 'koreacentral',
            'Korea South': 'koreasouth',
            'Central India': 'centralindia',
            'South India': 'southindia',
            'West India': 'westindia',
            'UAE North': 'uaenorth',
            'UAE Central': 'uaecentral',
            'South Africa North': 'southafricanorth',
            'South Africa West': 'southafricawest',
        }
        
        # Check if we have a direct mapping
        if location in azure_location_map:
            return azure_location_map[location]
        
        # If no direct mapping, convert to lowercase and remove spaces/special chars
        normalized = location.lower().replace(' ', '').replace('-', '').replace('_', '')
        return normalized
    
    # AWS and GCP typically use consistent naming already
    elif provider in ['aws', 'gcp']:
        # AWS regions: us-east-1, eu-west-1, ap-southeast-1, etc.
        # GCP regions: us-central1, europe-west1, asia-southeast1, etc.
        # These are typically already in the correct format
        return location.lower()
    
    # Fallback: lowercase and clean up
    return location.lower().replace(' ', '').replace('_', '')


# Export all filters for easy registration
ALL_FILTERS = {
    # Basic sanitization
    'sanitize': sanitize_for_terraform,
    'tf_resource_name': to_terraform_resource_name,
    'terraform_name': terraform_name,
    'terraform_sanitize_name': terraform_sanitize_name,
    
    # Type conversion
    'tf_string': to_terraform_string,
    'tf_list': to_terraform_list,
    'tf_map': to_terraform_map,
    'tf_bool': to_terraform_bool,
    'tf_int': to_terraform_int,
    'tf_float': to_terraform_float,
    'tojson': tojson,
    'to_terraform_collection': to_terraform_collection,
    'tf_collection': to_terraform_collection,
    
    # Safe conversion
    'safe_int': safe_int,
    'safe_bool': safe_bool,
    'terraform_bool': terraform_bool,
    'safe_lower': safe_lower,
    'safe_upper': safe_upper,
    'safe_replace': safe_replace,
    'safe_default': safe_default,
    'safe_split': safe_split,
    'safe_join': safe_join,
    
    # ID and name handling
    'strip_id_prefix': strip_id_prefix,
    'generate_name': generate_resource_name,
    
    # Conditional checks
    'has_value': has_value,
    'is_defined': is_defined,
    'is_not_none': is_not_none,
    'safe_get': safe_get,
    'default_if_empty': default_if_empty,
    
    # String manipulation
    'escape_quotes': escape_quotes,
    'strip_whitespace': strip_whitespace,
    'sanitize_public_key': sanitize_public_key,
    'quote_txt_value': quote_txt_value,
    'strip_empty_lines': strip_empty_lines,
    'indent_text': indent_text,
    'join_with_commas': join_with_commas,
    
    # Formatting helpers
    'format_tags': format_tags,
    'format_cidrs': format_cidr_blocks,
    'format_sgs': format_security_groups,
    'format_resource_reference': format_resource_reference,
    'conditional_block': conditional_block,
    
    # Validation
    'validate_port': validate_port,
    'validate_cidr': validate_cidr,
    'validate_arn': validate_arn,
    
    # AWS specific
    'extract_region_from_arn': extract_region_from_arn,
    'extract_account_from_arn': extract_account_from_arn,
    'extract_resource_from_arn': extract_resource_from_arn,
    
    # Collection manipulation
    'group_by_key': group_by_key,
    'unique_values': unique_values,
    'filter_by_key': filter_by_key,
    'sort_by_key': sort_by_key,
    
    # Cross-resource references
    'find_storage_account_reference': find_storage_account_reference,
    'find_resource_reference': find_resource_reference,
    
    # Location normalization (multi-cloud)
    'normalize_location': normalize_location,
    
    # GCP specific
    'is_gcp_computed_field': is_gcp_computed_field,
    'filter_computed_fields_from_ignore_changes': filter_computed_fields_from_ignore_changes,
    'render_gcp_labels': render_gcp_labels,
    
    # Legacy compatibility
    'lower': safe_lower,
    'upper': safe_upper,
    'replace': safe_replace,
    'default': safe_default,
    'safe': lambda x: x,  # For marking strings as safe
}
