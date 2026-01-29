"""Scan commands for discovering cloud resources."""
import typer
from pathlib import Path
from typing import Optional

from terraback.utils.logging import get_logger
from terraback.cli.scan import scan_all, scan_recursive, check_auth, upgrade_info

logger = get_logger(__name__)

app = typer.Typer(name="scan", help="Resource scanning commands")


@app.command("all")
def cmd_scan_all(
    provider: str = typer.Argument(..., help="Cloud provider: 'aws', 'azure', or 'gcp'"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory to save Terraform files"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile name"),
    region: Optional[str] = typer.Option(None, "--region", "-r", help="AWS region, Azure location, or GCP region"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure subscription ID"),
    project_id: Optional[str] = typer.Option(None, "--project-id", help="GCP project ID"),
    resource_group: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Azure resource group"),
    zone: Optional[str] = typer.Option(None, "--zone", "-z", help="GCP zone"),
    with_deps: bool = typer.Option(False, "--with-deps", help="Recursively scan dependencies (Professional feature)"),
    parallel: int = typer.Option(1, "--parallel", help="Number of parallel workers (1-32)"),
    enterprise_modules: bool = typer.Option(
        False,
        "--enterprise-modules",
        help="Generate complete Terraform stack with enterprise modules (Professional feature)",
    ),
):
    """Scan all resources in a cloud provider."""
    scan_all(
        provider=provider,
        output_dir=output_dir,
        profile=profile,
        region=region,
        subscription_id=subscription_id,
        project_id=project_id,
        resource_group=resource_group,
        zone=zone,
        with_deps=with_deps,
        parallel=parallel,
        enterprise_modules=enterprise_modules,
    )


@app.command("recursive")
def cmd_scan_recursive(
    provider: str = typer.Argument(..., help="Cloud provider: 'aws', 'azure', or 'gcp'"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory to save Terraform files"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile name"),
    region: Optional[str] = typer.Option(None, "--region", "-r", help="AWS region, Azure location, or GCP region"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure subscription ID"),
    project_id: Optional[str] = typer.Option(None, "--project-id", help="GCP project ID"),
    zone: Optional[str] = typer.Option(None, "--zone", "-z", help="GCP zone"),
):
    """Recursively scan all resources and their dependencies (Professional feature)."""
    scan_recursive(
        resource_type=provider,
        output_dir=output_dir,
        profile=profile,
        region=region,
        subscription_id=subscription_id,
        project_id=project_id,
        zone=zone,
    )


@app.command("auth-check")
def cmd_auth_check():
    """Check authentication status for all cloud providers."""
    check_auth()


@app.command("upgrade-info")
def cmd_upgrade_info():
    """Display information about upgrading to Terraback Professional."""
    upgrade_info()