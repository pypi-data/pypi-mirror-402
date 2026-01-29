import typer
import json
from pathlib import Path
from typing import Optional

# --- App Definition ---
app = typer.Typer(
    name="aws",
    help="Work with Amazon Web Services resources.",
    no_args_is_help=True,
)

# --- Service Module Imports ---
# Import all AWS service modules that contain their own Typer apps and registration logic.
from . import (
    ec2, vpc, s3, iam, rds, lambda_func, elbv2, elb,
    route53, sns, sqs, acm, apigateway, autoscaling,
    cloudfront, cloudwatch, ecr, ecs, efs, eips,
    elasticache, secretsmanager, ssm, dynamodb, kms,
    eventbridge, stepfunctions, kinesis, opensearch, msk,
    cloudtrail, guardduty, backup
)

# --- Module and Dependency Definitions ---
# A single place to define all service modules to be registered.
SERVICE_MODULES = [
    ("EC2", ec2), ("VPC", vpc), ("S3", s3), ("IAM", iam), ("RDS", rds),
    ("Lambda", lambda_func), ("ELBv2", elbv2), ("ELB", elb), ("Route53", route53),
    ("SNS", sns), ("SQS", sqs), ("ACM", acm), ("API Gateway", apigateway),
    ("Auto Scaling", autoscaling), ("CloudFront", cloudfront), ("CloudWatch", cloudwatch),
    ("ECR", ecr), ("ECS", ecs), ("EFS", efs), ("EIPs", eips),
    ("ElastiCache", elasticache), ("Secrets Manager", secretsmanager), ("SSM", ssm),
    ("DynamoDB", dynamodb), ("KMS", kms), ("EventBridge", eventbridge),
    ("Step Functions", stepfunctions), ("Kinesis", kinesis), ("OpenSearch", opensearch),
    ("MSK", msk), ("CloudTrail", cloudtrail), ("GuardDuty", guardduty), ("Backup", backup),
]

# A single place to define all cross-service dependencies for the Professional tier.
PROFESSIONAL_DEPENDENCIES = [
    ("aws_ec2", "aws_vpc"), ("aws_ec2", "aws_security_groups"), ("aws_ec2", "aws_subnets"), ("aws_ec2", "aws_eips"),
    ("aws_vpc", "aws_internet_gateways"), ("aws_nat_gateways", "aws_subnets"), ("aws_elbv2_load_balancers", "aws_subnets"),
    ("aws_rds", "aws_db_subnet_groups"), ("aws_db_subnet_groups", "aws_subnets"), ("aws_lambda", "aws_iam_roles"),
    ("aws_ecs_services", "aws_ecs_clusters"), ("aws_ecs_services", "aws_ecs_task_definitions"),
]

# --- Registration Logic ---
_registered = False

def register():
    """
    Register all AWS resources and their dependencies with the central cross-scan registry.
    This function is idempotent and will only run once.
    """
    global _registered
    if _registered:
        return
    _registered = True

    from terraback.core.license import check_feature_access, Tier
    from terraback.utils.cross_scan_registry import cross_scan_registry

    with cross_scan_registry.autosave_mode(False):
        # Each module is responsible for registering its own scan functions.
        for service_name, module in SERVICE_MODULES:
            try:
                if hasattr(module, "register"):
                    module.register()
            except Exception as e:
                typer.echo(f"Warning: Failed to register {service_name}: {e}", err=True)

        # Register dependencies only if the user has the required license.
        if check_feature_access(Tier.PROFESSIONAL):
            for source, target in PROFESSIONAL_DEPENDENCIES:
                cross_scan_registry.register_dependency(source, target)

        cross_scan_registry.flush()

# --- CLI Command Definitions ---

# Add each service's Typer app as a subcommand to 'aws'.
# This creates commands like 'terraback aws ec2 scan', 'terraback aws vpc list', etc.
for service_name_lower, module in [(name.lower().replace(" ", ""), mod) for name, mod in SERVICE_MODULES]:
    if hasattr(module, "app"):
        app.add_typer(module.app, name=service_name_lower, help=f"Work with {service_name_lower.upper()} resources.")

@app.command("scan-all")
def scan_all_aws(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory for generated Terraform files"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile name"),
    region: Optional[str] = typer.Option(None, "--region", "-r", help="AWS region"),
    with_deps: bool = typer.Option(False, "--with-deps", help="Recursively scan dependencies (Professional feature)"),
    parallel: int = typer.Option(1, "--parallel", help="Number of parallel workers (Professional feature)"),
    check: bool = typer.Option(True, "--check/--skip-check", help="Validate Terraform after scan"),
):
    """Scan all available AWS resources based on your license tier."""
    register()

    from terraback.cli.aws.session import get_boto_session
    from terraback.core.license import check_feature_access, Tier
    from terraback.utils.cross_scan_registry import cross_scan_registry, recursive_scan, recursive_scan_all, get_all_scan_functions
    from terraback.utils.parallel_scan import ParallelScanManager, create_scan_tasks

    # 1. Authenticate with AWS
    try:
        session = get_boto_session(profile, region or "us-east-1")
        identity = session.client('sts').get_caller_identity()
        typer.echo(f"Scanning AWS resources in account {identity['Account']}")
        typer.echo(f"Region: {region or 'us-east-1 (default)'}")
    except Exception as e:
        typer.echo(f"Error: AWS authentication failed: {e}", err=True)
        raise typer.Exit(code=1)

    # Use us-east-1 as default region if not specified
    effective_region = region or "us-east-1"

    # 2. Handle Dependency Scanning (--with-deps)
    if with_deps:
        if check_feature_access(Tier.PROFESSIONAL):
            typer.echo("\nScanning with dependency resolution...")
            recursive_scan_all(output_dir=output_dir, profile=profile, region=effective_region)
            typer.echo("\nScan complete!")
            return
        else:
            typer.echo("\nDependency scanning ensures no missing references in your Terraform.")
            typer.echo("Unlock with Professional ($499 lifetime): terraback license activate <key>\n")

    # 3. Perform Standard Scan (without --with-deps)
    all_scans = get_all_scan_functions()
    scan_configs = []
    skipped_configs = []

    for name, details in all_scans.items():
        # Only scan AWS resources - filter out other providers
        if not name.startswith("aws_"):
            continue
        
        if check_feature_access(details.get("tier", Tier.COMMUNITY)):
            scan_configs.append({'name': name, 'function': details['function']})
        else:
            skipped_configs.append(name)

    if skipped_configs:
        typer.echo(f"\nNote: {len(skipped_configs)} advanced resources available with Professional license.")

    base_kwargs = {'output_dir': output_dir, 'profile': profile, 'region': effective_region}
    tasks = create_scan_tasks(scan_configs, base_kwargs)

    # 4. Execute Scans (Parallel or Sequential)
    use_parallel = parallel > 1 and check_feature_access(Tier.PROFESSIONAL)
    
    if use_parallel:
        typer.echo(f"\nScanning {len(tasks)} resource types in parallel with {parallel} workers...")
        manager = ParallelScanManager(max_workers=parallel)
        manager.scan_parallel(tasks)
    else:
        if parallel > 1:
            typer.echo("\nParallel scanning (5x faster) available with Professional license.")
        typer.echo(f"\nScanning {len(tasks)} resource types sequentially...")
        for task in tasks:
            typer.echo(f"--- Scanning {task.name} ---")
            task.function(**task.kwargs)

    # Generate post-scan summary
    _print_scan_summary(output_dir, check)


@app.command("import")
def import_all_aws(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing import files"),
    terraform_dir: Optional[Path] = typer.Option(None, "--terraform-dir", "-t", help="Terraform directory (defaults to output_dir)"),
    method: str = typer.Option(
        "auto",
        "--method",
        "-m",
        help="Import method: 'auto' (detect best), 'bulk' (fastest for Terraform 1.5+), 'sequential' (reliable)",
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Import all scanned AWS resources into Terraform state.
    
    This command supports two import methods:
    
    - bulk: Uses Terraform import blocks (requires Terraform 1.5+), imports all 
            resources in a single operation (~2-3 minutes for hundreds of resources)
            
    - sequential: Imports resources one by one, slower but avoids state lock 
                  conflicts (~4 seconds per resource)
    
    By default, it automatically detects the best method based on your Terraform version.
    """
    from terraback.utils.terraform_import import import_resources
    
    if terraform_dir is None:
        terraform_dir = output_dir
    
    # Load import files from import/ subdirectory
    import_dir = output_dir / "import"
    import_files = list(import_dir.glob("*_import.json")) if import_dir.exists() else []
    all_imports = []
    
    for import_file in import_files:
        try:
            with open(import_file, "r") as f:
                resources = json.load(f)
                for resource in resources:
                    all_imports.append({
                        "type": resource.get("resource_type"),
                        "name": resource.get("resource_name"),
                        "id": resource.get("remote_id"),
                        "file": import_file.name,
                    })
        except Exception as e:
            typer.echo(f"Error reading {import_file.name}: {e}", err=True)
    
    if not all_imports:
        typer.echo("No resources to import. Run 'terraback aws scan-all' first.")
        raise typer.Exit(1)
    
    # Show summary
    by_type = {}
    for imp in all_imports:
        resource_type = imp["type"]
        by_type[resource_type] = by_type.get(resource_type, 0) + 1
    
    typer.echo(f"\nFound {len(all_imports)} resources to import:")
    for resource_type, count in sorted(by_type.items()):
        typer.echo(f"  {resource_type}: {count}")
    
    # Confirm
    if not yes:
        if not typer.confirm("\nDo you want to proceed with the import?"):
            raise typer.Exit(0)
    
    # Import
    typer.echo(f"\nImporting resources using {method} method...")
    imported, failed, failed_details = import_resources(
        terraform_dir,
        all_imports,
        method=method,
        progress=True
    )
    
    if failed > 0:
        typer.echo("\nSome resources failed to import:")
        for fail in failed_details[:5]:
            typer.echo(f"  - {fail.get('address', 'unknown')}: {fail.get('error', 'unknown error')}")
        raise typer.Exit(1)
    else:
        typer.echo("\nAll resources imported successfully!")
        typer.echo("Run 'terraform plan' to verify the imported state.")


def _print_scan_summary(output_dir: Path, check: bool = True):
    """Print a comprehensive post-scan summary with actionable next steps."""
    import os
    from datetime import datetime

    typer.echo("\n" + "=" * 60)
    typer.echo("SCAN COMPLETE")
    typer.echo("=" * 60)

    # Count generated files and resources
    tf_files = list(output_dir.glob("*.tf")) if output_dir.exists() else []
    import_dir = output_dir / "import"
    import_files = list(import_dir.glob("*_import.json")) if import_dir.exists() else []

    # Count total resources from import files
    total_resources = 0
    resource_types = {}
    for import_file in import_files:
        try:
            with open(import_file, "r") as f:
                resources = json.load(f)
                total_resources += len(resources)
                for res in resources:
                    rtype = res.get("resource_type", "unknown")
                    resource_types[rtype] = resource_types.get(rtype, 0) + 1
        except Exception:
            pass

    # Print results summary
    typer.echo(f"\nGenerated Files: {len(tf_files)} Terraform files")
    typer.echo(f"Resources Found: {total_resources} across {len(resource_types)} resource types")
    typer.echo(f"Output Location: {output_dir.absolute()}/")

    # Show resource breakdown (top 5)
    if resource_types:
        typer.echo("\nTop Resources:")
        sorted_types = sorted(resource_types.items(), key=lambda x: x[1], reverse=True)[:5]
        for rtype, count in sorted_types:
            typer.echo(f"  - {rtype}: {count}")
        if len(resource_types) > 5:
            typer.echo(f"  ... and {len(resource_types) - 5} more types")

    # Time saved estimate (conservative: 5 min per resource for manual work)
    time_saved_minutes = total_resources * 5
    if time_saved_minutes >= 60:
        hours = time_saved_minutes // 60
        mins = time_saved_minutes % 60
        time_str = f"{hours}h {mins}m" if mins else f"{hours} hours"
    else:
        time_str = f"{time_saved_minutes} minutes"

    typer.echo(f"\nEstimated Time Saved: ~{time_str} of manual Terraform work")

    # Run terraform validation if requested
    if check and tf_files:
        typer.echo("\n" + "-" * 40)
        typer.echo("Running Terraform validation...")
        from terraback.utils.terraform_checker import check_and_fix_terraform_files
        check_and_fix_terraform_files(output_dir)

    # What's next checklist
    typer.echo("\n" + "-" * 40)
    typer.echo("WHAT'S NEXT")
    typer.echo("-" * 40)
    typer.echo("\n1. Review generated Terraform files:")
    typer.echo(f"   cd {output_dir.absolute()}")
    typer.echo("   ls -la *.tf")
    typer.echo("\n2. Initialize Terraform:")
    typer.echo("   terraform init")
    typer.echo("\n3. Import resources into state:")
    typer.echo(f"   terraback aws import -o {output_dir}")
    typer.echo("\n4. Verify with plan (should show no changes):")
    typer.echo("   terraform plan")
    typer.echo("\n5. Your infrastructure is now under Terraform control!")
    typer.echo("")
