"""AWS Service ID field mappings for accurate resource identification."""

# Mapping of AWS service resources to their primary identifier field names
# This helps the generic scanner correctly extract resource IDs
AWS_ID_FIELD_MAPPINGS = {
    # ACM
    'Certificate': 'CertificateArn',
    
    # API Gateway
    'RestApi': 'id',
    'ApiKey': 'id',
    'Deployment': 'id',
    'Stage': 'stageName',
    'Resource': 'id',
    'Method': 'httpMethod',
    'Integration': 'httpMethod',
    
    # Auto Scaling
    'AutoScalingGroup': 'AutoScalingGroupName',
    'LaunchConfiguration': 'LaunchConfigurationName',
    'ScalingPolicy': 'PolicyName',
    
    # CloudFront
    'Distribution': 'Id',
    'CachePolicy': 'Id',
    'OriginAccessControl': 'Id',
    'OriginRequestPolicy': 'Id',
    
    # CloudWatch
    'MetricAlarm': 'AlarmName',
    'Dashboard': 'DashboardName',
    'LogGroup': 'logGroupName',
    
    # EC2
    'Instance': 'InstanceId',
    'Ami': 'ImageId',
    'KeyPair': 'KeyName',
    'LaunchTemplate': 'LaunchTemplateName',
    'NetworkInterface': 'NetworkInterfaceId',
    'Volume': 'VolumeId',
    'Snapshot': 'SnapshotId',
    'SecurityGroup': 'GroupId',
    'Subnet': 'SubnetId',
    'Vpc': 'VpcId',
    'InternetGateway': 'InternetGatewayId',
    'NatGateway': 'NatGatewayId',
    'RouteTable': 'RouteTableId',
    'VpcEndpoint': 'VpcEndpointId',
    'Address': 'AllocationId',
    
    # ECR
    'Repository': 'repositoryName',
    
    # ECS
    'Cluster': 'clusterArn',
    'Service': 'serviceName',
    'TaskDefinition': 'taskDefinitionArn',
    
    # EFS
    'FileSystem': 'FileSystemId',
    'AccessPoint': 'AccessPointId',
    'MountTarget': 'MountTargetId',
    
    # ElastiCache
    'CacheCluster': 'CacheClusterId',
    'ReplicationGroup': 'ReplicationGroupId',
    'CacheParameterGroup': 'CacheParameterGroupName',
    'CacheSubnetGroup': 'CacheSubnetGroupName',
    
    # ELB (Classic)
    'LoadBalancer': 'LoadBalancerName',
    
    # ELBv2
    'LoadBalancerV2': 'LoadBalancerArn',
    'TargetGroup': 'TargetGroupArn',
    'Listener': 'ListenerArn',
    'ListenerRule': 'RuleArn',
    
    # IAM
    'Role': 'RoleName',
    'Policy': 'PolicyName',
    'User': 'UserName',
    'Group': 'GroupName',
    'InstanceProfile': 'InstanceProfileName',
    
    # Lambda
    'Function': 'FunctionName',
    'LayerVersion': 'LayerVersionArn',
    
    # RDS
    'DBInstance': 'DBInstanceIdentifier',
    'DBCluster': 'DBClusterIdentifier',
    'DBParameterGroup': 'DBParameterGroupName',
    'DBSubnetGroup': 'DBSubnetGroupName',
    
    # Route53
    'HostedZone': 'Id',
    'ResourceRecordSet': 'Name',  # Combined with Type for uniqueness
    
    # S3
    'Bucket': 'Name',
    
    # Secrets Manager
    'Secret': 'Name',
    'SecretVersion': 'VersionId',
    
    # SNS
    'Topic': 'TopicArn',
    'Subscription': 'SubscriptionArn',
    
    # SQS
    'Queue': 'QueueUrl',
    
    # SSM
    'Document': 'Name',
    'Parameter': 'Name',
    'MaintenanceWindow': 'WindowId',
}

# Resources that should be filtered out (AWS-managed)
AWS_MANAGED_RESOURCE_PATTERNS = {
    'CacheParameterGroup': ['default.'],
    'DBParameterGroup': ['default.'],
    'Document': ['AWS-', 'Amazon-'],
    'Parameter': ['/aws/'],
    'Policy': ['AWS', 'arn:aws:iam::aws:policy/'],
    'SecurityGroup': ['default'],
}

def get_id_field(resource_type: str) -> str:
    """Get the ID field name for a resource type."""
    return AWS_ID_FIELD_MAPPINGS.get(resource_type, 'id')

def should_filter_resource(resource_type: str, resource_data: dict) -> bool:
    """Check if a resource should be filtered out."""
    if resource_type not in AWS_MANAGED_RESOURCE_PATTERNS:
        return False
    
    patterns = AWS_MANAGED_RESOURCE_PATTERNS[resource_type]
    id_field = get_id_field(resource_type)
    resource_id = resource_data.get(id_field, '')
    
    for pattern in patterns:
        if pattern in resource_id:
            return True
    
    return False