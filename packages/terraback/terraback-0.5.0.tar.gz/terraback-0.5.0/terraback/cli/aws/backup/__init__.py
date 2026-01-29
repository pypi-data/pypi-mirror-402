import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(name="backup", help="Work with AWS Backup resources")

from .vaults import scan_backup_vaults, list_backup_vaults, import_backup_vault


@app.command("scan")
def scan(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory to save Terraform files"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile name"),
    region: str = typer.Option("us-east-1", "--region", "-r", help="AWS region"),
):
    """Scan AWS Backup resources (vaults, plans, selections) and generate Terraform code."""
    scan_backup_vaults(output_dir, profile, region)


@app.command("list")
def list_vaults(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """List all scanned AWS Backup vaults."""
    list_backup_vaults(output_dir)


@app.command("import")
def import_vault(
    vault_name: str = typer.Argument(..., help="Name of the backup vault to import"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """Import a specific AWS Backup vault into Terraform state."""
    import_backup_vault(vault_name, output_dir)


def register():
    """Register AWS Backup scan functions with the cross-scan registry."""
    from terraback.utils.cross_scan_registry import register_scan_function
    from terraback.core.license import Tier

    register_scan_function(
        "aws_backup_vaults",
        scan_backup_vaults,
        tier=Tier.COMMUNITY
    )
