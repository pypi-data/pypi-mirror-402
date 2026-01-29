"""
Resource processor to enhance resources with proper names and filtering.
This keeps the simple CLI structure while fixing naming issues.
"""
from typing import List, Dict, Any, Optional
import re

# AWS managed resource patterns to filter out
AWS_MANAGED_PATTERNS = {
    'parameter_groups': ['default.'],
    'db_parameter_groups': ['default.'],
    'documents': ['AWS-', 'Amazon-'],
    'parameters': ['/aws/'],
    'policies': ['AWS', 'arn:aws:iam::aws:policy/'],
    'security_groups': ['default'],
    'roles': ['AWS', '/aws-service-role/'],
}

# Field mappings for different resource types
RESOURCE_ID_FIELDS = {
    # EC2
    'instances': 'InstanceId',
    'volumes': 'VolumeId',
    'snapshots': 'SnapshotId',
    'amis': 'ImageId',
    'security_groups': 'GroupId',
    'vpcs': 'VpcId',
    'subnets': 'SubnetId',
    'internet_gateways': 'InternetGatewayId',
    'nat_gateways': 'NatGatewayId',
    'route_tables': 'RouteTableId',
    'network_interfaces': 'NetworkInterfaceId',
    'key_pairs': 'KeyName',
    'launch_templates': 'LaunchTemplateName',
    
    # S3
    'buckets': 'Name',
    
    # RDS
    'db_instances': 'DBInstanceIdentifier',
    'db_parameter_groups': 'DBParameterGroupName',
    'db_subnet_groups': 'DBSubnetGroupName',
    
    # Lambda
    'functions': 'FunctionName',
    'layers': 'LayerArn',
    
    # IAM
    'roles': 'RoleName',
    'policies': 'PolicyName',
    
    # ElastiCache
    'cache_clusters': 'CacheClusterId',
    'cache_parameter_groups': 'CacheParameterGroupName',
    'replication_groups': 'ReplicationGroupId',
    'cache_subnet_groups': 'CacheSubnetGroupName',
    
    # CloudWatch
    'alarms': 'AlarmName',
    'dashboards': 'DashboardName',
    'log_groups': 'logGroupName',
    
    # Route53
    'hosted_zones': 'Id',
    'resource_record_sets': 'Name',
    
    # ECS
    'clusters': 'clusterName',
    'services': 'serviceName',
    'task_definitions': 'taskDefinitionArn',
    
    # SSM
    'documents': 'Name',
    'parameters': 'Name',
    'maintenance_windows': 'WindowId',
    
    # SNS
    'topics': 'TopicArn',
    'subscriptions': 'SubscriptionArn',
    
    # SQS
    'queues': 'QueueUrl',
    
    # Secrets Manager
    'secrets': 'Name',
    'secret_versions': 'VersionId',

    # KMS
    'keys': 'KeyId',
    'aliases': 'AliasName',

    # DynamoDB
    'tables': 'TableName',
}

def filter_aws_managed_resources(resources: List[Dict[str, Any]], resource_type: str) -> List[Dict[str, Any]]:
    """Filter out AWS-managed resources that shouldn't be imported."""
    if resource_type not in AWS_MANAGED_PATTERNS:
        return resources
    
    patterns = AWS_MANAGED_PATTERNS[resource_type]
    filtered = []
    
    # Get the ID field for this resource type
    id_field = RESOURCE_ID_FIELDS.get(resource_type, 'id')
    
    for resource in resources:
        resource_id = resource.get(id_field, '')
        
        # Check if resource matches any filter pattern
        should_filter = False
        for pattern in patterns:
            if pattern in str(resource_id):
                should_filter = True
                break
        
        if not should_filter:
            filtered.append(resource)
    
    return filtered

def enhance_resource_names(resources: List[Dict[str, Any]], resource_type: str) -> List[Dict[str, Any]]:
    """Add proper name_sanitized field to resources for Terraform generation."""
    # Get the ID field for this resource type
    id_field = RESOURCE_ID_FIELDS.get(resource_type, 'id')
    
    for resource in resources:
        # Try to find a good identifier
        resource_id = None
        
        # First try the specific ID field
        if id_field in resource:
            resource_id = resource[id_field]
        
        # Fallback to common fields
        if not resource_id:
            for field in ['Id', 'id', 'Name', 'name']:
                if field in resource:
                    resource_id = resource[field]
                    break
        
        # Handle ARNs
        if resource_id and resource_id.startswith('arn:'):
            # Extract the last part of the ARN
            resource_id = resource_id.split('/')[-1] or resource_id.split(':')[-1]
        
        # Generate sanitized name
        if resource_id:
            # Remove invalid characters for Terraform (replace dots, hyphens, and other special chars with underscores)
            sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', str(resource_id))
            # Ensure it starts with a letter
            if sanitized and not sanitized[0].isalpha():
                sanitized = f'resource_{sanitized}'
            resource['name_sanitized'] = sanitized
        else:
            # Fallback name
            resource['name_sanitized'] = f'{resource_type}_resource'
    
    return resources

def process_resources(resources: List[Dict[str, Any]], resource_type: str, include_all: bool = False) -> List[Dict[str, Any]]:
    """Process resources: filter AWS-managed ones and enhance names."""
    # Filter AWS-managed resources unless include_all is True
    if not include_all:
        resources = filter_aws_managed_resources(resources, resource_type)
    
    # Enhance resource names
    resources = enhance_resource_names(resources, resource_type)
    
    return resources