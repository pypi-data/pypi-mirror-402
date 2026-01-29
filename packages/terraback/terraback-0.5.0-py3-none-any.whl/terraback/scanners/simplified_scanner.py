"""Simplified scanner focused on accuracy and speed for Terraform import."""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import boto3
import concurrent.futures
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from terraback.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ResourceSpec:
    """Specification for scanning and importing a resource."""
    # AWS API details
    service: str
    list_operation: str
    list_key: str
    id_field: str
    
    # Terraform details
    terraform_type: str
    import_id_format: str = "{id}"  # Can be customized like "{region}:{id}"
    
    # Filtering
    exclude_prefixes: List[str] = None
    
    # Template requirements
    required_fields: List[str] = None  # Fields needed for accurate templates


# Complete resource specifications for accurate Terraform generation
RESOURCE_SPECS = {
    # VPC Resources
    'aws_vpc': ResourceSpec(
        service='ec2',
        list_operation='describe_vpcs',
        list_key='Vpcs',
        id_field='VpcId',
        terraform_type='aws_vpc',
        required_fields=['CidrBlock', 'EnableDnsHostnames', 'EnableDnsSupport']
    ),
    
    'aws_subnet': ResourceSpec(
        service='ec2',
        list_operation='describe_subnets',
        list_key='Subnets',
        id_field='SubnetId',
        terraform_type='aws_subnet',
        required_fields=['VpcId', 'CidrBlock', 'AvailabilityZone']
    ),
    
    'aws_security_group': ResourceSpec(
        service='ec2',
        list_operation='describe_security_groups',
        list_key='SecurityGroups',
        id_field='GroupId',
        terraform_type='aws_security_group',
        exclude_prefixes=['default'],
        required_fields=['GroupName', 'Description', 'VpcId', 'IpPermissions', 'IpPermissionsEgress']
    ),
    
    # Compute Resources
    'aws_instance': ResourceSpec(
        service='ec2',
        list_operation='describe_instances',
        list_key='Reservations',  # Special handling needed
        id_field='InstanceId',
        terraform_type='aws_instance',
        required_fields=['InstanceType', 'ImageId', 'SubnetId', 'SecurityGroups']
    ),
    
    # S3
    'aws_s3_bucket': ResourceSpec(
        service='s3',
        list_operation='list_buckets',
        list_key='Buckets',
        id_field='Name',
        terraform_type='aws_s3_bucket',
        required_fields=['Name']
    ),
    
    # RDS
    'aws_db_instance': ResourceSpec(
        service='rds',
        list_operation='describe_db_instances',
        list_key='DBInstances',
        id_field='DBInstanceIdentifier',
        terraform_type='aws_db_instance',
        required_fields=['DBInstanceClass', 'Engine', 'AllocatedStorage']
    ),
    
    # Lambda
    'aws_lambda_function': ResourceSpec(
        service='lambda',
        list_operation='list_functions',
        list_key='Functions',
        id_field='FunctionName',
        terraform_type='aws_lambda_function',
        required_fields=['Runtime', 'Handler', 'Role']
    ),
    
    # IAM
    'aws_iam_role': ResourceSpec(
        service='iam',
        list_operation='list_roles',
        list_key='Roles',
        id_field='RoleName',
        terraform_type='aws_iam_role',
        exclude_prefixes=['AWS', '/aws-service-role/'],
        required_fields=['AssumeRolePolicyDocument']
    ),
}


class FastScanner:
    """Fast, accurate scanner for Terraform import."""
    
    def __init__(self, profile: Optional[str] = None, region: str = 'us-east-1'):
        self.session = boto3.Session(profile_name=profile, region_name=region)
        self.region = region
        self.clients = {}  # Client cache
    
    def get_client(self, service: str):
        """Get or create cached client."""
        if service not in self.clients:
            self.clients[service] = self.session.client(service)
        return self.clients[service]
    
    def scan_service(self, terraform_type: str) -> List[Dict[str, Any]]:
        """Scan a specific resource type for import."""
        if terraform_type not in RESOURCE_SPECS:
            logger.error(f"Unknown resource type: {terraform_type}")
            return []
        
        spec = RESOURCE_SPECS[terraform_type]
        client = self.get_client(spec.service)
        
        # Special handling for different services
        if terraform_type == 'aws_instance':
            return self._scan_ec2_instances(client, spec)
        elif terraform_type == 'aws_s3_bucket':
            return self._scan_s3_buckets(client, spec)
        else:
            return self._scan_standard(client, spec)
    
    def _scan_standard(self, client, spec: ResourceSpec) -> List[Dict[str, Any]]:
        """Standard scanning for most resources."""
        resources = []
        
        try:
            # Use paginator if available
            if hasattr(client, 'can_paginate') and client.can_paginate(spec.list_operation):
                paginator = client.get_paginator(spec.list_operation)
                for page in paginator.paginate():
                    items = page.get(spec.list_key, [])
                    for item in items:
                        resource = self._process_resource(item, spec)
                        if resource:
                            resources.append(resource)
            else:
                # Single call
                operation = getattr(client, spec.list_operation)
                response = operation()
                items = response.get(spec.list_key, [])
                for item in items:
                    resource = self._process_resource(item, spec)
                    if resource:
                        resources.append(resource)
                        
        except Exception as e:
            logger.error(f"Error scanning {spec.terraform_type}: {e}")
        
        return resources
    
    def _scan_ec2_instances(self, client, spec: ResourceSpec) -> List[Dict[str, Any]]:
        """Special handling for EC2 instances."""
        resources = []
        
        try:
            paginator = client.get_paginator('describe_instances')
            for page in paginator.paginate():
                for reservation in page.get('Reservations', []):
                    for instance in reservation.get('Instances', []):
                        resource = self._process_resource(instance, spec)
                        if resource:
                            resources.append(resource)
        except Exception as e:
            logger.error(f"Error scanning EC2 instances: {e}")
        
        return resources
    
    def _scan_s3_buckets(self, client, spec: ResourceSpec) -> List[Dict[str, Any]]:
        """Special handling for S3 buckets - need additional details."""
        resources = []
        
        try:
            response = client.list_buckets()
            for bucket in response.get('Buckets', []):
                # Get additional bucket details for accurate template
                try:
                    bucket_name = bucket['Name']
                    
                    # Get bucket location
                    location = client.get_bucket_location(Bucket=bucket_name)
                    region = location.get('LocationConstraint') or 'us-east-1'
                    
                    # Get bucket versioning
                    versioning = client.get_bucket_versioning(Bucket=bucket_name)
                    
                    # Enrich bucket data
                    bucket['Region'] = region
                    bucket['Versioning'] = versioning.get('Status', 'Disabled')
                    
                    resource = self._process_resource(bucket, spec)
                    if resource:
                        resources.append(resource)
                        
                except Exception as e:
                    logger.warning(f"Could not get details for bucket {bucket_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error scanning S3 buckets: {e}")
        
        return resources
    
    def _process_resource(self, raw_data: Dict[str, Any], spec: ResourceSpec) -> Optional[Dict[str, Any]]:
        """Process resource for Terraform import."""
        # Extract ID
        resource_id = raw_data.get(spec.id_field)
        if not resource_id:
            return None
        
        # Apply filters
        if spec.exclude_prefixes:
            for prefix in spec.exclude_prefixes:
                if str(resource_id).startswith(prefix):
                    logger.debug(f"Filtered {spec.terraform_type}: {resource_id}")
                    return None
        
        # Build import ID
        import_id = spec.import_id_format.format(
            id=resource_id,
            region=self.region
        )
        
        # Extract required fields for template accuracy
        template_data = {}
        if spec.required_fields:
            for field in spec.required_fields:
                if field in raw_data:
                    template_data[field] = raw_data[field]
        
        # Build resource object
        resource = {
            'id': resource_id,
            'terraform_type': spec.terraform_type,
            'import_id': import_id,
            'name_sanitized': self._sanitize_name(resource_id),
            'template_data': template_data,
            'tags': self._extract_tags(raw_data),
            'raw': raw_data  # Keep raw data for template generation
        }
        
        return resource
    
    def _extract_tags(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Extract tags in a consistent format."""
        if 'Tags' in data:
            if isinstance(data['Tags'], list):
                return {tag.get('Key', ''): tag.get('Value', '') 
                       for tag in data['Tags'] if 'Key' in tag}
            return data['Tags']
        return {}
    
    def _sanitize_name(self, name: str) -> str:
        """Create valid Terraform resource name."""
        import re
        name = str(name)
        # Replace invalid characters
        name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
        # Ensure starts with letter
        if name and not name[0].isalpha():
            name = 'resource_' + name
        return name[:63]

    def scan_all(self, resource_types: List[str] = None, parallel: int = 5) -> Dict[str, List[Dict]]:
        """Scan multiple resource types in parallel."""
        if resource_types is None:
            resource_types = list(RESOURCE_SPECS.keys())
        
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
            future_to_type = {
                executor.submit(self.scan_service, rt): rt 
                for rt in resource_types
            }
            
            for future in concurrent.futures.as_completed(future_to_type):
                resource_type = future_to_type[future]
                try:
                    resources = future.result()
                    if resources:
                        results[resource_type] = resources
                        logger.info(f"Found {len(resources)} {resource_type} resources")
                except Exception as e:
                    logger.error(f"Failed to scan {resource_type}: {e}")
        
        return results


class TerraformGenerator:
    """Generate accurate Terraform configurations for import."""
    
    def __init__(self, template_dir: Path):
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def generate(self, resources: List[Dict[str, Any]], output_dir: Path) -> Tuple[Path, Path]:
        """Generate Terraform file and import commands."""
        if not resources:
            return None, None
        
        terraform_type = resources[0]['terraform_type']
        
        # Generate Terraform configuration
        tf_file = self._generate_terraform(resources, terraform_type, output_dir)
        
        # Generate import commands
        import_file = self._generate_imports(resources, output_dir)
        
        return tf_file, import_file
    
    def _generate_terraform(self, resources: List[Dict], terraform_type: str, output_dir: Path) -> Path:
        """Generate accurate Terraform configuration."""
        # Try specific template first
        template = None
        try:
            template = self.env.get_template(f"aws/{terraform_type}.tf.j2")
        except TemplateNotFound as e:
            # Fall back to generic
            logger.warning(f"Template for {terraform_type} not found: {e}. Using generic template")
            template = self.env.get_template("aws/generic_resource.tf.j2")
        
        # Ensure unique names
        seen_names = {}
        for resource in resources:
            name = resource['name_sanitized']
            if name in seen_names:
                seen_names[name] += 1
                resource['name_sanitized'] = f"{name}_{seen_names[name]}"
            else:
                seen_names[name] = 0
        
        # Render
        content = template.render(resources=resources)
        
        # Write file
        tf_file = output_dir / f"{terraform_type}.tf"
        tf_file.write_text(content)
        
        return tf_file
    
    def _generate_imports(self, resources: List[Dict], output_dir: Path) -> Path:
        """Generate import commands."""
        import_cmds = []
        
        for resource in resources:
            cmd = f"terraform import {resource['terraform_type']}.{resource['name_sanitized']} {resource['import_id']}"
            import_cmds.append(cmd)
        
        # Write import script
        import_file = output_dir / f"import_{resources[0]['terraform_type']}.sh"
        import_file.write_text('\n'.join(import_cmds))
        import_file.chmod(0o755)
        
        return import_file