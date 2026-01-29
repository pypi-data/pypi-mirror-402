"""Utilities for restructuring generated Terraform into enterprise modules."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Tuple

import re

from terraback.utils.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# The configuration maps Terraform resource types to the enterprise module and
# file they should be consolidated into.  Each cloud provider has its own
# curated mapping so the generator can organise output across AWS, Azure and
# GCP consistently.  The structure is easily extensible as additional
# resources are supported.

# Resource variable configuration - maps resource types to attributes that should
# become module variables. Each entry contains:
# - attribute_name: The Terraform attribute name
# - variable_name: The corresponding variable name
# - type: Terraform variable type
# - description: Variable description
# - extract_default: Whether to extract current value as default
RESOURCE_VARIABLE_CONFIG: Dict[str, List[Dict[str, any]]] = {
    "aws_instance": [
        {"attribute": "instance_type", "variable": "instance_type", "type": "string",
         "description": "EC2 instance type", "extract_default": True},
        {"attribute": "ami", "variable": "ami", "type": "string",
         "description": "AMI ID for the instance", "extract_default": True},
        {"attribute": "subnet_id", "variable": "subnet_id", "type": "string",
         "description": "Subnet ID where instance will be launched", "extract_default": False},
        {"attribute": "key_name", "variable": "key_name", "type": "string",
         "description": "Key pair name for SSH access", "extract_default": True},
        {"attribute": "monitoring", "variable": "enable_monitoring", "type": "bool",
         "description": "Enable detailed monitoring", "extract_default": True},
    ],
    "aws_lambda_function": [
        {"attribute": "runtime", "variable": "runtime", "type": "string",
         "description": "Lambda runtime environment", "extract_default": True},
        {"attribute": "memory_size", "variable": "memory_size", "type": "number",
         "description": "Memory allocation in MB", "extract_default": True},
        {"attribute": "timeout", "variable": "timeout", "type": "number",
         "description": "Function timeout in seconds", "extract_default": True},
        {"attribute": "handler", "variable": "handler", "type": "string",
         "description": "Lambda function handler", "extract_default": True},
    ],
    "aws_vpc": [
        {"attribute": "cidr_block", "variable": "cidr_block", "type": "string",
         "description": "CIDR block for VPC", "extract_default": True},
        {"attribute": "enable_dns_support", "variable": "enable_dns_support", "type": "bool",
         "description": "Enable DNS support in VPC", "extract_default": True},
        {"attribute": "enable_dns_hostnames", "variable": "enable_dns_hostnames", "type": "bool",
         "description": "Enable DNS hostnames in VPC", "extract_default": True},
        {"attribute": "instance_tenancy", "variable": "instance_tenancy", "type": "string",
         "description": "Tenancy option for instances", "extract_default": True},
    ],
    "aws_security_group": [
        {"attribute": "vpc_id", "variable": "vpc_id", "type": "string",
         "description": "VPC ID where security group will be created", "extract_default": False},
        {"attribute": "description", "variable": "security_group_description", "type": "string",
         "description": "Security group description", "extract_default": True},
    ],
    "aws_s3_bucket": [
        {"attribute": "bucket", "variable": "bucket_name", "type": "string",
         "description": "S3 bucket name", "extract_default": True},
    ],
    "aws_rds_cluster": [
        {"attribute": "engine", "variable": "engine", "type": "string",
         "description": "Database engine type", "extract_default": True},
        {"attribute": "engine_version", "variable": "engine_version", "type": "string",
         "description": "Database engine version", "extract_default": True},
        {"attribute": "database_name", "variable": "database_name", "type": "string",
         "description": "Name of the database", "extract_default": True},
        {"attribute": "master_username", "variable": "master_username", "type": "string",
         "description": "Master username for database", "extract_default": True},
    ],
    "aws_db_instance": [
        {"attribute": "engine", "variable": "engine", "type": "string",
         "description": "Database engine type", "extract_default": True},
        {"attribute": "engine_version", "variable": "engine_version", "type": "string",
         "description": "Database engine version", "extract_default": True},
        {"attribute": "instance_class", "variable": "instance_class", "type": "string",
         "description": "RDS instance class", "extract_default": True},
        {"attribute": "allocated_storage", "variable": "allocated_storage", "type": "number",
         "description": "Allocated storage in GB", "extract_default": True},
    ],
    "aws_ecs_service": [
        {"attribute": "desired_count", "variable": "desired_count", "type": "number",
         "description": "Desired number of tasks", "extract_default": True},
        {"attribute": "cluster", "variable": "cluster_arn", "type": "string",
         "description": "ECS cluster ARN", "extract_default": False},
    ],
    "aws_eks_cluster": [
        {"attribute": "version", "variable": "kubernetes_version", "type": "string",
         "description": "Kubernetes version", "extract_default": True},
    ],
    "aws_elasticache_cluster": [
        {"attribute": "engine", "variable": "engine", "type": "string",
         "description": "Cache engine (redis/memcached)", "extract_default": True},
        {"attribute": "node_type", "variable": "node_type", "type": "string",
         "description": "Cache node type", "extract_default": True},
        {"attribute": "num_cache_nodes", "variable": "num_cache_nodes", "type": "number",
         "description": "Number of cache nodes", "extract_default": True},
    ],
    "aws_lb": [
        {"attribute": "load_balancer_type", "variable": "load_balancer_type", "type": "string",
         "description": "Type of load balancer", "extract_default": True},
        {"attribute": "internal", "variable": "internal", "type": "bool",
         "description": "Whether load balancer is internal", "extract_default": True},
    ],
    "aws_acm_certificate": [
        {"attribute": "domain_name", "variable": "domain_name", "type": "string",
         "description": "Domain name for certificate", "extract_default": True},
        {"attribute": "validation_method", "variable": "validation_method", "type": "string",
         "description": "Certificate validation method", "extract_default": True},
    ],
}

# Resource output configuration - maps resource types to attributes that should
# become module outputs
RESOURCE_OUTPUT_CONFIG: Dict[str, List[Dict[str, str]]] = {
    "aws_instance": [
        {"attribute": "id", "description": "Instance ID"},
        {"attribute": "arn", "description": "Instance ARN"},
        {"attribute": "public_ip", "description": "Public IP address"},
        {"attribute": "private_ip", "description": "Private IP address"},
        {"attribute": "public_dns", "description": "Public DNS name"},
        {"attribute": "private_dns", "description": "Private DNS name"},
    ],
    "aws_lambda_function": [
        {"attribute": "arn", "description": "Lambda function ARN"},
        {"attribute": "invoke_arn", "description": "Invocation ARN"},
        {"attribute": "function_name", "description": "Function name"},
        {"attribute": "qualified_arn", "description": "Qualified ARN with version"},
        {"attribute": "version", "description": "Latest published version"},
    ],
    "aws_vpc": [
        {"attribute": "id", "description": "VPC ID"},
        {"attribute": "arn", "description": "VPC ARN"},
        {"attribute": "cidr_block", "description": "VPC CIDR block"},
        {"attribute": "default_route_table_id", "description": "Default route table ID"},
        {"attribute": "default_security_group_id", "description": "Default security group ID"},
        {"attribute": "default_network_acl_id", "description": "Default network ACL ID"},
    ],
    "aws_subnet": [
        {"attribute": "id", "description": "Subnet ID"},
        {"attribute": "arn", "description": "Subnet ARN"},
        {"attribute": "cidr_block", "description": "Subnet CIDR block"},
        {"attribute": "availability_zone", "description": "Availability zone"},
    ],
    "aws_security_group": [
        {"attribute": "id", "description": "Security group ID"},
        {"attribute": "arn", "description": "Security group ARN"},
        {"attribute": "vpc_id", "description": "VPC ID"},
    ],
    "aws_s3_bucket": [
        {"attribute": "id", "description": "Bucket name"},
        {"attribute": "arn", "description": "Bucket ARN"},
        {"attribute": "bucket_domain_name", "description": "Bucket domain name"},
        {"attribute": "bucket_regional_domain_name", "description": "Regional domain name"},
    ],
    "aws_rds_cluster": [
        {"attribute": "id", "description": "Cluster identifier"},
        {"attribute": "arn", "description": "Cluster ARN"},
        {"attribute": "endpoint", "description": "Cluster endpoint"},
        {"attribute": "reader_endpoint", "description": "Reader endpoint"},
        {"attribute": "cluster_resource_id", "description": "Cluster resource ID"},
    ],
    "aws_db_instance": [
        {"attribute": "id", "description": "Database instance ID"},
        {"attribute": "arn", "description": "Database instance ARN"},
        {"attribute": "endpoint", "description": "Database endpoint"},
        {"attribute": "address", "description": "Database hostname"},
        {"attribute": "port", "description": "Database port"},
    ],
    "aws_ecs_cluster": [
        {"attribute": "id", "description": "Cluster ID"},
        {"attribute": "arn", "description": "Cluster ARN"},
    ],
    "aws_ecs_service": [
        {"attribute": "id", "description": "Service ID"},
        {"attribute": "name", "description": "Service name"},
        {"attribute": "cluster", "description": "Cluster ARN"},
    ],
    "aws_eks_cluster": [
        {"attribute": "id", "description": "Cluster name"},
        {"attribute": "arn", "description": "Cluster ARN"},
        {"attribute": "endpoint", "description": "Cluster endpoint"},
        {"attribute": "certificate_authority", "description": "Certificate authority data"},
    ],
    "aws_elasticache_cluster": [
        {"attribute": "id", "description": "Cluster ID"},
        {"attribute": "arn", "description": "Cluster ARN"},
        {"attribute": "cache_nodes", "description": "Cache nodes"},
        {"attribute": "configuration_endpoint", "description": "Configuration endpoint"},
    ],
    "aws_lb": [
        {"attribute": "id", "description": "Load balancer ID"},
        {"attribute": "arn", "description": "Load balancer ARN"},
        {"attribute": "dns_name", "description": "DNS name"},
        {"attribute": "zone_id", "description": "Hosted zone ID"},
    ],
    "aws_lb_target_group": [
        {"attribute": "id", "description": "Target group ID"},
        {"attribute": "arn", "description": "Target group ARN"},
    ],
    "aws_iam_role": [
        {"attribute": "id", "description": "Role name"},
        {"attribute": "arn", "description": "Role ARN"},
        {"attribute": "unique_id", "description": "Unique ID"},
    ],
    "aws_iam_policy": [
        {"attribute": "id", "description": "Policy ID"},
        {"attribute": "arn", "description": "Policy ARN"},
    ],
    "aws_kms_key": [
        {"attribute": "id", "description": "Key ID"},
        {"attribute": "arn", "description": "Key ARN"},
        {"attribute": "key_id", "description": "Key ID"},
    ],
    "aws_sns_topic": [
        {"attribute": "id", "description": "Topic ID"},
        {"attribute": "arn", "description": "Topic ARN"},
    ],
    "aws_sqs_queue": [
        {"attribute": "id", "description": "Queue URL"},
        {"attribute": "arn", "description": "Queue ARN"},
        {"attribute": "url", "description": "Queue URL"},
    ],
    "aws_dynamodb_table": [
        {"attribute": "id", "description": "Table name"},
        {"attribute": "arn", "description": "Table ARN"},
    ],
    "aws_acm_certificate": [
        {"attribute": "id", "description": "Certificate ID"},
        {"attribute": "arn", "description": "Certificate ARN"},
        {"attribute": "domain_name", "description": "Domain name"},
    ],
    "aws_route53_zone": [
        {"attribute": "zone_id", "description": "Hosted zone ID"},
        {"attribute": "name_servers", "description": "Name servers"},
    ],
    "aws_cloudfront_distribution": [
        {"attribute": "id", "description": "Distribution ID"},
        {"attribute": "arn", "description": "Distribution ARN"},
        {"attribute": "domain_name", "description": "CloudFront domain name"},
    ],
}

AWS_RESOURCE_MODULE_MAP: Dict[str, Tuple[str, str]] = {
    # Application Load Balancer components
    "aws_lb": ("alb", "lb.tf"),
    "aws_alb": ("alb", "lb.tf"),
    "aws_lb_target_group": ("alb", "lb.tf"),
    "aws_lb_target_group_attachment": ("alb", "lb.tf"),
    "aws_lb_listener": ("alb", "listeners.tf"),
    "aws_lb_listener_rule": ("alb", "listeners.tf"),
    "aws_lb_ssl_negotiation_policy": ("alb", "lb.tf"),
    "aws_globalaccelerator_accelerator": ("alb", "global-accelerator.tf"),
    "aws_globalaccelerator_listener": ("alb", "global-accelerator.tf"),
    "aws_globalaccelerator_endpoint_group": ("alb", "global-accelerator.tf"),
    "aws_wafv2_web_acl": ("alb", "packet-filter.tf"),
    "aws_wafv2_web_acl_association": ("alb", "packet-filter.tf"),

    # Auto Scaling Groups
    "aws_autoscaling_group": ("asg", "asg.tf"),
    "aws_autoscaling_policy": ("asg", "asg.tf"),
    "aws_autoscaling_schedule": ("asg", "asg.tf"),
    "aws_autoscaling_attachment": ("asg", "asg.tf"),
    "aws_launch_configuration": ("asg", "ec2-launch-template.tf"),
    "aws_launch_template": ("asg", "ec2-launch-template.tf"),

    # AWS Backup for EC2
    "aws_backup_vault": ("backup-ec2", "vault.tf"),
    "aws_backup_plan": ("backup-ec2", "plan.tf"),
    "aws_backup_selection": ("backup-ec2", "selection.tf"),

    # CloudFront
    "aws_cloudfront_distribution": ("cloudfront", "distribution.tf"),
    "aws_cloudfront_cache_policy": ("cloudfront", "cache-policies.tf"),
    "aws_cloudfront_origin_request_policy": ("cloudfront", "aws_cloudfront_origin_request.tf"),
    "aws_cloudfront_response_headers_policy": ("cloudfront", "headers-policies.tf"),
    "aws_cloudfront_origin_access_control": ("cloudfront", "origin_access_control.tf"),
    "aws_cloudfront_public_key": ("cloudfront", "public-keys.tf"),

    # CloudWatch
    "aws_cloudwatch_log_group": ("cloudwatch-log-group", "log-group.tf"),
    "aws_cloudwatch_log_stream": ("cloudwatch-log-group", "log-group.tf"),
    "aws_cloudwatch_dashboard": ("cloudwatch-dashboard", "dashboard.tf"),
    "aws_cloudwatch_metric_alarm": ("cloudwatch-metric-alarm", "metric-alarm.tf"),

    # DynamoDB
    "aws_dynamodb_table": ("dynamodb-table", "dynamodb-table.tf"),
    "aws_dynamodb_table_item": ("dynamodb-table", "dynamodb-table.tf"),

    # EC2 Instance
    "aws_instance": ("ec2-instance", "instance.tf"),
    "aws_ebs_volume": ("ec2-instance", "instance.tf"),
    "aws_volume_attachment": ("ec2-instance", "instance.tf"),
    "aws_ebs_snapshot": ("ec2-instance", "instance.tf"),
    "aws_network_interface": ("ec2-instance", "networking.tf"),
    "aws_eip": ("ec2-instance", "networking.tf"),
    "aws_eip_association": ("ec2-instance", "networking.tf"),

    # ECS Service
    "aws_ecs_cluster": ("ecs", "ecs-cluster.tf"),
    "aws_ecs_service": ("ecs", "ecs-service.tf"),
    "aws_ecs_task_definition": ("ecs", "ecs-task-definition.tf"),
    "aws_ecs_task_set": ("ecs", "ecs-task-definition.tf"),
    "aws_ecr_repository": ("ecs", "ecs-ecr.tf"),
    "aws_ecr_lifecycle_policy": ("ecs", "ecs-ecr.tf"),
    "aws_appautoscaling_target": ("ecs", "autoscaling.tf"),
    "aws_appautoscaling_policy": ("ecs", "autoscaling.tf"),
    "aws_codepipeline": ("ecs", "code-pipeline.tf"),
    "aws_codebuild_project": ("ecs", "code-pipeline.tf"),

    # ElastiCache Redis
    "aws_elasticache_cluster": ("elasticache-redis", "cluster.tf"),
    "aws_elasticache_replication_group": ("elasticache-redis", "cluster.tf"),
    "aws_elasticache_parameter_group": ("elasticache-redis", "parameters.tf"),
    "aws_elasticache_subnet_group": ("elasticache-redis", "networking.tf"),

    # IAM Roles and Policies
    "aws_iam_role": ("iam-customer-service-role", "role.tf"),
    "aws_iam_role_policy": ("iam-customer-service-role", "role.tf"),
    "aws_iam_role_policy_attachment": ("iam-customer-service-role", "managed-policies.tf"),
    "aws_iam_instance_profile": ("iam-customer-service-role", "instance-profile.tf"),
    "aws_iam_policy": ("iam-customer-policy", "policy.tf"),
    "aws_iam_user": ("iam-customer-user", "iam-user.tf"),
    "aws_iam_user_policy": ("iam-customer-user", "iam-user.tf"),
    "aws_iam_user_policy_attachment": ("iam-customer-user", "managed-policies.tf"),
    "aws_iam_access_key": ("iam-customer-user", "iam-user.tf"),

    # KMS
    "aws_kms_key": ("kms-customer-key", "keys.tf"),
    "aws_kms_alias": ("kms-customer-key", "keys.tf"),

    # Lambda
    "aws_lambda_function": ("lambda-function", "function.tf"),
    "aws_lambda_permission": ("lambda-function", "permissions.tf"),
    "aws_lambda_event_source_mapping": ("lambda-function", "function.tf"),
    "aws_lambda_alias": ("lambda-function", "function.tf"),
    "aws_lambda_layer_version": ("lambda-function", "function.tf"),

    # MSK (Managed Streaming for Kafka)
    "aws_msk_cluster": ("msk-cluster", "cluster.tf"),
    "aws_msk_configuration": ("msk-cluster", "configuration.tf"),

    # OpenSearch
    "aws_opensearch_domain": ("opensearch", "cluster.tf"),
    "aws_opensearch_domain_policy": ("opensearch", "permissions.tf"),
    "aws_elasticsearch_domain": ("opensearch", "cluster.tf"),
    "aws_elasticsearch_domain_policy": ("opensearch", "permissions.tf"),

    # RDS
    "aws_db_instance": ("rds", "rds-cluster.tf"),
    "aws_db_parameter_group": ("rds", "cluster-parameter-group.tf"),
    "aws_db_subnet_group": ("rds", "subnet-group.tf"),
    "aws_db_option_group": ("rds", "cluster-parameter-group.tf"),

    # RDS Aurora PostgreSQL
    "aws_rds_cluster": ("rds-aurora-postgresql", "cluster.tf"),
    "aws_rds_cluster_instance": ("rds-aurora-postgresql", "instances.tf"),
    "aws_rds_cluster_parameter_group": ("rds-aurora-postgresql", "parameter-groups.tf"),
    "aws_db_cluster_parameter_group": ("rds-aurora-postgresql", "parameter-groups.tf"),

    # Route53
    "aws_route53_zone": ("route53", "zones.tf"),
    "aws_route53_record": ("route53", "records.tf"),
    "aws_route53_health_check": ("route53", "health-checks.tf"),

    # EventBridge
    "aws_cloudwatch_event_rule": ("eventbridge", "rules.tf"),
    "aws_cloudwatch_event_target": ("eventbridge", "targets.tf"),
    "aws_eventbridge_rule": ("eventbridge", "rules.tf"),
    "aws_eventbridge_target": ("eventbridge", "targets.tf"),

    # SNS
    "aws_sns_topic": ("sns", "topics.tf"),
    "aws_sns_topic_subscription": ("sns", "subscriptions.tf"),
    "aws_sns_topic_policy": ("sns", "policies.tf"),

    # API Gateway
    "aws_api_gateway_rest_api": ("api-gateway", "rest-api.tf"),
    "aws_api_gateway_resource": ("api-gateway", "resources.tf"),
    "aws_api_gateway_method": ("api-gateway", "methods.tf"),
    "aws_api_gateway_integration": ("api-gateway", "integrations.tf"),
    "aws_api_gateway_deployment": ("api-gateway", "deployment.tf"),
    "aws_api_gateway_stage": ("api-gateway", "deployment.tf"),

    # S3
    "aws_s3_bucket": ("s3-bucket", "bucket.tf"),
    "aws_s3_bucket_policy": ("s3-bucket", "policy.tf"),
    "aws_s3_bucket_versioning": ("s3-bucket", "versioning.tf"),
    "aws_s3_bucket_lifecycle_configuration": ("s3-bucket", "lifecycle-configuration.tf"),
    "aws_s3_bucket_cors_configuration": ("s3-bucket", "cors.tf"),
    "aws_s3_bucket_server_side_encryption_configuration": ("s3-bucket", "encryption.tf"),
    "aws_s3_bucket_website_configuration": ("s3-bucket", "website.tf"),
    "aws_s3_bucket_public_access_block": ("s3-bucket", "bucket.tf"),
    "aws_athena_workgroup": ("s3-bucket", "athena.tf"),
    "aws_athena_database": ("s3-bucket", "athena.tf"),

    # Secrets Manager
    "aws_secretsmanager_secret": ("secretsmanager-secret", "secret.tf"),
    "aws_secretsmanager_secret_version": ("secretsmanager-secret", "secret.tf"),
    "aws_secretsmanager_secret_rotation": ("secretsmanager-secret", "rotation.tf"),
    "aws_secretsmanager_secret_policy": ("secretsmanager-secret", "policy.tf"),

    # SQS
    "aws_sqs_queue": ("sqs-queue", "sqs-queue.tf"),
    "aws_sqs_queue_policy": ("sqs-queue", "policy.tf"),

    # SSM
    "aws_ssm_document": ("ssm-document", "ssm-document.tf"),
    "aws_ssm_parameter": ("ssm-plaintext-parameter-store", "ssm-parameter-store.tf"),

    # Step Functions
    "aws_sfn_state_machine": ("step-functions-state-machine", "state-machine.tf"),
    "aws_sfn_activity": ("step-functions-state-machine", "state-machine.tf"),

    # VPC Core Resources
    "aws_vpc": ("vpc", "vpc.tf"),
    "aws_subnet": ("vpc", "subnets.tf"),
    "aws_internet_gateway": ("vpc", "internet-gateway.tf"),
    "aws_nat_gateway": ("vpc", "nat-gateway.tf"),
    "aws_route_table": ("vpc", "route-tables.tf"),
    "aws_route": ("vpc", "routes.tf"),
    "aws_route_table_association": ("vpc", "route-tables.tf"),
    "aws_network_acl": ("vpc", "network-acls.tf"),
    "aws_network_acl_rule": ("vpc", "network-acls.tf"),
    "aws_vpc_dhcp_options": ("vpc", "dhcp-options.tf"),
    "aws_vpc_dhcp_options_association": ("vpc", "dhcp-options.tf"),
    "aws_vpc_peering_connection": ("vpc", "peering.tf"),
    "aws_vpc_peering_connection_accepter": ("vpc", "peering.tf"),

    # VPC Security Groups
    "aws_security_group": ("vpc-security-group", "security-group.tf"),
    "aws_security_group_rule": ("vpc-security-group", "rules.tf"),

    # VPC Endpoints
    "aws_vpc_endpoint": ("vpc-endpoint-service", "vpc-endpoint-service.tf"),
    "aws_vpc_endpoint_service": ("vpc-endpoint-service", "vpc-endpoint-service.tf"),

    # OpsWorks
    "aws_opsworks_stack": ("opsworks", "stack.tf"),
    "aws_opsworks_custom_layer": ("opsworks", "layer.tf"),
    "aws_opsworks_application": ("opsworks", "instance.tf"),
    "aws_opsworks_instance": ("opsworks", "instance.tf"),
    "aws_opsworks_user_profile": ("opsworks", "iam.tf"),
    "aws_opsworks_permission": ("opsworks", "iam.tf"),
    "aws_opsworks_rds_db_instance": ("opsworks", "data.tf"),

    # IAM Identity Center (AWS SSO)
    "aws_identitystore_user": ("iam-identity-center", "main.tf"),
    "aws_identitystore_group": ("iam-identity-center", "main.tf"),
    "aws_identitystore_group_membership": ("iam-identity-center", "main.tf"),
    "aws_ssoadmin_permission_set": ("iam-identity-center", "main.tf"),
    "aws_ssoadmin_account_assignment": ("iam-identity-center", "main.tf"),
    "aws_ssoadmin_managed_policy_attachment": ("iam-identity-center", "main.tf"),

    # Additional CloudWatch resources
    "aws_cloudwatch_log_subscription_filter": ("cloudwatch-log-group", "log-group.tf"),
    "aws_cloudwatch_log_metric_filter": ("cloudwatch-log-group", "log-group.tf"),
    "aws_cloudwatch_event_bus": ("eventbridge", "event-bus.tf"),

    # ACM (Certificate Manager)
    "aws_acm_certificate": ("acm", "certificates.tf"),
    "aws_acm_certificate_validation": ("acm", "certificates.tf"),

    # WAF (separate from WAFv2)
    "aws_waf_web_acl": ("waf", "web-acl.tf"),
    "aws_waf_rule": ("waf", "rules.tf"),
    "aws_waf_rule_group": ("waf", "rule-groups.tf"),
    "aws_waf_ipset": ("waf", "ipsets.tf"),

    # Config
    "aws_config_configuration_recorder": ("config", "recorder.tf"),
    "aws_config_delivery_channel": ("config", "delivery.tf"),
    "aws_config_config_rule": ("config", "rules.tf"),

    # Transfer Family
    "aws_transfer_server": ("transfer", "server.tf"),
    "aws_transfer_user": ("transfer", "users.tf"),
    "aws_transfer_ssh_key": ("transfer", "users.tf"),

    # EFS (Elastic File System)
    "aws_efs_file_system": ("efs", "file-system.tf"),
    "aws_efs_mount_target": ("efs", "mount-targets.tf"),
    "aws_efs_access_point": ("efs", "access-points.tf"),
    "aws_efs_backup_policy": ("efs", "backup.tf"),

    # EKS (Elastic Kubernetes Service)
    "aws_eks_cluster": ("eks", "cluster.tf"),
    "aws_eks_node_group": ("eks", "node-groups.tf"),
    "aws_eks_fargate_profile": ("eks", "fargate-profiles.tf"),
    "aws_eks_addon": ("eks", "addons.tf"),

    # Kinesis
    "aws_kinesis_stream": ("kinesis", "streams.tf"),
    "aws_kinesis_firehose_delivery_stream": ("kinesis", "firehose.tf"),

    # CloudTrail
    "aws_cloudtrail": ("cloudtrail", "trail.tf"),

    # GuardDuty
    "aws_guardduty_detector": ("guardduty", "detector.tf"),
    "aws_guardduty_filter": ("guardduty", "filters.tf"),

    # Organizations
    "aws_organizations_organization": ("organizations", "organization.tf"),
    "aws_organizations_account": ("organizations", "accounts.tf"),
    "aws_organizations_organizational_unit": ("organizations", "organizational-units.tf"),
    "aws_organizations_policy": ("organizations", "policies.tf"),

    # Elastic Beanstalk
    "aws_elastic_beanstalk_application": ("elastic-beanstalk", "application.tf"),
    "aws_elastic_beanstalk_environment": ("elastic-beanstalk", "environment.tf"),
    "aws_elastic_beanstalk_configuration_template": ("elastic-beanstalk", "configuration.tf"),

    # Batch
    "aws_batch_compute_environment": ("batch", "compute-environment.tf"),
    "aws_batch_job_queue": ("batch", "job-queue.tf"),
    "aws_batch_job_definition": ("batch", "job-definition.tf"),

    # Glue
    "aws_glue_catalog_database": ("glue", "catalog.tf"),
    "aws_glue_catalog_table": ("glue", "catalog.tf"),
    "aws_glue_crawler": ("glue", "crawler.tf"),
    "aws_glue_job": ("glue", "jobs.tf"),

    # Athena additional resources
    "aws_athena_named_query": ("s3-bucket", "athena.tf"),

    # DMS (Database Migration Service)
    "aws_dms_replication_instance": ("dms", "replication-instance.tf"),
    "aws_dms_endpoint": ("dms", "endpoints.tf"),
    "aws_dms_replication_task": ("dms", "replication-task.tf"),

    # DataSync
    "aws_datasync_location_s3": ("datasync", "locations.tf"),
    "aws_datasync_location_efs": ("datasync", "locations.tf"),
    "aws_datasync_task": ("datasync", "tasks.tf"),

    # Redshift
    "aws_redshift_cluster": ("redshift", "cluster.tf"),
    "aws_redshift_subnet_group": ("redshift", "subnet-group.tf"),
    "aws_redshift_parameter_group": ("redshift", "parameter-group.tf"),

    # Neptune
    "aws_neptune_cluster": ("neptune", "cluster.tf"),
    "aws_neptune_cluster_instance": ("neptune", "instances.tf"),
    "aws_neptune_cluster_parameter_group": ("neptune", "parameter-groups.tf"),

    # DocumentDB
    "aws_docdb_cluster": ("documentdb", "cluster.tf"),
    "aws_docdb_cluster_instance": ("documentdb", "instances.tf"),
    "aws_docdb_cluster_parameter_group": ("documentdb", "parameter-groups.tf"),

    # App Runner
    "aws_apprunner_service": ("apprunner", "service.tf"),
    "aws_apprunner_vpc_connector": ("apprunner", "vpc-connector.tf"),

    # Lightsail
    "aws_lightsail_instance": ("lightsail", "instance.tf"),
    "aws_lightsail_database": ("lightsail", "database.tf"),

    # CloudMap (Service Discovery)
    "aws_service_discovery_private_dns_namespace": ("cloudmap", "namespace.tf"),
    "aws_service_discovery_service": ("cloudmap", "service.tf"),

    # MediaLive
    "aws_medialive_channel": ("medialive", "channel.tf"),
    "aws_medialive_input": ("medialive", "input.tf"),

    # MediaPackage
    "aws_media_package_channel": ("mediapackage", "channel.tf"),

    # Amplify
    "aws_amplify_app": ("amplify", "app.tf"),
    "aws_amplify_branch": ("amplify", "branch.tf"),
}


AZURE_RESOURCE_MODULE_MAP: Dict[str, Tuple[str, str]] = {
    # Virtual machine compute resources
    "azurerm_linux_virtual_machine": ("compute/virtual-machine", "vm.tf"),
    "azurerm_windows_virtual_machine": ("compute/virtual-machine", "vm.tf"),
    "azurerm_virtual_machine": ("compute/virtual-machine", "vm.tf"),
    "azurerm_managed_disk": ("compute/virtual-machine", "disks.tf"),
    "azurerm_virtual_machine_data_disk_attachment": ("compute/virtual-machine", "disks.tf"),
    "azurerm_availability_set": ("compute/virtual-machine", "availability.tf"),
    "azurerm_virtual_machine_scale_set": ("compute/vmss", "vmss.tf"),
    "azurerm_linux_virtual_machine_scale_set": ("compute/vmss", "vmss.tf"),
    "azurerm_windows_virtual_machine_scale_set": ("compute/vmss", "vmss.tf"),

    # Networking primitives
    "azurerm_virtual_network": ("networking/vnet", "virtual-network.tf"),
    "azurerm_subnet": ("networking/vnet", "subnets.tf"),
    "azurerm_subnet_network_security_group_association": ("networking/vnet", "subnets.tf"),
    "azurerm_public_ip": ("networking/public-ip", "public-ip.tf"),
    "azurerm_network_interface": ("networking/network-interface", "nic.tf"),
    "azurerm_network_interface_security_group_association": ("networking/network-interface", "nic.tf"),
    "azurerm_network_security_group": ("security/network-security-group", "nsg.tf"),
    "azurerm_network_security_rule": ("security/network-security-group", "rules.tf"),
    "azurerm_nat_gateway": ("networking/nat-gateway", "nat-gateway.tf"),
    "azurerm_nat_gateway_public_ip_association": ("networking/nat-gateway", "nat-gateway.tf"),
    "azurerm_route_table": ("networking/route-table", "route-table.tf"),
    "azurerm_route": ("networking/route-table", "routes.tf"),

    # Load balancing and application gateways
    "azurerm_lb": ("networking/load-balancer", "lb.tf"),
    "azurerm_lb_backend_address_pool": ("networking/load-balancer", "backend.tf"),
    "azurerm_lb_rule": ("networking/load-balancer", "rules.tf"),
    "azurerm_lb_probe": ("networking/load-balancer", "probes.tf"),
    "azurerm_lb_nat_rule": ("networking/load-balancer", "nat-rules.tf"),
    "azurerm_application_gateway": ("networking/application-gateway", "application-gateway.tf"),
    "azurerm_application_gateway_backend_address_pool": ("networking/application-gateway", "backend.tf"),
    "azurerm_web_application_firewall_policy": ("networking/application-gateway", "waf.tf"),

    # Container services
    "azurerm_kubernetes_cluster": ("container/aks", "cluster.tf"),
    "azurerm_kubernetes_cluster_node_pool": ("container/aks", "node-pools.tf"),
    "azurerm_container_registry": ("container/acr", "registry.tf"),
    "azurerm_container_group": ("container/aci", "container-instances.tf"),

    # Database services
    "azurerm_mssql_server": ("database/sql", "server.tf"),
    "azurerm_mssql_database": ("database/sql", "databases.tf"),
    "azurerm_mssql_firewall_rule": ("database/sql", "firewall.tf"),
    "azurerm_postgresql_server": ("database/postgresql", "server.tf"),
    "azurerm_postgresql_database": ("database/postgresql", "databases.tf"),
    "azurerm_mysql_server": ("database/mysql", "server.tf"),
    "azurerm_mysql_database": ("database/mysql", "databases.tf"),
    "azurerm_cosmosdb_account": ("database/cosmosdb", "account.tf"),
    "azurerm_cosmosdb_sql_database": ("database/cosmosdb", "databases.tf"),

    # App Services
    "azurerm_app_service_plan": ("app-services/plan", "plan.tf"),
    "azurerm_app_service": ("app-services/web-app", "app.tf"),
    "azurerm_function_app": ("app-services/function-app", "function.tf"),
    "azurerm_service_plan": ("app-services/plan", "plan.tf"),
    "azurerm_linux_web_app": ("app-services/web-app", "app.tf"),
    "azurerm_windows_web_app": ("app-services/web-app", "app.tf"),
    "azurerm_linux_function_app": ("app-services/function-app", "function.tf"),
    "azurerm_windows_function_app": ("app-services/function-app", "function.tf"),

    # Monitoring and diagnostics
    "azurerm_monitor_metric_alert": ("monitoring/alerts", "metric-alerts.tf"),
    "azurerm_monitor_activity_log_alert": ("monitoring/alerts", "activity-alerts.tf"),
    "azurerm_monitor_action_group": ("monitoring/alerts", "action-groups.tf"),
    "azurerm_log_analytics_workspace": ("monitoring/logging", "log-analytics.tf"),
    "azurerm_application_insights": ("monitoring/insights", "app-insights.tf"),
    "azurerm_monitor_diagnostic_setting": ("monitoring/diagnostics", "diagnostics.tf"),

    # DNS
    "azurerm_dns_zone": ("dns", "zones.tf"),
    "azurerm_dns_a_record": ("dns", "records.tf"),
    "azurerm_dns_cname_record": ("dns", "records.tf"),
    "azurerm_private_dns_zone": ("dns/private", "zones.tf"),
    "azurerm_private_dns_a_record": ("dns/private", "records.tf"),

    # Data and secrets
    "azurerm_storage_account": ("storage/account", "storage-account.tf"),
    "azurerm_storage_container": ("storage/account", "containers.tf"),
    "azurerm_storage_blob": ("storage/account", "blobs.tf"),
    "azurerm_storage_share": ("storage/account", "file-shares.tf"),
    "azurerm_key_vault": ("security/key-vault", "key-vault.tf"),
    "azurerm_key_vault_secret": ("security/key-vault", "secrets.tf"),
    "azurerm_key_vault_key": ("security/key-vault", "keys.tf"),
    "azurerm_key_vault_certificate": ("security/key-vault", "certificates.tf"),

    # Identity and access
    "azurerm_user_assigned_identity": ("identity/managed-identity", "identity.tf"),
    "azurerm_role_assignment": ("identity/rbac", "assignments.tf"),
    "azurerm_role_definition": ("identity/rbac", "definitions.tf"),

    # Messaging
    "azurerm_servicebus_namespace": ("messaging/servicebus", "namespace.tf"),
    "azurerm_servicebus_queue": ("messaging/servicebus", "queues.tf"),
    "azurerm_servicebus_topic": ("messaging/servicebus", "topics.tf"),
    "azurerm_servicebus_subscription": ("messaging/servicebus", "subscriptions.tf"),
    "azurerm_eventhub_namespace": ("messaging/eventhub", "namespace.tf"),
    "azurerm_eventhub": ("messaging/eventhub", "eventhub.tf"),
}


GCP_RESOURCE_MODULE_MAP: Dict[str, Tuple[str, str]] = {
    # Compute instances and templates
    "google_compute_instance": ("compute/instances", "instances.tf"),
    "google_compute_instance_template": ("compute/instance-templates", "templates.tf"),
    "google_compute_instance_group": ("compute/instance-groups", "instance-groups.tf"),
    "google_compute_instance_group_manager": ("compute/instance-groups", "managers.tf"),
    "google_compute_region_instance_group_manager": ("compute/instance-groups", "managers.tf"),
    "google_compute_autoscaler": ("compute/autoscaling", "autoscaler.tf"),
    "google_compute_region_autoscaler": ("compute/autoscaling", "autoscaler.tf"),
    "google_compute_disk": ("compute/disks", "disks.tf"),
    "google_compute_snapshot": ("compute/disks", "snapshots.tf"),
    "google_compute_image": ("compute/images", "images.tf"),

    # Core networking
    "google_compute_network": ("networking/vpc", "network.tf"),
    "google_compute_subnetwork": ("networking/vpc", "subnets.tf"),
    "google_compute_firewall": ("networking/firewall", "firewall.tf"),
    "google_compute_router": ("networking/router", "router.tf"),
    "google_compute_router_nat": ("networking/router", "nat.tf"),
    "google_compute_route": ("networking/routes", "routes.tf"),
    "google_compute_address": ("networking/addresses", "addresses.tf"),
    "google_compute_global_address": ("networking/addresses", "global-addresses.tf"),

    # Load balancing components
    "google_compute_backend_service": ("networking/load-balancing", "backend.tf"),
    "google_compute_region_backend_service": ("networking/load-balancing", "backend.tf"),
    "google_compute_url_map": ("networking/load-balancing", "url-maps.tf"),
    "google_compute_target_http_proxy": ("networking/load-balancing", "proxies.tf"),
    "google_compute_target_https_proxy": ("networking/load-balancing", "proxies.tf"),
    "google_compute_target_tcp_proxy": ("networking/load-balancing", "proxies.tf"),
    "google_compute_target_ssl_proxy": ("networking/load-balancing", "proxies.tf"),
    "google_compute_forwarding_rule": ("networking/load-balancing", "forwarding-rules.tf"),
    "google_compute_global_forwarding_rule": ("networking/load-balancing", "forwarding-rules.tf"),
    "google_compute_health_check": ("networking/load-balancing", "health-checks.tf"),
    "google_compute_http_health_check": ("networking/load-balancing", "health-checks.tf"),
    "google_compute_https_health_check": ("networking/load-balancing", "health-checks.tf"),
    "google_compute_ssl_certificate": ("networking/load-balancing", "certificates.tf"),

    # GKE (Kubernetes)
    "google_container_cluster": ("container/gke", "cluster.tf"),
    "google_container_node_pool": ("container/gke", "node-pools.tf"),
    "google_container_registry": ("container/registry", "registry.tf"),

    # Cloud Functions
    "google_cloudfunctions_function": ("serverless/functions", "functions.tf"),
    "google_cloudfunctions2_function": ("serverless/functions", "functions-v2.tf"),

    # Cloud Run
    "google_cloud_run_service": ("serverless/cloud-run", "service.tf"),
    "google_cloud_run_domain_mapping": ("serverless/cloud-run", "domains.tf"),

    # DNS
    "google_dns_managed_zone": ("dns", "zones.tf"),
    "google_dns_record_set": ("dns", "records.tf"),

    # Storage
    "google_storage_bucket": ("storage/buckets", "buckets.tf"),
    "google_storage_bucket_iam_binding": ("storage/buckets", "iam.tf"),
    "google_storage_bucket_iam_member": ("storage/buckets", "iam.tf"),
    "google_filestore_instance": ("storage/filestore", "instances.tf"),

    # Caching (Memorystore)
    "google_redis_instance": ("caching/memorystore-redis", "redis.tf"),
    "google_memcache_instance": ("caching/memorystore-memcached", "memcached.tf"),

    # Databases
    "google_sql_database_instance": ("database/cloud-sql", "instances.tf"),
    "google_sql_database": ("database/cloud-sql", "databases.tf"),
    "google_sql_user": ("database/cloud-sql", "users.tf"),
    "google_spanner_instance": ("database/spanner", "instances.tf"),
    "google_spanner_database": ("database/spanner", "databases.tf"),
    "google_bigtable_instance": ("database/bigtable", "instances.tf"),
    "google_bigtable_table": ("database/bigtable", "tables.tf"),
    "google_firestore_database": ("database/firestore", "databases.tf"),

    # Messaging
    "google_pubsub_topic": ("messaging/pubsub", "topics.tf"),
    "google_pubsub_subscription": ("messaging/pubsub", "subscriptions.tf"),
    "google_pubsub_schema": ("messaging/pubsub", "schemas.tf"),
    "google_cloud_tasks_queue": ("messaging/cloud-tasks", "queues.tf"),

    # API Gateway
    "google_api_gateway_api": ("api-gateway", "api.tf"),
    "google_api_gateway_api_config": ("api-gateway", "config.tf"),
    "google_api_gateway_gateway": ("api-gateway", "gateway.tf"),

    # Eventarc
    "google_eventarc_trigger": ("integration/eventarc", "triggers.tf"),

    # Workflows
    "google_workflows_workflow": ("integration/workflows", "workflows.tf"),

    # IAM
    "google_service_account": ("iam/service-accounts", "accounts.tf"),
    "google_service_account_key": ("iam/service-accounts", "keys.tf"),
    "google_project_iam_binding": ("iam/project", "bindings.tf"),
    "google_project_iam_member": ("iam/project", "members.tf"),

    # Secret Manager
    "google_secret_manager_secret": ("security/secrets", "secrets.tf"),
    "google_secret_manager_secret_version": ("security/secrets", "versions.tf"),

    # KMS
    "google_kms_key_ring": ("security/kms", "key-rings.tf"),
    "google_kms_crypto_key": ("security/kms", "keys.tf"),

    # Certificate Manager
    "google_certificate_manager_certificate": ("security/certificate-manager", "certificates.tf"),

    # Private CA
    "google_privateca_certificate_authority": ("security/private-ca", "certificate-authority.tf"),

    # Binary Authorization
    "google_binary_authorization_policy": ("security/binary-authorization", "policy.tf"),

    # Monitoring
    "google_monitoring_alert_policy": ("monitoring", "alerts.tf"),
    "google_monitoring_notification_channel": ("monitoring", "notifications.tf"),
    "google_monitoring_uptime_check_config": ("monitoring", "uptime-checks.tf"),

    # Logging
    "google_logging_project_sink": ("logging", "sinks.tf"),
    "google_logging_metric": ("logging", "metrics.tf"),

    # Deployment Manager
    "google_deployment_manager_deployment": ("management/deployment-manager", "deployments.tf"),
}


RESOURCE_MODULE_MAP: Dict[str, Dict[str, Tuple[str, str]]] = {
    "aws": AWS_RESOURCE_MODULE_MAP,
    "azure": AZURE_RESOURCE_MODULE_MAP,
    "gcp": GCP_RESOURCE_MODULE_MAP,
}


# ---------------------------------------------------------------------------
# Data classes and helpers
# ---------------------------------------------------------------------------

_RESOURCE_PATTERN = re.compile(r"resource\s+\"(?P<type>[^\"]+)\"\s+\"(?P<name>[^\"]+)\"\s*\{")


@dataclass
class ResourceBlock:
    """A parsed Terraform ``resource`` block."""

    resource_type: str
    name: str
    start: int
    end: int
    body: str


def _iter_resource_blocks(content: str) -> Iterator[ResourceBlock]:
    """Yield ``ResourceBlock`` objects for each Terraform resource in content."""

    for match in _RESOURCE_PATTERN.finditer(content):
        start = match.start()
        brace_depth = 1
        index = match.end()

        while index < len(content) and brace_depth > 0:
            char = content[index]
            if char == "{":
                brace_depth += 1
            elif char == "}":
                brace_depth -= 1
            index += 1

        # Include trailing newline to keep formatting tidy when blocks are moved
        end = index
        yield ResourceBlock(
            resource_type=match.group("type"),
            name=match.group("name"),
            start=start,
            end=end,
            body=content[start:end].rstrip(),
        )


def _append_to_module_file(path: Path, block: ResourceBlock) -> None:
    """Append a Terraform block to the given module file with separation.

    Checks for duplicate resources (same type and name) before appending.
    Skips appending if the resource already exists in the destination file.
    """

    if path.exists():
        existing = path.read_text()
        if existing.strip():
            # Check if this resource already exists in the file
            for existing_block in _iter_resource_blocks(existing):
                if (existing_block.resource_type == block.resource_type and
                    existing_block.name == block.name):
                    logger.debug(
                        "Skipping duplicate resource: %s.%s already exists in %s",
                        block.resource_type,
                        block.name,
                        path
                    )
                    return

            path.write_text(existing.rstrip() + "\n\n" + block.body.rstrip() + "\n")
            return

    path.write_text(block.body.rstrip() + "\n")


def _is_only_comments_or_whitespace(content: str) -> bool:
    """Check if content only contains comments, whitespace, or is empty.

    Returns True if the content has no actual Terraform blocks (resource, data,
    variable, output, etc.) and only contains comments and/or whitespace.
    """
    lines = content.split('\n')
    for line in lines:
        stripped = line.strip()
        # Skip empty lines and comment lines
        if not stripped or stripped.startswith('#'):
            continue
        # If we find any non-comment, non-whitespace content, return False
        return False
    # All lines were either empty or comments
    return True


def _extract_attribute_value(resource_body: str, attribute: str) -> str | None:
    """Extract the value of a simple attribute from a resource block body.

    Handles simple assignments like:
        attribute = "value"
        attribute = 123
        attribute = true

    Does not handle complex nested blocks or lists.
    """
    pattern = rf'^\s*{re.escape(attribute)}\s*=\s*(.+?)$'
    for line in resource_body.split('\n'):
        match = re.match(pattern, line.strip())
        if match:
            value = match.group(1).strip()
            # Remove trailing comments
            if '#' in value:
                value = value.split('#')[0].strip()
            # Remove trailing commas
            value = value.rstrip(',').strip()
            return value
    return None


def _format_variable_default(value: str, var_type: str) -> str:
    """Format a value as a Terraform variable default.

    Args:
        value: The extracted value (may include quotes)
        var_type: The Terraform type (string, number, bool, etc.)

    Returns:
        Properly formatted default value for the variable block
    """
    if not value:
        return None

    value = value.strip()

    # For strings, keep quotes
    if var_type == "string":
        if not (value.startswith('"') and value.endswith('"')):
            return f'"{value}"'
        return value

    # For numbers, remove quotes if present
    elif var_type == "number":
        return value.strip('"')

    # For booleans, convert to lowercase
    elif var_type == "bool":
        value_lower = value.strip('"').lower()
        if value_lower in ("true", "false"):
            return value_lower
        return None

    return value


def _generate_variables_content(
    module_dir: Path,
    resource_types: set[str]
) -> str:
    """Generate variables.tf content based on resources in the module.

    Args:
        module_dir: Path to the module directory
        resource_types: Set of resource types found in this module

    Returns:
        String content for variables.tf file
    """
    lines = [
        "# Module variables",
        "# Auto-generated based on resources in this module",
        "",
    ]

    # Always include common variables
    lines.extend([
        'variable "tags" {',
        '  description = "Common tags to apply to all resources"',
        '  type        = map(string)',
        '  default     = {}',
        '}',
        '',
        'variable "environment" {',
        '  description = "Environment name (e.g., dev, staging, prod)"',
        '  type        = string',
        '  default     = "dev"',
        '}',
        '',
    ])

    # Collect all variables from configured resource types
    variables_added = set()

    for resource_type in sorted(resource_types):
        var_config = RESOURCE_VARIABLE_CONFIG.get(resource_type, [])
        if not var_config:
            continue

        # Read all .tf files in the module to extract values
        resource_blocks = []
        for tf_file in module_dir.glob("*.tf"):
            if tf_file.name in ("variables.tf", "outputs.tf", "locals.tf"):
                continue
            content = tf_file.read_text()
            resource_blocks.extend(list(_iter_resource_blocks(content)))

        # Filter to this resource type
        type_blocks = [b for b in resource_blocks if b.resource_type == resource_type]

        for var_def in var_config:
            var_name = var_def["variable"]

            # Skip if already added (avoid duplicates)
            if var_name in variables_added:
                continue

            variables_added.add(var_name)

            # Try to extract a default value from first matching resource
            default_value = None
            if var_def.get("extract_default") and type_blocks:
                for block in type_blocks:
                    extracted = _extract_attribute_value(block.body, var_def["attribute"])
                    if extracted:
                        default_value = _format_variable_default(extracted, var_def["type"])
                        break

            # Generate variable block
            lines.append(f'variable "{var_name}" {{')
            lines.append(f'  description = "{var_def["description"]}"')
            lines.append(f'  type        = {var_def["type"]}')

            if default_value:
                lines.append(f'  default     = {default_value}')

            lines.append('}')
            lines.append('')

    return '\n'.join(lines)


def _generate_outputs_content(
    module_dir: Path,
    resource_types: set[str]
) -> str:
    """Generate outputs.tf content based on resources in the module.

    Args:
        module_dir: Path to the module directory
        resource_types: Set of resource types found in this module

    Returns:
        String content for outputs.tf file
    """
    lines = [
        "# Module outputs",
        "# Auto-generated based on resources in this module",
        "",
    ]

    # Collect all resources from the module
    resource_blocks = []
    for tf_file in module_dir.glob("*.tf"):
        if tf_file.name in ("variables.tf", "outputs.tf", "locals.tf"):
            continue
        content = tf_file.read_text()
        resource_blocks.extend(list(_iter_resource_blocks(content)))

    # Group by resource type
    resources_by_type: Dict[str, List[ResourceBlock]] = {}
    for block in resource_blocks:
        if block.resource_type not in resources_by_type:
            resources_by_type[block.resource_type] = []
        resources_by_type[block.resource_type].append(block)

    # Generate outputs for each resource
    for resource_type in sorted(resources_by_type.keys()):
        output_config = RESOURCE_OUTPUT_CONFIG.get(resource_type, [])
        if not output_config:
            continue

        blocks = resources_by_type[resource_type]

        # If only one resource of this type, create simple outputs
        if len(blocks) == 1:
            block = blocks[0]
            resource_ref = f"{resource_type}.{block.name}"

            for output_def in output_config:
                attr = output_def["attribute"]
                desc = output_def["description"]

                # Create a clean output name
                output_name = f"{block.name}_{attr}"

                lines.append(f'output "{output_name}" {{')
                lines.append(f'  description = "{desc}"')
                lines.append(f'  value       = {resource_ref}.{attr}')
                lines.append('}')
                lines.append('')

        # If multiple resources, create map outputs
        else:
            for output_def in output_config:
                attr = output_def["attribute"]
                desc = output_def["description"]

                # Create output name based on resource type and attribute
                type_suffix = resource_type.replace("aws_", "").replace("_", "-")
                output_name = f"{type_suffix}_{attr}s"

                lines.append(f'output "{output_name}" {{')
                lines.append(f'  description = "Map of {desc} for all {resource_type} resources"')
                lines.append('  value       = {')

                for block in blocks:
                    resource_ref = f"{resource_type}.{block.name}"
                    lines.append(f'    "{block.name}" = {resource_ref}.{attr}')

                lines.append('  }')
                lines.append('}')
                lines.append('')

    return '\n'.join(lines)


def _parse_variable_block(block_text: str) -> dict:
    """Parse a Terraform variable block into a dictionary.

    Args:
        block_text: The text of a variable block

    Returns:
        Dictionary with keys: name, description, type, default
    """
    result = {"name": "", "description": "", "type": "", "default": ""}

    # Extract variable name from opening line
    name_match = re.search(r'variable\s+"([^"]+)"', block_text)
    if name_match:
        result["name"] = name_match.group(1)

    # Extract description
    desc_match = re.search(r'description\s*=\s*"([^"]*)"', block_text)
    if desc_match:
        result["description"] = desc_match.group(1)

    # Extract type
    type_match = re.search(r'type\s*=\s*(\S+)', block_text)
    if type_match:
        result["type"] = type_match.group(1)

    # Extract default value (if present)
    default_match = re.search(r'default\s*=\s*(.+?)(?:\n|$)', block_text)
    if default_match:
        result["default"] = default_match.group(1).strip()

    return result


def _parse_output_block(block_text: str) -> dict:
    """Parse a Terraform output block into a dictionary.

    Args:
        block_text: The text of an output block

    Returns:
        Dictionary with keys: name, description
    """
    result = {"name": "", "description": ""}

    # Extract output name from opening line
    name_match = re.search(r'output\s+"([^"]+)"', block_text)
    if name_match:
        result["name"] = name_match.group(1)

    # Extract description
    desc_match = re.search(r'description\s*=\s*"([^"]*)"', block_text)
    if desc_match:
        result["description"] = desc_match.group(1)

    return result


def _generate_readme_content(
    module_dir: Path,
    module_name: str,
    resource_types: set[str]
) -> str:
    """Generate README.md content for a module.

    Args:
        module_dir: Path to the module directory
        module_name: Name of the module
        resource_types: Set of resource types in the module

    Returns:
        String content for README.md file
    """
    # Format module title (convert dashes to spaces and title case)
    module_title = module_name.replace("-", " ").replace("/", " - ").title()

    lines = [
        f"# {module_title}",
        "",
    ]

    # Add description based on resource types
    if resource_types:
        lines.append("This module manages the following infrastructure resources:")
        lines.append("")

    # Add resources section
    if resource_types:
        lines.append("## Resources")
        lines.append("")
        lines.append("This module creates and manages the following resources:")
        for resource_type in sorted(resource_types):
            lines.append(f"- {resource_type}")
        lines.append("")

    # Parse variables.tf if it exists
    variables_file = module_dir / "variables.tf"
    variables = []
    if variables_file.exists():
        content = variables_file.read_text()
        # Split by variable blocks
        var_blocks = re.findall(
            r'variable\s+"[^"]+"\s*\{[^}]*\}',
            content,
            re.DOTALL
        )
        for block in var_blocks:
            var_info = _parse_variable_block(block)
            if var_info["name"]:
                variables.append(var_info)

    # Add inputs section
    if variables:
        lines.append("## Inputs")
        lines.append("")
        lines.append("| Name | Description | Type | Default |")
        lines.append("|------|-------------|------|---------|")
        for var in variables:
            name = var["name"]
            desc = var["description"] or "n/a"
            var_type = var["type"] or "string"
            default = var["default"] or "n/a"
            # Escape pipe characters in values
            desc = desc.replace("|", "\\|")
            default = default.replace("|", "\\|")
            lines.append(f"| {name} | {desc} | {var_type} | {default} |")
        lines.append("")

    # Parse outputs.tf if it exists
    outputs_file = module_dir / "outputs.tf"
    outputs = []
    if outputs_file.exists():
        content = outputs_file.read_text()
        # Split by output blocks
        output_blocks = re.findall(
            r'output\s+"[^"]+"\s*\{[^}]*\}',
            content,
            re.DOTALL
        )
        for block in output_blocks:
            output_info = _parse_output_block(block)
            if output_info["name"]:
                outputs.append(output_info)

    # Add outputs section
    if outputs:
        lines.append("## Outputs")
        lines.append("")
        lines.append("| Name | Description |")
        lines.append("|------|-------------|")
        for output in outputs:
            name = output["name"]
            desc = output["description"] or "n/a"
            # Escape pipe characters
            desc = desc.replace("|", "\\|")
            lines.append(f"| {name} | {desc} |")
        lines.append("")

    # Add usage example
    lines.append("## Usage")
    lines.append("")
    lines.append("```hcl")
    # Convert module path separators for the module name
    tf_module_name = module_name.replace("/", "-").replace("\\", "-")
    lines.append(f'module "{tf_module_name}" {{')
    lines.append(f'  source = "./modules/{module_name}"')
    lines.append("")

    # Add example variable assignments (only for non-default variables)
    example_vars = [v for v in variables if v["name"] not in ["tags", "environment"]]
    if example_vars:
        # Add first few example variables
        for var in example_vars[:3]:
            var_name = var["name"]
            var_type = var["type"]

            # Generate example value based on type
            if var_type == "string":
                example_value = '"example-value"'
            elif var_type == "number":
                example_value = "100"
            elif var_type == "bool":
                example_value = "true"
            elif "map" in var_type:
                example_value = "{}"
            elif "list" in var_type:
                example_value = "[]"
            else:
                example_value = "null"

            lines.append(f"  {var_name} = {example_value}")
        lines.append("")

    # Always show tags and environment as examples
    lines.append("  tags = {")
    lines.append('    Project = "example"')
    lines.append('    Owner   = "team"')
    lines.append("  }")
    lines.append("")
    lines.append('  environment = "production"')
    lines.append("}")
    lines.append("```")
    lines.append("")

    return '\n'.join(lines)


def _create_module_metadata_files(module_dir: Path) -> None:
    """Create standard module metadata files with auto-generated content.

    Analyzes the resource blocks in the module directory and generates:
    - variables.tf with resource-specific variables
    - outputs.tf with resource-specific outputs
    - locals.tf with common local values
    - README.md with module documentation
    """
    # Get the module name from the directory path
    # Find the modules directory in the path
    parts = module_dir.parts
    try:
        modules_index = parts.index("modules")
        # Get everything after "modules"
        module_name = "/".join(parts[modules_index + 1:])
    except (ValueError, IndexError):
        # Fallback to just the directory name
        module_name = module_dir.name

    # Scan all .tf files in module to identify resource types
    resource_types = set()
    for tf_file in module_dir.glob("*.tf"):
        if tf_file.name in ("variables.tf", "outputs.tf", "locals.tf"):
            continue
        content = tf_file.read_text()
        for block in _iter_resource_blocks(content):
            resource_types.add(block.resource_type)

    # Create variables.tf with auto-generated content
    variables_file = module_dir / "variables.tf"
    if not variables_file.exists():
        variables_content = _generate_variables_content(module_dir, resource_types)
        variables_file.write_text(variables_content)
        logger.debug("Generated variables.tf for module: %s", module_dir.name)

    # Create outputs.tf with auto-generated content
    outputs_file = module_dir / "outputs.tf"
    if not outputs_file.exists():
        outputs_content = _generate_outputs_content(module_dir, resource_types)
        outputs_file.write_text(outputs_content)
        logger.debug("Generated outputs.tf for module: %s", module_dir.name)

    # Create locals.tf if it doesn't exist
    locals_file = module_dir / "locals.tf"
    if not locals_file.exists():
        locals_content = '''# Local values
# Add your local computed values here

locals {
  common_tags = merge(
    var.tags,
    {
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  )
}
'''
        locals_file.write_text(locals_content)
        logger.debug("Generated locals.tf for module: %s", module_dir.name)

    # Create README.md with auto-generated content
    readme_file = module_dir / "README.md"
    if not readme_file.exists():
        readme_content = _generate_readme_content(module_dir, module_name, resource_types)
        readme_file.write_text(readme_content)
        logger.debug("Generated README.md for module: %s", module_dir.name)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class EnterpriseModuleGenerator:
    """Post-process generated Terraform files into enterprise modules."""

    def __init__(self, provider: str = "aws") -> None:
        self.provider = provider.lower()
        self.resource_map = RESOURCE_MODULE_MAP.get(self.provider, {})

    # Public -----------------------------------------------------------------

    def generate(self, output_dir: Path) -> List[Path]:
        """
        Reorganise Terraform files within ``output_dir`` into enterprise modules.

        The function scans every ``*.tf`` file, moves recognised resource blocks
        into the configured module files and deletes the original file when all
        resources have been relocated.

        Parameters
        ----------
        output_dir:
            Directory containing the generated Terraform configuration.

        Returns
        -------
        list[Path]
            A list of module files that were created or modified.
        """

        output_path = Path(output_dir)
        if not output_path.exists():
            logger.debug("Enterprise module generation skipped; %s does not exist", output_path)
            return []

        if not self.resource_map:
            logger.debug(
                "Enterprise module generation skipped; no mapping available for provider '%s'",
                self.provider,
            )
            return []

        module_base = output_path / "modules"
        module_base.mkdir(parents=True, exist_ok=True)

        updated_files: List[Path] = []
        module_dirs_used: set[Path] = set()

        for tf_file in sorted(output_path.glob("*.tf")):
            if tf_file.name in {"provider.tf", "variables.tf", "outputs.tf"}:
                # Keep common root files untouched
                continue

            content = tf_file.read_text()
            blocks = list(_iter_resource_blocks(content))
            if not blocks:
                continue

            cursor = 0
            keep_segments: List[str] = []
            file_modified = False

            for block in blocks:
                mapping = self.resource_map.get(block.resource_type)
                if not mapping:
                    continue

                module_name, module_file = mapping
                module_dir = module_base / module_name
                module_dir.mkdir(parents=True, exist_ok=True)
                destination = module_dir / module_file

                _append_to_module_file(destination, block)
                if destination not in updated_files:
                    updated_files.append(destination)

                # Track which module directories we've used
                module_dirs_used.add(module_dir)

                keep_segments.append(content[cursor:block.start])
                cursor = block.end
                file_modified = True

            # Always append remaining content
            keep_segments.append(content[cursor:])
            new_content = "".join(keep_segments).strip()

            # Delete file if it's empty OR only contains comments/whitespace
            if not new_content or _is_only_comments_or_whitespace(new_content):
                tf_file.unlink()
                logger.debug("Deleted file with no resources: %s", tf_file)
            elif file_modified:
                # Only write back if we actually moved resources
                tf_file.write_text(new_content + "\n")

        # Create module metadata files for each module directory
        for module_dir in module_dirs_used:
            _create_module_metadata_files(module_dir)
            # Add metadata files to updated_files list
            for metadata_file in ["variables.tf", "outputs.tf", "locals.tf", "README.md"]:
                metadata_path = module_dir / metadata_file
                if metadata_path.exists() and metadata_path not in updated_files:
                    updated_files.append(metadata_path)

        # Generate modules.tf with module instantiation blocks
        if module_dirs_used:
            modules_tf = self._generate_module_blocks(output_path, module_dirs_used)
            if modules_tf:
                updated_files.append(modules_tf)

        return updated_files

    def _generate_module_blocks(self, output_dir: Path, module_dirs: set) -> Path:
        """Generate modules.tf with module instantiation blocks.

        This creates the root-level module blocks that instantiate each
        enterprise module, allowing terraform to use them.

        Args:
            output_dir: Root output directory
            module_dirs: Set of module directories that were created

        Returns:
            Path to the generated modules.tf file
        """
        modules_tf_path = output_dir / "modules.tf"

        # Get module names relative to the modules/ directory
        modules_base = output_dir / "modules"
        module_names = sorted(
            str(d.relative_to(modules_base))
            for d in module_dirs
            if d.is_dir()
        )

        lines = [
            "# Module instantiation blocks",
            "# Generated by terraback enterprise modules",
            "#",
            "# Each module below corresponds to a directory in ./modules/",
            "",
        ]

        for module_name in module_names:
            # Convert path separators to hyphens for module name
            tf_module_name = module_name.replace("/", "-").replace("\\", "-")
            lines.append(f'module "{tf_module_name}" {{')
            lines.append(f'  source = "./modules/{module_name}"')
            lines.append("}")
            lines.append("")

        modules_tf_path.write_text("\n".join(lines))
        logger.debug("Generated module blocks: %s", modules_tf_path)

        return modules_tf_path


__all__ = ["EnterpriseModuleGenerator"]

