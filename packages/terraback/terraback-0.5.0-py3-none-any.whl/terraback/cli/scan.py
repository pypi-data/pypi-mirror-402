from pathlib import Path
from typing import Optional

import typer

from terraback.cli import aws, azure, gcp
from terraback.core.license import require_professional, get_active_tier, Tier, check_feature_access
from terraback.utils.scan_cache import get_scan_cache
from terraback.utils.stack_generator import (
    StackGenerator,
    StackGenerationResult
)
from terraback.terraform_generator.imports import generate_imports_tf


def scan_all(
    provider: str,
    output_dir: Path = Path("generated"),
    profile: Optional[str] = None,
    region: Optional[str] = None,
    subscription_id: Optional[str] = None,
    project_id: Optional[str] = None,
    resource_group: Optional[str] = None,
    zone: Optional[str] = None,
    with_deps: bool = False,
    parallel: int = 1,
    enterprise_modules: bool = False,
):
    provider = provider.lower()
    from datetime import timedelta
    get_scan_cache(ttl=timedelta(minutes=60))  # Default 60 min cache TTL
    if parallel < 1:
        typer.echo("Warning: Parallel workers must be at least 1. Setting to 1.", err=True)
        parallel = 1
    elif parallel > 32:
        typer.echo("Warning: Limiting parallel workers to 32 for stability.", err=True)
        parallel = 32
    if parallel > 1:
        typer.secho(f"Parallel mode enabled with {parallel} workers", fg=typer.colors.BRIGHT_GREEN, bold=True)
    if with_deps:
        if not check_feature_access(Tier.PROFESSIONAL):
            typer.echo("\nDependency scanning (--with-deps) requires a Professional license")
            typer.echo("Proceeding with independent scanning of each service...")
            typer.echo("To unlock dependency scanning: terraback license activate <key>\n")
    # Skip terraform validation if using enterprise modules (they need customization)
    check_terraform = not enterprise_modules

    if provider == "aws":
        aws.register()
        from terraback.cli.aws import scan_all_aws
        scan_all_aws(output_dir=output_dir, profile=profile, region=region, with_deps=with_deps, parallel=parallel, check=check_terraform)
    elif provider == "azure":
        azure.register()
        from terraback.cli.azure import scan_all_azure
        scan_all_azure(
            output_dir=output_dir,
            subscription_id=subscription_id,
            location=region,
            resource_group_name=resource_group,
            with_deps=with_deps,
            parallel=parallel,
            check=check_terraform,
        )
    elif provider == "gcp":
        gcp.register()
        from terraback.cli.gcp import scan_all_gcp
        scan_all_gcp(
            output_dir=output_dir,
            project_id=project_id,
            region=region,
            zone=zone,
            with_deps=with_deps,
            parallel=parallel,
            check=check_terraform,
        )
    else:
        typer.echo(f"Error: Unknown provider '{provider}'. Use 'aws', 'azure', or 'gcp'.", err=True)
        raise typer.Exit(code=1)

    # Generate imports.tf for basic scan (enterprise modules generates its own)
    if not enterprise_modules:
        imports_path = generate_imports_tf(output_dir)
        if imports_path:
            typer.secho(
                f"\nGenerated {imports_path.name} - run 'terraform plan' to preview imports",
                fg=typer.colors.GREEN
            )

    if enterprise_modules:
        if not check_feature_access(Tier.PROFESSIONAL):
            typer.secho(
                "\nEnterprise module generation (--enterprise-modules) requires a Professional license",
                fg=typer.colors.YELLOW,
                bold=True
            )
            typer.echo("Your current tier: " + get_active_tier().value.capitalize())
            typer.echo("To unlock: terraback license activate <key>\n")
            return

        typer.echo("\nGenerating enterprise modules...")

        # Collect scanned resources
        scanned_resources = _collect_scanned_resources(output_dir)

        # Generate full stack with auto-detected environments
        generator = StackGenerator(provider=provider)
        result = generator.generate_full_stack(
            output_dir=output_dir,
            scanned_resources=scanned_resources,
            environments=["auto"],  # Auto-detect environments
        )

        # Report results
        _report_full_stack_generation(result, output_dir)


@require_professional
def scan_recursive(
    resource_type: str,
    output_dir: Path = Path("generated"),
    profile: Optional[str] = None,
    region: Optional[str] = None,
    subscription_id: Optional[str] = None,
    project_id: Optional[str] = None,
    zone: Optional[str] = None,
):
    from datetime import timedelta
    from terraback.utils.cross_scan_registry import base_recursive_scan
    resource_type_map = {
        'vm': 'azure_virtual_machine',
        'vms': 'azure_virtual_machine',
        'lb': 'azure_lb',
        'lbs': 'azure_lb',
        'rg': 'azure_resource_group',
        'rgs': 'azure_resource_group',
        'vnet': 'azure_virtual_network',
        'vpc': 'vpc',
        'subnet': 'azure_subnet',
        'subnets': 'azure_subnet',
        'nsg': 'azure_network_security_group',
        'nsgs': 'azure_network_security_group',
        'instance': 'ec2',
        'instances': 'ec2',
        'bucket': 's3_bucket',
        'buckets': 's3_bucket',
        'gcp_vm': 'gcp_instance',
        'gcp_vms': 'gcp_instance',
        'gcp_bucket': 'gcp_bucket',
        'gcp_buckets': 'gcp_bucket',
    }
    normalized_type = resource_type_map.get(resource_type.lower(), resource_type.lower())
    typer.echo(f"Starting Professional recursive scan for '{normalized_type}'...")
    is_azure = normalized_type.startswith('azure_')
    is_gcp = normalized_type.startswith('gcp_')
    if is_azure:
        azure.register()
    elif is_gcp:
        gcp.register()
    else:
        aws.register()
    kwargs = {'resource_type': normalized_type, 'output_dir': output_dir}
    if is_azure:
        from terraback.cli.azure.session import get_default_subscription_id
        if not subscription_id:
            subscription_id = get_default_subscription_id()
            if not subscription_id:
                typer.echo("Error: No Azure subscription found. Please run 'az login'", err=True)
                raise typer.Exit(code=1)
        kwargs['subscription_id'] = subscription_id
        kwargs['location'] = region
    elif is_gcp:
        from terraback.cli.gcp.session import get_default_project_id
        if not project_id:
            project_id = get_default_project_id()
            if not project_id:
                typer.echo("Error: No GCP project found. Please run 'gcloud config set project'", err=True)
                raise typer.Exit(code=1)
        kwargs['project_id'] = project_id
        kwargs['region'] = region
        kwargs['zone'] = zone
    else:
        from terraback.cli.common.defaults import get_aws_defaults
        defaults = get_aws_defaults()
        kwargs['profile'] = profile or defaults['profile']
        kwargs['region'] = region or defaults['region']

    # Enable caching with default 60 min TTL
    cache = get_scan_cache(cache_dir=output_dir / '.terraback' / 'cache', ttl=timedelta(minutes=60))
    base_recursive_scan(**kwargs)
    stats = cache.get_stats()
    typer.echo("\nCache Statistics:")
    typer.echo(f"  Hit Rate: {stats['hit_rate']}")
    typer.echo(f"  Cache Size: {stats['total_size_kb']} KB")


def check_auth() -> None:
    typer.echo("Checking cloud authentication status...\n")
    try:
        from terraback.cli.aws.session import get_boto_session
        session = get_boto_session()
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        typer.echo("AWS: Authenticated")
        typer.echo(f"  Account: {identity['Account']}")
        typer.echo(f"  User/Role: {identity['Arn'].split('/')[-1]}")
        typer.echo(f"  Region: {session.region_name}")
    except Exception:
        typer.echo("AWS: Not authenticated (run: aws configure)")
    try:
        from terraback.cli.azure.session import get_default_subscription_id
        sub_id = get_default_subscription_id()
        if sub_id:
            typer.echo("\nAzure: Authenticated")
            typer.echo(f"  Subscription: {sub_id}")
        else:
            typer.echo("\nAzure: Not authenticated (run: az login)")
    except Exception:
        typer.echo("\nAzure: Not authenticated (run: az login)")
    try:
        from terraback.cli.gcp.session import get_default_project_id
        project_id = get_default_project_id()
        if project_id:
            typer.echo("\nGCP: Authenticated")
            typer.echo(f"  Project: {project_id}")
        else:
            typer.echo("\nGCP: Not authenticated (run: gcloud auth application-default login)")
    except Exception:
        typer.echo("\nGCP: Not authenticated (run: gcloud auth application-default login)")


def upgrade_info() -> None:
    current_tier = get_active_tier()
    if current_tier == Tier.COMMUNITY:
        typer.echo("Save 40+ Hours per Infrastructure Migration\n")
        typer.echo("Community Edition (Free) - What you have:")
        typer.echo("  - Core resources: EC2, VPC, S3, VMs, VNets, Storage")
        typer.echo("  - AWS, Azure, and GCP scanning")
        typer.echo("  - Ready-to-use Terraform files\n")
        typer.echo("Professional License ($499 one-time) - What you unlock:")
        typer.echo("  - Complete coverage: RDS, Lambda, EKS, ALB, Route53, and 50+ services")
        typer.echo("  - Auto-generate reusable Terraform modules (--enterprise-modules)")
        typer.echo("  - Smart dependency detection - no missing resources (--with-deps)")
        typer.echo("  - Scan multiple accounts/subscriptions in parallel")
        typer.echo("  - Save 40-80 hours on typical infrastructure projects")
        typer.echo("  - Lifetime access with all future updates\n")
        typer.echo("Get started: https://terraback.lemonsqueezy.com/checkout/buy/d7168719-2f22-41d4-8c8b-84dcfc96ca51")
        typer.echo("Questions: sales@terraback.io")
    elif current_tier == Tier.PROFESSIONAL:
        typer.secho("You have Professional access!", fg=typer.colors.GREEN, bold=True)
        typer.echo("All advanced features are unlocked.")
    elif current_tier == Tier.ENTERPRISE:
        typer.secho("You have Enterprise access!", fg=typer.colors.GREEN, bold=True)
        typer.echo("All features including enterprise support are available.")


def _collect_scanned_resources(output_dir: Path) -> dict:
    """
    Collect all scanned resources from generated import JSON files.
    Reads *_import.json files from import/ subdirectory to extract resource data with actual cloud IDs.
    """
    import json
    from terraback.utils.logging import get_logger

    logger = get_logger(__name__)
    resources = {}

    # Read all *_import.json files from import/ subdirectory
    import_dir = output_dir / "import"
    if not import_dir.exists():
        logger.warning(f"Import directory not found: {import_dir}")
        return resources

    for import_file in import_dir.glob("*_import.json"):
        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            for entry in import_data:
                resource_type = entry.get("resource_type", "")
                if not resource_type:
                    continue

                # Get the actual resource data
                resource_data = entry.get("resource_data", {})
                remote_id = entry.get("remote_id", "")

                # Get name_sanitized from resource_data, then resource_name, then generate from remote_id
                name_sanitized = resource_data.get("name_sanitized", "")
                if not name_sanitized:
                    # Try resource_name from the import entry (this is the actual Terraform resource name)
                    name_sanitized = entry.get("resource_name", "")
                if not name_sanitized:
                    # Fall back to using a sanitized version of remote_id
                    from terraback.terraform_generator.filters import terraform_name
                    name_sanitized = terraform_name(remote_id)

                if resource_type not in resources:
                    resources[resource_type] = []

                # Create resource dict with actual cloud ID
                resource = {
                    "name_sanitized": name_sanitized,
                    "id": remote_id,  # Use actual cloud resource ID
                    "_source_file": str(import_file)
                }

                # Preserve all important fields from resource_data for import ID matching
                # These fields are used by ImportBlockGenerator.IMPORT_ID_ATTRIBUTES
                important_fields = [
                    # Common identifiers
                    "Name", "name", "Id", "id", "Tags", "tags",
                    # AWS EC2/VPC
                    "InstanceId", "VpcId", "SubnetId", "GroupId", "VolumeId",
                    "InternetGatewayId", "RouteTableId", "NetworkInterfaceId",
                    # AWS Lambda
                    "FunctionName", "FunctionArn",
                    # AWS IAM
                    "RoleName", "PolicyName", "Arn",
                    # AWS S3
                    "BucketName", "Bucket",
                    # AWS DynamoDB
                    "TableName", "TableArn",
                    # AWS ACM
                    "CertificateArn", "DomainName",
                    # AWS CloudFront
                    "DistributionId",
                    # AWS CloudWatch
                    "logGroupName", "LogGroupName", "AlarmName",
                    # AWS KMS
                    "KeyId", "AliasName",
                    # AWS Secrets Manager
                    "SecretId", "SecretArn", "VersionId",
                    # AWS SNS
                    "TopicArn", "TopicName", "SubscriptionArn",
                    # AWS SQS
                    "QueueUrl", "QueueName", "QueueArn",
                    # AWS ECS
                    "clusterName", "ClusterArn", "serviceName", "ServiceArn",
                    # AWS ECR
                    "repositoryName", "RepositoryArn",
                    # AWS CloudTrail
                    "TrailArn",
                    # AWS Kinesis
                    "StreamName", "StreamArn",
                    # AWS EventBridge
                    "RuleName", "EventBusName",
                    # AWS GuardDuty
                    "DetectorId",
                    # AWS RDS
                    "DBInstanceIdentifier", "DBSubnetGroupName",
                    # AWS Backup
                    "BackupVaultName", "BackupVaultArn",
                    # AWS API Gateway
                    "restApiId", "RestApiId", "resourceId", "httpMethod", "deploymentId",
                    # AWS Route53
                    "ZoneId", "HostedZoneId",
                    # AWS Step Functions
                    "stateMachineArn", "stateMachineName",
                    # AWS Lambda Permission
                    "StatementId",
                ]
                for key in important_fields:
                    if key in resource_data:
                        resource[key] = resource_data[key]

                resources[resource_type].append(resource)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from {import_file}: {e}")
        except Exception as e:
            logger.warning(f"Failed to read {import_file}: {e}")

    logger.info(f"Collected {sum(len(v) for v in resources.values())} resources from {len(resources)} resource types")
    return resources


def _report_full_stack_generation(result: StackGenerationResult, output_dir: Path) -> None:
    """Report stack generation results to user."""
    typer.echo("\n" + "=" * 60)
    typer.secho("Full Terraform Stack Generated!", fg=typer.colors.GREEN, bold=True)
    typer.echo("=" * 60)

    if result.environments:
        typer.echo(f"\nDetected environments: {', '.join(result.environments)}")

    typer.echo("\nRoot configuration files:")
    for file in result.root_files:
        typer.echo(f"  - {file.name}")

    typer.echo(f"\nModule files: {len(result.module_files)} files in modules/")

    if result.config_files:
        typer.echo(f"\nEnvironment configurations:")
        for file in result.config_files:
            typer.echo(f"  - config/{file.name}")

    if result.import_blocks_generated:
        typer.echo("\nImport blocks: imports.tf")

    typer.echo("\nNext steps:")
    typer.echo("  1. Review generated configuration")
    typer.echo("  2. Initialize Terraform: make init")
    if len(result.environments) > 1:
        typer.echo(f"  3. Plan changes: make plan ENV={result.environments[0]}")
        typer.echo(f"  4. Import resources: terraform plan -var-file=config/{result.environments[0]}.tfvars")
        typer.echo(f"  5. Apply configuration: make apply ENV={result.environments[0]}")
    else:
        typer.echo("  3. Plan changes: make plan")
        typer.echo("  4. Import resources: terraform plan")
        typer.echo("  5. Apply configuration: make apply")

    if result.errors:
        typer.echo("\nWarnings:")
        for error in result.errors:
            typer.secho(f"  ! {error}", fg=typer.colors.YELLOW)
