"""
Full-stack Terraform generation for enterprise modules.

This module generates complete, deployment-ready Terraform stacks from scanned
cloud resources. It orchestrates module generation, root configuration, and
environment setup.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

from terraback.utils.enterprise_modules import EnterpriseModuleGenerator, RESOURCE_MODULE_MAP
from terraback.utils.logging import get_logger
from terraback.core.license import check_feature_access, Tier
from terraback.terraform_generator.writer import generate_provider_config

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Configuration Classes
# ---------------------------------------------------------------------------

@dataclass
class EnvironmentConfig:
    """Configuration for a single environment."""
    name: str
    resources: Dict[str, List[Dict]]
    tags: Dict[str, str]
    region: Optional[str] = None


@dataclass
class StackGenerationResult:
    """Result of stack generation."""
    root_files: List[Path]
    module_files: List[Path]
    config_files: List[Path]
    environments: List[str]
    import_blocks_generated: bool
    errors: List[str]


# ---------------------------------------------------------------------------
# Environment Detection
# ---------------------------------------------------------------------------

class EnvironmentDetector:
    """Detects environments from resource naming and tagging patterns."""

    ENV_PATTERNS = [
        r'[-_](dev|development)[-_]?',
        r'[-_](prod|production)[-_]?',
        r'[-_](test|testing)[-_]?',
        r'[-_](stage|staging)[-_]?',
        r'[-_](qa)[-_]?',
        r'[-_](sandbox)[-_]?',
        r'[-_](dr)[-_]?',
    ]

    def detect_environments(
        self,
        resources: Dict[str, List[Dict]],
        provider: str
    ) -> Dict[str, EnvironmentConfig]:
        """
        Analyze resources to detect environment boundaries.
        Returns mapping of environment name to its resources.
        """
        env_resources = {}

        for resource_type, resource_list in resources.items():
            for resource in resource_list:
                # Strategy 1: Check tags first (highest confidence)
                env = self._extract_env_from_tags(resource, provider)

                # Strategy 2: Parse resource names
                if not env:
                    env = self._extract_env_from_name(resource)

                # Strategy 3: Default to "default" if no match
                if not env:
                    env = "default"

                # Store environment in resource for later use
                resource['_environment'] = env

                # Group resource by environment
                if env not in env_resources:
                    env_resources[env] = {}
                if resource_type not in env_resources[env]:
                    env_resources[env][resource_type] = []
                env_resources[env][resource_type].append(resource)

        # Convert to EnvironmentConfig objects
        env_configs = {}
        for env_name, env_res in env_resources.items():
            env_configs[env_name] = EnvironmentConfig(
                name=env_name,
                resources=env_res,
                tags=self._generate_env_tags(env_name),
                region=self._detect_primary_region(env_res, provider)
            )

        return env_configs

    def _extract_env_from_tags(
        self, resource: Dict, provider: str
    ) -> Optional[str]:
        """Extract environment from resource tags."""
        if provider == "aws":
            tags = resource.get("Tags", [])

            # Handle both AWS API format (list of dicts) and import JSON format (dict)
            if isinstance(tags, dict):
                # Import JSON format: {"Environment": "production", "Service": "app"}
                for key in ["Environment", "environment", "Env", "env"]:
                    if key in tags:
                        return str(tags[key]).lower()
            elif isinstance(tags, list):
                # AWS API format: [{"Key": "Environment", "Value": "production"}]
                for tag in tags:
                    if isinstance(tag, dict) and tag.get("Key", "").lower() in ["environment", "env"]:
                        return tag.get("Value", "").lower()
        elif provider == "azure":
            tags = resource.get("tags", {})
            for key in ["environment", "env", "Environment", "Env"]:
                if key in tags:
                    return str(tags[key]).lower()
        elif provider == "gcp":
            labels = resource.get("labels", {})
            for key in ["environment", "env"]:
                if key in labels:
                    return str(labels[key]).lower()
        return None

    def _extract_env_from_name(self, resource: Dict) -> Optional[str]:
        """Extract environment from naming patterns."""
        name = resource.get("Name") or resource.get("name", "")
        if isinstance(name, dict):
            name = name.get("Value", "")

        name = str(name).lower()

        for pattern in self.ENV_PATTERNS:
            match = re.search(pattern, name)
            if match:
                return match.group(1)

        return None

    def _generate_env_tags(self, env_name: str) -> Dict[str, str]:
        """Generate standard tags for an environment."""
        return {
            "Environment": env_name,
            "ManagedBy": "Terraback",
        }

    def _detect_primary_region(
        self, resources: Dict[str, List[Dict]], provider: str
    ) -> Optional[str]:
        """Detect the primary region for an environment."""
        regions = []

        for resource_type, resource_list in resources.items():
            for resource in resource_list:
                if provider == "aws":
                    region = resource.get("Region")
                elif provider == "azure":
                    region = resource.get("location")
                elif provider == "gcp":
                    region = resource.get("region")
                else:
                    region = None

                if region:
                    regions.append(region)

        # Return most common region
        if regions:
            return max(set(regions), key=regions.count)
        return None


# ---------------------------------------------------------------------------
# Import Block Generation
# ---------------------------------------------------------------------------

class ImportBlockGenerator:
    """Generates Terraform import blocks for module instances by reading actual module files.

    Features:
    - Basic import ID lookup for standard resources
    - Composite import ID generation for complex resources (API Gateway, Route53 records)
    - AWS ID extraction from resource names (sg-xxx, vpc-xxx patterns)
    - Multiple fallback strategies for ID matching
    - Optional validation of generated import blocks
    """

    # Mapping of resource type to (tf_attribute, scan_data_key) for import ID matching
    IMPORT_ID_ATTRIBUTES = {
        # AWS Core
        "aws_lambda_function": ("function_name", "FunctionName"),
        "aws_lambda_permission": ("statement_id", "StatementId"),
        "aws_s3_bucket": ("bucket", "Name"),
        "aws_s3_bucket_versioning": ("bucket", "Name"),
        "aws_s3_bucket_public_access_block": ("bucket", "Name"),
        "aws_dynamodb_table": ("name", "TableName"),
        "aws_iam_role": ("name", "RoleName"),
        "aws_iam_policy": ("arn", "Arn"),
        "aws_acm_certificate": ("arn", "CertificateArn"),
        "aws_cloudfront_distribution": ("id", "Id"),
        "aws_cloudfront_origin_access_control": ("name", "Name"),
        "aws_cloudwatch_log_group": ("name", "logGroupName"),
        "aws_cloudwatch_metric_alarm": ("alarm_name", "AlarmName"),
        "aws_kms_key": ("key_id", "KeyId"),
        "aws_kms_alias": ("name", "AliasName"),
        "aws_secretsmanager_secret": ("name", "Name"),
        "aws_secretsmanager_secret_version": ("secret_id", "SecretArn"),
        "aws_sns_topic": ("name", "TopicName"),
        "aws_sns_topic_subscription": ("arn", "SubscriptionArn"),
        "aws_sqs_queue": ("name", "QueueName"),
        "aws_security_group": ("id", "GroupId"),
        "aws_vpc": ("id", "VpcId"),
        "aws_subnet": ("id", "SubnetId"),
        "aws_internet_gateway": ("id", "InternetGatewayId"),
        "aws_route_table": ("id", "RouteTableId"),
        "aws_ebs_volume": ("id", "VolumeId"),
        "aws_instance": ("id", "InstanceId"),
        "aws_network_interface": ("id", "NetworkInterfaceId"),
        "aws_ecs_cluster": ("name", "clusterName"),
        "aws_ecr_repository": ("name", "repositoryName"),
        "aws_cloudtrail": ("name", "Name"),
        "aws_kinesis_stream": ("name", "StreamName"),
        "aws_cloudwatch_event_rule": ("name", "Name"),
        "aws_guardduty_detector": ("id", "DetectorId"),
        "aws_db_instance": ("identifier", "DBInstanceIdentifier"),
        "aws_db_subnet_group": ("name", "DBSubnetGroupName"),
        "aws_backup_vault": ("name", "BackupVaultName"),
        # API Gateway - uses composite IDs
        "aws_api_gateway_rest_api": ("id", "id"),
        "aws_api_gateway_resource": ("id", "id"),
        "aws_api_gateway_method": ("http_method", "httpMethod"),
        "aws_api_gateway_integration": ("http_method", "httpMethod"),
        "aws_api_gateway_deployment": ("id", "id"),
        # Route53
        "aws_route53_zone": ("zone_id", "ZoneId"),
        "aws_route53_record": ("name", "Name"),
        # Step Functions
        "aws_sfn_state_machine": ("name", "name"),
        # Azure
        "azurerm_resource_group": ("name", "name"),
        "azurerm_virtual_network": ("name", "name"),
        "azurerm_subnet": ("name", "name"),
        # GCP
        "google_compute_instance": ("name", "name"),
        "google_storage_bucket": ("name", "name"),
    }

    # Composite import IDs for resources requiring special ID formats
    # Format: resource_type -> (format_string, required_fields)
    COMPOSITE_IMPORT_IDS = {
        # API Gateway - methods and integrations need rest-api-id/resource-id/method
        "aws_api_gateway_method": {
            "format": "{rest_api_id}/{resource_id}/{http_method}",
            "fields": ["rest_api_id", "resource_id", "http_method"],
        },
        "aws_api_gateway_integration": {
            "format": "{rest_api_id}/{resource_id}/{http_method}",
            "fields": ["rest_api_id", "resource_id", "http_method"],
        },
        "aws_api_gateway_method_response": {
            "format": "{rest_api_id}/{resource_id}/{http_method}/{status_code}",
            "fields": ["rest_api_id", "resource_id", "http_method", "status_code"],
        },
        "aws_api_gateway_integration_response": {
            "format": "{rest_api_id}/{resource_id}/{http_method}/{status_code}",
            "fields": ["rest_api_id", "resource_id", "http_method", "status_code"],
        },
        # API Gateway - resources need rest-api-id/resource-id
        "aws_api_gateway_resource": {
            "format": "{rest_api_id}/{resource_id}",
            "fields": ["rest_api_id", "resource_id"],
        },
        # API Gateway - deployments need rest-api-id/deployment-id
        "aws_api_gateway_deployment": {
            "format": "{rest_api_id}/{deployment_id}",
            "fields": ["rest_api_id", "deployment_id"],
        },
        # Route53 records - zone-id_record-name_record-type
        "aws_route53_record": {
            "format": "{zone_id}_{name}_{type}",
            "fields": ["zone_id", "name", "type"],
        },
        # Lambda permissions - function-name/statement-id
        "aws_lambda_permission": {
            "format": "{function_name}/{statement_id}",
            "fields": ["function_name", "statement_id"],
        },
        # S3 bucket policies - bucket-name
        "aws_s3_bucket_policy": {
            "format": "{bucket}",
            "fields": ["bucket"],
        },
    }

    def generate_imports_from_modules(
        self,
        output_dir: Path,
        resources: Dict[str, List[Dict]],
        module_mapping: Dict[str, Tuple[str, str]],
        provider: str
    ) -> str:
        """
        Generate imports.tf by reading actual resource names from module files.

        Args:
            output_dir: Directory containing modules/
            resources: Scanned resources grouped by type (for import IDs)
            module_mapping: Resource type to (module_name, file_name) mapping
            provider: Cloud provider (aws, azure, gcp)

        Returns:
            Content for imports.tf file
        """
        imports = []
        imports.append("# Terraform import blocks")
        imports.append("# Generated by terraback")
        imports.append("# Terraform 1.5+ required\n")

        modules_dir = output_dir / "modules"
        if not modules_dir.exists():
            return "\n".join(imports)

        # Build lookup of import IDs from scan data
        import_id_lookup = self._build_import_id_lookup(resources, provider)

        # Process each module directory
        for module_dir in sorted(modules_dir.rglob("*")):
            if not module_dir.is_dir():
                continue

            # Get module name relative to modules/
            module_name = str(module_dir.relative_to(modules_dir))
            tf_module_name = module_name.replace("/", "-").replace("\\", "-")

            # Parse all .tf files in this module
            for tf_file in module_dir.glob("*.tf"):
                if tf_file.name in ("variables.tf", "outputs.tf", "locals.tf"):
                    continue

                content = tf_file.read_text()
                for resource_type, resource_name, identifier_value, block_content in self._extract_resources(content):
                    # Check if this resource type needs a composite import ID
                    if resource_type in self.COMPOSITE_IMPORT_IDS:
                        # Find the resource in scan data for composite ID building
                        resource_data = self._find_resource_data(
                            resource_type, identifier_value, resources, provider
                        )
                        if resource_data:
                            import_id = self._build_composite_import_id(
                                resource_type, resource_data, block_content
                            )
                        else:
                            import_id = ""
                    else:
                        # Find the import ID for this resource using standard lookup
                        import_id = self._find_import_id(
                            resource_type, identifier_value, import_id_lookup, provider
                        )

                    if import_id:
                        import_block = f'''import {{
  to = module.{tf_module_name}.{resource_type}.{resource_name}
  id = "{import_id}"
}}'''
                        imports.append(import_block)

        return "\n".join(imports)

    def _find_resource_data(
        self,
        resource_type: str,
        identifier_value: str,
        resources: Dict[str, List[Dict]],
        provider: str
    ) -> Optional[Dict]:
        """Find the resource data from scanned resources by identifier."""
        if not identifier_value:
            return None

        # Get the internal resource type (remove provider prefix)
        internal_type = resource_type
        if provider == "aws" and resource_type.startswith("aws_"):
            internal_type = resource_type[4:]  # Remove "aws_" prefix
        elif provider == "azure" and resource_type.startswith("azurerm_"):
            internal_type = "azure_" + resource_type[8:]
        elif provider == "gcp" and resource_type.startswith("google_"):
            internal_type = resource_type[7:]  # Remove "google_" prefix

        # Search in the resources dictionary
        for res_type, resource_list in resources.items():
            tf_type = self._get_terraform_resource_type(res_type, provider)
            if tf_type != resource_type:
                continue

            # Try to find by name_sanitized first (most reliable)
            for resource in resource_list:
                name_sanitized = resource.get("name_sanitized", "")
                if name_sanitized and (name_sanitized == identifier_value or
                                       name_sanitized.lower() == identifier_value.lower()):
                    return resource

                # Try other identifier fields
                attr_info = self.IMPORT_ID_ATTRIBUTES.get(resource_type)
                if attr_info:
                    _, scan_attr = attr_info
                    identifier = resource.get(scan_attr, "")
                    if identifier and (str(identifier) == identifier_value or
                                       str(identifier).lower() == identifier_value.lower()):
                        return resource

                # Try common fields
                for key in ["Name", "name", "Id", "id"]:
                    val = resource.get(key)
                    if val and (str(val) == identifier_value or
                                str(val).lower() == identifier_value.lower()):
                        return resource

        return None

    def _build_import_id_lookup(
        self, resources: Dict[str, List[Dict]], provider: str
    ) -> Dict[str, Dict[str, str]]:
        """Build a lookup table: resource_type -> identifier_value -> import_id"""
        lookup: Dict[str, Dict[str, str]] = {}

        for resource_type, resource_list in resources.items():
            tf_type = self._get_terraform_resource_type(resource_type, provider)
            if tf_type not in lookup:
                lookup[tf_type] = {}

            for resource in resource_list:
                # Try to get the import ID from various fields
                # First check id field (may contain remote_id value for some resources)
                import_id = resource.get("id", "")
                # For ACM certificates, the id should be CertificateArn
                if not import_id or (tf_type == "aws_acm_certificate" and not import_id.startswith("arn:")):
                    import_id = self._get_resource_id(resource, resource_type, provider)

                if not import_id:
                    continue

                # Add name_sanitized as primary lookup key - this matches the terraform resource name
                name_sanitized = resource.get("name_sanitized", "")
                if name_sanitized:
                    lookup[tf_type][name_sanitized] = import_id
                    lookup[tf_type][name_sanitized.lower()] = import_id

                # Also add other identifiers for fallback matching
                attr_info = self.IMPORT_ID_ATTRIBUTES.get(tf_type)
                if attr_info:
                    _, scan_attr = attr_info
                    identifier = resource.get(scan_attr, "")
                    if identifier:
                        lookup[tf_type][str(identifier)] = import_id
                        lookup[tf_type][str(identifier).lower()] = import_id

                # Add common identifier fields
                for key in ["Name", "name", "Id"]:
                    val = resource.get(key)
                    if val and val != import_id:
                        lookup[tf_type][str(val)] = import_id
                        lookup[tf_type][str(val).lower()] = import_id

        return lookup

    # Resources where the ID can be extracted from the resource name
    ID_FROM_RESOURCE_NAME = {
        "aws_security_group": "sg-",
        "aws_vpc": "vpc-",
        "aws_subnet": "subnet-",
        "aws_internet_gateway": "igw-",
        "aws_route_table": "rtb-",
        "aws_nat_gateway": "nat-",
        "aws_ebs_volume": "vol-",
        "aws_network_interface": "eni-",
    }

    def _extract_resources(self, content: str) -> List[Tuple[str, str, str, str]]:
        """Extract (resource_type, resource_name, identifier_value, block_content) from HCL content.

        The identifier_value is used to look up the import ID from the scan data.
        We prioritize using resource_name (name_sanitized) as it's the most reliable match.
        The block_content is returned for composite ID extraction.
        """
        results = []
        resource_pattern = re.compile(
            r'resource\s+"(?P<type>[^"]+)"\s+"(?P<name>[^"]+)"\s*\{',
            re.MULTILINE
        )

        for match in resource_pattern.finditer(content):
            resource_type = match.group("type")
            resource_name = match.group("name")

            # Find the block content to extract identifier
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

            # Primary strategy: use resource_name as identifier since it matches name_sanitized
            # This is the most reliable way to match resources across all types
            identifier = resource_name

            # For resources where ID is embedded in resource name, also extract the AWS ID
            id_prefix = self.ID_FROM_RESOURCE_NAME.get(resource_type)
            if id_prefix:
                aws_id = self._extract_id_from_resource_name(resource_name, id_prefix)
                if aws_id:
                    # Use AWS ID directly as it's the import ID for these resource types
                    identifier = aws_id

            results.append((resource_type, resource_name, identifier, block_content))

        return results

    def _extract_id_from_resource_name(self, resource_name: str, id_prefix: str) -> str:
        """Extract AWS resource ID from terraform resource name.

        Examples:
            resource_0f8a39e1b42aa274f -> sg-0f8a39e1b42aa274f
            vpc_2a863150 -> vpc-2a863150
            subnet_0e5b62425884d7cf5 -> subnet-0e5b62425884d7cf5
            resource_subnet_0e5b62425884d7cf5 -> subnet-0e5b62425884d7cf5
            igw_abc123def456 -> igw-abc123def456
        """
        name = resource_name

        # Build dynamic prefix list based on the id_prefix (e.g., "vpc-" -> "vpc_")
        resource_type_prefix = id_prefix.replace("-", "_")

        # Common prefixes to strip, in order of specificity
        prefixes_to_try = [
            f"resource_{resource_type_prefix}",  # e.g., resource_subnet_
            f"resource_",                         # e.g., resource_
            resource_type_prefix,                 # e.g., vpc_, subnet_, igw_
        ]

        # Strip the first matching prefix
        for prefix in prefixes_to_try:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break

        # Check if what remains looks like a hex ID
        # AWS IDs are typically 8-17 hex characters
        clean_name = name.replace("_", "").replace("-", "")
        if re.match(r'^[0-9a-f]{8,17}$', clean_name, re.IGNORECASE):
            return f"{id_prefix}{name.replace('_', '')}"

        return ""

    def _extract_attribute(self, block_content: str, attr_name: str) -> str:
        """Extract attribute value from HCL block content."""
        # Match: attr_name = "value" or attr_name = value
        pattern = re.compile(
            rf'^\s*{re.escape(attr_name)}\s*=\s*"?([^"\n]+)"?',
            re.MULTILINE
        )
        match = pattern.search(block_content)
        if match:
            return match.group(1).strip().strip('"')
        return ""

    def _find_import_id(
        self,
        resource_type: str,
        identifier_value: str,
        lookup: Dict[str, Dict[str, str]],
        provider: str
    ) -> str:
        """Find the import ID for a resource based on its identifier."""
        if not identifier_value:
            return ""

        type_lookup = lookup.get(resource_type, {})

        # Try exact match first
        if identifier_value in type_lookup:
            return type_lookup[identifier_value]

        # Try lowercase match
        if identifier_value.lower() in type_lookup:
            return type_lookup[identifier_value.lower()]

        # For many resources, the identifier IS the import ID
        # These are resources where the Terraform import ID matches the identifier we extract
        identifier_is_import_id = {
            # VPC resources - use AWS resource IDs directly
            "aws_vpc", "aws_subnet", "aws_security_group",
            "aws_internet_gateway", "aws_route_table", "aws_nat_gateway",
            "aws_ebs_volume", "aws_network_interface",
            # EC2
            "aws_instance",
            # GuardDuty
            "aws_guardduty_detector",
            # CloudFront - distribution ID
            "aws_cloudfront_distribution",
            "aws_cloudfront_origin_access_control",
            # ACM - uses ARN from lookup (removed from identifier_is_import_id)
            # KMS - uses key ID or alias name
            "aws_kms_key", "aws_kms_alias",
            # SNS - uses ARN
            "aws_sns_topic", "aws_sns_topic_subscription",
            # Step Functions - uses ARN
            "aws_sfn_state_machine",
            # EventBridge / CloudWatch Events - uses name
            "aws_cloudwatch_event_rule",
            # Secrets Manager
            "aws_secretsmanager_secret", "aws_secretsmanager_secret_version",
            # S3 sub-resources - use bucket name
            "aws_s3_bucket_versioning", "aws_s3_bucket_public_access_block",
            "aws_s3_bucket_lifecycle_configuration", "aws_s3_bucket_policy",
            # IAM - policy uses ARN
            "aws_iam_policy",
            # API Gateway - uses ID
            "aws_api_gateway_rest_api",
            # Lambda permission - special composite
            "aws_lambda_permission",
        }

        if resource_type in identifier_is_import_id:
            return identifier_value

        return ""

    def _get_resource_id(
        self, resource: Dict, resource_type: str, provider: str
    ) -> str:
        """Extract the cloud provider resource ID for import."""
        if provider == "aws":
            # Try resource-type-specific keys first
            resource_id_keys = {
                "aws_instance": ["InstanceId", "id"],
                "aws_vpc": ["VpcId", "id"],
                "aws_subnet": ["SubnetId", "id"],
                "aws_security_group": ["GroupId", "id"],
                "aws_internet_gateway": ["InternetGatewayId", "id"],
                "aws_route_table": ["RouteTableId", "id"],
                "aws_ebs_volume": ["VolumeId", "id"],
                "aws_network_interface": ["NetworkInterfaceId", "id"],
                "aws_lambda_function": ["FunctionName", "id"],
                "aws_iam_role": ["RoleName", "id"],
                "aws_iam_policy": ["Arn", "id"],
                "aws_s3_bucket": ["Name", "BucketName", "id"],
                "aws_dynamodb_table": ["TableName", "id"],
                "aws_acm_certificate": ["CertificateArn", "id"],
                "aws_cloudfront_distribution": ["Id", "id"],
                "aws_cloudfront_origin_access_control": ["Id", "id"],
                "aws_cloudwatch_log_group": ["logGroupName", "LogGroupName", "id"],
                "aws_cloudwatch_metric_alarm": ["AlarmName", "id"],
                "aws_kms_key": ["KeyId", "id"],
                "aws_kms_alias": ["AliasName", "id"],
                "aws_secretsmanager_secret": ["Name", "SecretArn", "id"],
                "aws_secretsmanager_secret_version": ["VersionId", "id"],
                "aws_sns_topic": ["TopicArn", "id"],
                "aws_sns_topic_subscription": ["SubscriptionArn", "id"],
                "aws_sqs_queue": ["QueueUrl", "id"],
                "aws_ecs_cluster": ["ClusterArn", "clusterName", "id"],
                "aws_ecr_repository": ["repositoryName", "id"],
                "aws_cloudtrail": ["TrailArn", "Name", "id"],
                "aws_kinesis_stream": ["StreamArn", "StreamName", "id"],
                "aws_cloudwatch_event_rule": ["Name", "RuleName", "id"],
                "aws_guardduty_detector": ["DetectorId", "id"],
                "aws_db_instance": ["DBInstanceIdentifier", "id"],
                "aws_db_subnet_group": ["DBSubnetGroupName", "id"],
                "aws_backup_vault": ["BackupVaultName", "id"],
                "aws_route53_zone": ["ZoneId", "HostedZoneId", "id"],
                "aws_sfn_state_machine": ["stateMachineArn", "id"],
                "aws_api_gateway_rest_api": ["id", "Id"],
            }

            tf_type = self._get_terraform_resource_type(resource_type, provider)
            keys_to_try = resource_id_keys.get(tf_type, ["id", "Id", "Name", "name", "Arn"])

            for key in keys_to_try:
                if resource.get(key):
                    return resource[key]
            return ""
        elif provider == "azure":
            return resource.get("id", "")
        elif provider == "gcp":
            return resource.get("selfLink") or resource.get("id", "")
        return ""

    def _get_terraform_resource_type(self, resource_type: str, provider: str) -> str:
        """Get the Terraform resource type from internal type."""
        if provider == "aws" and not resource_type.startswith("aws_"):
            return f"aws_{resource_type}"
        elif provider == "azure":
            if resource_type.startswith("azure_"):
                return resource_type.replace("azure_", "azurerm_")
        elif provider == "gcp" and not resource_type.startswith("google_"):
            return f"google_{resource_type}"
        return resource_type

    def _build_composite_import_id(
        self,
        resource_type: str,
        resource: Dict,
        block_content: str
    ) -> str:
        """Build composite import ID for resources requiring special formats.

        Args:
            resource_type: Terraform resource type (e.g., aws_api_gateway_method)
            resource: Scanned resource data
            block_content: HCL block content for extracting additional attributes

        Returns:
            Composite import ID string, or empty string if required fields missing

        Examples:
            API Gateway Method: "rest-api-id/resource-id/GET"
            API Gateway Resource: "rest-api-id/resource-id"
            API Gateway Deployment: "rest-api-id/deployment-id"
            Route53 Record: "Z1234567890ABC_example.com_A"
            Lambda Permission: "my-function/AllowAPIGateway"
        """
        composite_config = self.COMPOSITE_IMPORT_IDS.get(resource_type)
        if not composite_config:
            return ""

        format_string = composite_config["format"]
        required_fields = composite_config["fields"]

        # Collect field values from resource data and HCL block
        field_values = {}
        for field in required_fields:
            value = None

            # Special handling for API Gateway composite IDs
            if resource_type in ["aws_api_gateway_resource", "aws_api_gateway_deployment"]:
                if field == "rest_api_id":
                    # Extract rest_api_id from HCL block
                    value = self._extract_attribute(block_content, "rest_api_id")
                elif field == "resource_id":
                    # Use the 'id' field from remote_id in the import JSON
                    value = resource.get("id", "")
                    # The id should be just the resource ID part, if it's composite, extract the last part
                    if "/" in value:
                        value = value.split("/")[-1]
                elif field == "deployment_id":
                    # Use the 'id' field from remote_id in the import JSON
                    value = resource.get("id", "")
                    # The id should be just the deployment ID part, if it's composite, extract the last part
                    if "/" in value:
                        value = value.split("/")[-1]

            # Try resource data first if not already set
            if not value:
                value = resource.get(field)

            # Try extracting from HCL block if not in resource data
            if not value and block_content:
                value = self._extract_attribute(block_content, field)

            # Handle common field name variations
            if not value:
                field_variations = {
                    "rest_api_id": ["RestApiId", "restApiId", "api_id"],
                    "resource_id": ["ResourceId", "resourceId", "id"],
                    "deployment_id": ["DeploymentId", "deploymentId", "id"],
                    "http_method": ["httpMethod", "HttpMethod", "method"],
                    "zone_id": ["ZoneId", "HostedZoneId", "hosted_zone_id"],
                    "function_name": ["FunctionName", "function"],
                    "statement_id": ["StatementId", "Sid"],
                }
                for variation in field_variations.get(field, []):
                    value = resource.get(variation)
                    if value:
                        break

            if not value:
                logger.warning(
                    f"Missing required field '{field}' for composite import ID of {resource_type}"
                )
                return ""

            field_values[field] = value

        try:
            return format_string.format(**field_values)
        except KeyError as e:
            logger.error(f"Failed to format composite import ID for {resource_type}: {e}")
            return ""

    def validate_import_blocks(
        self,
        imports_content: str,
        output_dir: Path,
        validate_with_terraform: bool = False
    ) -> Tuple[bool, List[str]]:
        """Validate generated import blocks for correctness.

        Args:
            imports_content: Generated imports.tf content
            output_dir: Directory containing Terraform files
            validate_with_terraform: If True, run 'terraform validate' (requires terraform CLI)

        Returns:
            Tuple of (is_valid, list_of_errors)

        Validation checks:
        1. Syntax validation (import block structure)
        2. ID format validation (non-empty, valid characters)
        3. Module reference validation (module exists)
        4. Optional: Terraform CLI validation
        """
        errors = []

        # Parse import blocks
        import_blocks = self._parse_import_blocks(imports_content)

        if not import_blocks:
            if "import {" in imports_content:
                errors.append("Failed to parse import blocks from content")
            # Empty imports file is valid if no resources
            return True, []

        # Validate each import block
        for idx, block in enumerate(import_blocks):
            block_num = idx + 1

            # Check 'to' field
            if not block.get("to"):
                errors.append(f"Import block {block_num}: missing 'to' field")
            else:
                # Validate module reference format
                to_field = block["to"]
                if not to_field.startswith("module."):
                    errors.append(
                        f"Import block {block_num}: 'to' must reference a module (got: {to_field})"
                    )
                else:
                    # Check if module directory exists
                    module_path = to_field.split(".")[1]
                    module_dir = output_dir / "modules" / module_path.replace("-", "/")
                    if not module_dir.exists():
                        errors.append(
                            f"Import block {block_num}: module directory not found: {module_dir}"
                        )

            # Check 'id' field
            import_id = block.get("id")
            if not import_id:
                errors.append(f"Import block {block_num}: missing or empty 'id' field")
            elif len(import_id) < 3:
                errors.append(
                    f"Import block {block_num}: 'id' too short (likely invalid): {import_id}"
                )
            elif import_id.startswith("$") or import_id.startswith("var."):
                errors.append(
                    f"Import block {block_num}: 'id' contains variable reference (not supported): {import_id}"
                )

        # Optional: Terraform CLI validation
        if validate_with_terraform and not errors:
            tf_errors = self._validate_with_terraform_cli(output_dir)
            errors.extend(tf_errors)

        return len(errors) == 0, errors

    def _parse_import_blocks(self, content: str) -> List[Dict[str, str]]:
        """Parse import blocks from imports.tf content.

        Returns:
            List of dicts with 'to' and 'id' keys (may be empty if missing)
        """
        blocks = []

        # First, find all import blocks (even malformed ones)
        block_pattern = re.compile(
            r'import\s*\{([^}]*)\}',
            re.MULTILINE | re.DOTALL
        )

        for match in block_pattern.finditer(content):
            block_content = match.group(1)
            block = {"to": "", "id": ""}

            # Extract 'to' field
            to_match = re.search(r'to\s*=\s*([^\s\n]+)', block_content)
            if to_match:
                block["to"] = to_match.group(1).strip()

            # Extract 'id' field (handle both quoted and unquoted)
            id_match = re.search(r'id\s*=\s*"([^"]*)"', block_content)
            if id_match:
                block["id"] = id_match.group(1).strip()
            else:
                # Try unquoted
                id_match = re.search(r'id\s*=\s*([^\s\n]+)', block_content)
                if id_match:
                    block["id"] = id_match.group(1).strip()

            blocks.append(block)

        return blocks

    def _validate_with_terraform_cli(self, output_dir: Path) -> List[str]:
        """Run 'terraform validate' to check import blocks.

        Note: This requires terraform CLI to be installed and is optional.

        Returns:
            List of error messages (empty if validation passes)
        """
        import subprocess

        errors = []

        try:
            result = subprocess.run(
                ["terraform", "validate", "-json"],
                cwd=output_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                try:
                    import json
                    validation_result = json.loads(result.stdout)
                    if not validation_result.get("valid", False):
                        for diag in validation_result.get("diagnostics", []):
                            severity = diag.get("severity", "error")
                            summary = diag.get("summary", "Unknown error")
                            detail = diag.get("detail", "")
                            errors.append(f"[{severity}] {summary}: {detail}")
                except json.JSONDecodeError:
                    errors.append(f"Terraform validation failed: {result.stderr}")

        except FileNotFoundError:
            logger.warning("Terraform CLI not found, skipping terraform validation")
        except subprocess.TimeoutExpired:
            errors.append("Terraform validation timed out after 30 seconds")
        except Exception as e:
            logger.error(f"Error running terraform validate: {e}")
            errors.append(f"Terraform validation error: {str(e)}")

        return errors

    def generate_validation_report(
        self,
        output_dir: Path,
        imports_content: str,
        validate_with_terraform: bool = False
    ) -> str:
        """Generate a validation report for import blocks.

        Args:
            output_dir: Directory containing generated files
            imports_content: Generated imports.tf content
            validate_with_terraform: Whether to run terraform validate

        Returns:
            Markdown-formatted validation report
        """
        report_lines = []
        report_lines.append("# Import Block Validation Report")
        report_lines.append("")

        # Parse import blocks
        import_blocks = self._parse_import_blocks(imports_content)
        report_lines.append(f"## Summary")
        report_lines.append(f"- Total import blocks: {len(import_blocks)}")
        report_lines.append("")

        # Run validation
        is_valid, errors = self.validate_import_blocks(
            imports_content, output_dir, validate_with_terraform
        )

        if is_valid:
            report_lines.append("## Status: PASS")
            report_lines.append("")
            report_lines.append("All import blocks are valid.")
        else:
            report_lines.append("## Status: FAIL")
            report_lines.append("")
            report_lines.append(f"Found {len(errors)} validation error(s):")
            report_lines.append("")
            for idx, error in enumerate(errors, 1):
                report_lines.append(f"{idx}. {error}")

        report_lines.append("")
        report_lines.append("## Import Blocks")
        report_lines.append("")

        if import_blocks:
            for idx, block in enumerate(import_blocks, 1):
                report_lines.append(f"### Block {idx}")
                report_lines.append(f"- To: `{block.get('to', 'N/A')}`")
                report_lines.append(f"- ID: `{block.get('id', 'N/A')}`")
                report_lines.append("")
        else:
            report_lines.append("No import blocks found.")

        return "\n".join(report_lines)


# ---------------------------------------------------------------------------
# Module Dependencies Configuration
# ---------------------------------------------------------------------------

# Define inter-module dependencies for proper Terraform apply ordering.
# Format: module_name -> list of modules it depends on
MODULE_DEPENDENCIES: Dict[str, List[str]] = {
    # Lambda depends on IAM roles for execution
    "lambda-function": ["iam-customer-service-role", "vpc", "vpc-security-group"],

    # ECS depends on IAM, VPC, ALB
    "ecs": ["iam-customer-service-role", "vpc", "vpc-security-group", "alb"],

    # ALB depends on VPC and security groups
    "alb": ["vpc", "vpc-security-group", "acm"],

    # RDS depends on VPC, security groups, and subnet groups
    "rds": ["vpc", "vpc-security-group"],
    "rds-aurora-postgresql": ["vpc", "vpc-security-group"],

    # ElastiCache depends on VPC
    "elasticache-redis": ["vpc", "vpc-security-group"],

    # EKS depends on VPC and IAM
    "eks": ["vpc", "vpc-security-group", "iam-customer-service-role"],

    # API Gateway can depend on Lambda
    "api-gateway": ["lambda-function"],

    # CloudFront depends on S3 and ACM
    "cloudfront": ["s3-bucket", "acm"],

    # Security groups depend on VPC
    "vpc-security-group": ["vpc"],

    # VPC endpoints depend on VPC
    "vpc-endpoint-service": ["vpc", "vpc-security-group"],

    # Secrets Manager doesn't have dependencies but KMS does
    "secretsmanager-secret": ["kms-customer-key"],

    # SNS/SQS can have cross-dependencies
    "sqs-queue": ["kms-customer-key"],
    "sns": ["kms-customer-key"],

    # Route53 records may depend on ALB, CloudFront
    "route53": ["alb", "cloudfront", "api-gateway"],

    # Step Functions depend on Lambda, IAM
    "step-functions-state-machine": ["lambda-function", "iam-customer-service-role"],

    # EventBridge depends on Lambda, SNS, SQS
    "eventbridge": ["lambda-function", "sns", "sqs-queue"],

    # ASG depends on EC2 launch templates, ALB
    "asg": ["alb", "vpc", "vpc-security-group"],

    # EC2 instances depend on VPC
    "ec2-instance": ["vpc", "vpc-security-group", "iam-customer-service-role"],

    # EFS depends on VPC
    "efs": ["vpc", "vpc-security-group"],

    # OpenSearch depends on VPC
    "opensearch": ["vpc", "vpc-security-group"],

    # MSK depends on VPC
    "msk-cluster": ["vpc", "vpc-security-group"],

    # DynamoDB with KMS encryption
    "dynamodb-table": ["kms-customer-key"],

    # CloudWatch depends on Lambda for log subscriptions
    "cloudwatch-log-group": ["lambda-function"],
}


# ---------------------------------------------------------------------------
# Stack Generator
# ---------------------------------------------------------------------------

class StackGenerator:
    """
    Main stack generator orchestrator.

    Generates complete, deployment-ready Terraform stacks from scanned cloud resources.

    Note:
        This feature requires a Professional or Enterprise license.
        Use check_feature_access(Tier.PROFESSIONAL) before instantiating.
    """

    def __init__(self, provider: str):
        self.provider = provider
        self.module_generator = EnterpriseModuleGenerator(provider)
        self.environment_detector = EnvironmentDetector()
        self.import_generator = ImportBlockGenerator()
        self.module_mapping = RESOURCE_MODULE_MAP.get(provider, {})

    def generate_full_stack(
        self,
        output_dir: Path,
        scanned_resources: Dict[str, List[Dict]],
        environments: Optional[List[str]] = None,
    ) -> StackGenerationResult:
        """
        Generate complete Terraform stack.

        Args:
            output_dir: Output directory for generated files
            scanned_resources: Resources grouped by type
            environments: Optional list of environment names (auto-detect if None)

        Returns:
            StackGenerationResult with paths and metadata

        Raises:
            RuntimeError: If Professional license is not active
        """
        # Check Professional license
        if not check_feature_access(Tier.PROFESSIONAL):
            error_msg = (
                "Full stack generation requires a Professional license. "
                "Run 'terraback license activate <key>' to unlock."
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        result = StackGenerationResult(
            root_files=[],
            module_files=[],
            config_files=[],
            environments=[],
            import_blocks_generated=False,
            errors=[]
        )

        logger.info("Generating enterprise modules for %s", self.provider)

        # Generate enterprise modules
        module_files = self.module_generator.generate(output_dir)
        result.module_files = module_files

        # Detect or use provided environments
        if not environments or environments == ["auto"]:
            env_configs = self.environment_detector.detect_environments(
                scanned_resources, self.provider
            )
            result.environments = list(env_configs.keys())
            logger.info("Detected environments: %s", result.environments)
        else:
            result.environments = environments
            env_configs = self._create_env_configs(environments, scanned_resources)
            logger.info("Using provided environments: %s", result.environments)

        # Generate root main.tf with module calls
        main_tf = self._generate_main_tf(output_dir, env_configs)
        result.root_files.append(main_tf)

        # Generate root variables.tf
        variables_tf = self._generate_variables_tf(output_dir, scanned_resources, env_configs)
        result.root_files.append(variables_tf)

        # Generate root outputs.tf
        outputs_tf = self._generate_outputs_tf(output_dir, env_configs)
        result.root_files.append(outputs_tf)

        # Generate provider.tf
        generate_provider_config(output_dir, provider=self.provider)
        provider_tf = output_dir / "provider.tf"
        result.root_files.append(provider_tf)

        # Generate environment-specific tfvars if multiple environments detected
        if len(result.environments) > 1:
            logger.info("Generating environment-specific tfvars")
            config_dir = output_dir / "config"
            config_dir.mkdir(exist_ok=True)
            for env_name, env_config in env_configs.items():
                tfvars = self._generate_tfvars(config_dir, env_name, env_config)
                result.config_files.append(tfvars)

        # Generate imports.tf
        imports_tf = self._generate_imports_tf(output_dir, scanned_resources)
        result.root_files.append(imports_tf)
        result.import_blocks_generated = True

        # Clean up legacy .tf files from regular scan
        self._cleanup_legacy_tf_files(output_dir, result.root_files)

        logger.info("Enterprise module generation completed")
        return result

    def _create_env_configs(
        self, environments: List[str], resources: Dict[str, List[Dict]]
    ) -> Dict[str, EnvironmentConfig]:
        """Create environment configs for explicitly provided environments."""
        env_configs = {}
        for env_name in environments:
            env_configs[env_name] = EnvironmentConfig(
                name=env_name,
                resources=resources,
                tags={"Environment": env_name, "ManagedBy": "Terraback"},
                region=None
            )
        return env_configs

    def _cleanup_legacy_tf_files(self, output_dir: Path, root_files: List[Path]) -> None:
        """
        Remove legacy .tf files generated by regular scan that aren't part of the new stack.

        When enterprise modules is enabled, all resources are moved into modules.
        This cleans up leftover files like key_pairs.tf, elbv2_ssl_policy.tf, etc.
        """
        # Files to keep in root
        root_file_names = {f.name for f in root_files}

        # Count cleaned files for logging
        cleaned_count = 0

        # Remove any .tf file in root that we didn't just generate
        for tf_file in output_dir.glob("*.tf"):
            if tf_file.name not in root_file_names:
                logger.info(f"Removing legacy file: {tf_file.name}")
                tf_file.unlink()
                cleaned_count += 1

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} legacy .tf file(s)")

    def _generate_main_tf(
        self,
        output_dir: Path,
        env_configs: Dict[str, EnvironmentConfig],
    ) -> Path:
        """Generate root main.tf with module instantiations and dependencies."""
        main_content = []
        main_content.append("# Root Terraform configuration")
        main_content.append("# Generated by terraback\n")

        # Get unique modules used
        modules_used = self._get_modules_used(env_configs)

        # Sort modules by dependency order (dependencies first)
        sorted_modules = self._sort_modules_by_dependencies(modules_used)

        for module_name in sorted_modules:
            # Sanitize module name for Terraform (replace / with -)
            tf_module_name = module_name.replace("/", "-")
            main_content.append(f"\n# {module_name} module")
            main_content.append(f'module "{tf_module_name}" {{')
            main_content.append(f'  source = "./modules/{module_name}"')
            main_content.append('')
            main_content.append('  environment = var.environment')
            main_content.append('  tags        = var.common_tags')

            # Add depends_on if this module has dependencies that are also in use
            deps = self._get_module_dependencies(module_name, modules_used)
            if deps:
                deps_str = ", ".join(f"module.{d.replace('/', '-')}" for d in deps)
                main_content.append('')
                main_content.append(f'  depends_on = [{deps_str}]')

            main_content.append('}')

        main_tf_path = output_dir / "main.tf"
        main_tf_path.write_text("\n".join(main_content))
        return main_tf_path

    def _get_module_dependencies(
        self,
        module_name: str,
        modules_in_use: set
    ) -> List[str]:
        """Get list of dependencies for a module that are also in use."""
        all_deps = MODULE_DEPENDENCIES.get(module_name, [])
        # Only return dependencies that are actually being used in this stack
        return [dep for dep in all_deps if dep in modules_in_use]

    def _sort_modules_by_dependencies(self, modules: set) -> List[str]:
        """Sort modules so dependencies come before dependents (topological sort)."""
        # Build dependency graph
        in_degree = {m: 0 for m in modules}
        for module in modules:
            deps = self._get_module_dependencies(module, modules)
            in_degree[module] = len(deps)

        # Kahn's algorithm for topological sort
        result = []
        no_deps = [m for m in modules if in_degree[m] == 0]

        while no_deps:
            # Sort for deterministic output
            no_deps.sort()
            module = no_deps.pop(0)
            result.append(module)

            # Reduce in-degree for modules that depend on this one
            for other_module in modules:
                if module in self._get_module_dependencies(other_module, modules):
                    in_degree[other_module] -= 1
                    if in_degree[other_module] == 0:
                        no_deps.append(other_module)

        # If we couldn't sort all modules, there's a cycle - just append remaining
        remaining = [m for m in modules if m not in result]
        result.extend(sorted(remaining))

        return result

    def _generate_variables_tf(
        self,
        output_dir: Path,
        resources: Dict[str, List[Dict]],
        env_configs: Dict[str, EnvironmentConfig]
    ) -> Path:
        """Generate root variables.tf."""
        vars_content = []
        vars_content.append("# Root variables")
        vars_content.append("# Generated by terraback\n")

        # Common variables
        vars_content.append('variable "environment" {')
        vars_content.append('  description = "Environment name"')
        vars_content.append('  type        = string')
        if len(env_configs) == 1:
            env_name = list(env_configs.keys())[0]
            vars_content.append(f'  default     = "{env_name}"')
        vars_content.append('}\n')

        vars_content.append('variable "common_tags" {')
        vars_content.append('  description = "Common tags to apply to all resources"')
        vars_content.append('  type        = map(string)')
        vars_content.append('  default     = {}')
        vars_content.append('}\n')

        variables_tf_path = output_dir / "variables.tf"
        variables_tf_path.write_text("\n".join(vars_content))
        return variables_tf_path

    def _generate_outputs_tf(
        self,
        output_dir: Path,
        env_configs: Dict[str, EnvironmentConfig]
    ) -> Path:
        """Generate root outputs.tf aggregating module outputs."""
        outputs_content = []
        outputs_content.append("# Root outputs")
        outputs_content.append("# Generated by terraback\n")
        outputs_content.append("# Add module output references here as needed")

        outputs_tf_path = output_dir / "outputs.tf"
        outputs_tf_path.write_text("\n".join(outputs_content))
        return outputs_tf_path

    def _generate_tfvars(
        self,
        config_dir: Path,
        env_name: str,
        env_config: EnvironmentConfig
    ) -> Path:
        """Generate environment-specific tfvars file."""
        tfvars_content = []
        tfvars_content.append(f"# Environment: {env_name}")
        tfvars_content.append(f"# Generated by terraback\n")

        tfvars_content.append(f'environment = "{env_name}"\n')

        tfvars_content.append('common_tags = {')
        for key, value in env_config.tags.items():
            tfvars_content.append(f'  {key} = "{value}"')
        tfvars_content.append('}\n')

        tfvars_path = config_dir / f"{env_name}.tfvars"
        tfvars_path.write_text("\n".join(tfvars_content))
        return tfvars_path

    def _generate_imports_tf(
        self,
        output_dir: Path,
        resources: Dict[str, List[Dict]]
    ) -> Path:
        """Generate imports.tf by reading actual resource names from module files."""
        # Use the new method that reads from module files for accurate naming
        imports_content = self.import_generator.generate_imports_from_modules(
            output_dir, resources, self.module_mapping, self.provider
        )

        imports_tf_path = output_dir / "imports.tf"
        imports_tf_path.write_text(imports_content)
        return imports_tf_path

    def _get_modules_used(self, env_configs: Dict[str, EnvironmentConfig]) -> set:
        """Get set of module names used across all environments."""
        modules = set()
        for env_config in env_configs.values():
            for resource_type in env_config.resources.keys():
                mapping = self.module_mapping.get(resource_type)
                if mapping:
                    module_name, _ = mapping
                    modules.add(module_name)
        return modules


__all__ = [
    "StackGenerator",
    "EnvironmentConfig",
    "StackGenerationResult",
    "EnvironmentDetector",
    "ImportBlockGenerator",
]
