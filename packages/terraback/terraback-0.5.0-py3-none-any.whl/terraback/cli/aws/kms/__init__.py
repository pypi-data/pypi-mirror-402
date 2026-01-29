import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(name="kms", help="Work with KMS resources")

from .keys import scan_kms_keys, list_kms_keys, import_kms_key
from .aliases import scan_kms_aliases, list_kms_aliases, import_kms_alias


@app.command("scan")
def scan(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory to save Terraform files"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile name"),
    region: str = typer.Option("us-east-1", "--region", "-r", help="AWS region"),
):
    """Scan KMS keys and aliases and generate Terraform code."""
    scan_kms_keys(output_dir, profile, region)
    scan_kms_aliases(output_dir, profile, region)


@app.command("list")
def list_resources(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """List all scanned KMS resources."""
    typer.echo("KMS Keys:")
    list_kms_keys(output_dir)
    typer.echo("\nKMS Aliases:")
    list_kms_aliases(output_dir)


@app.command("import-key")
def import_key(
    key_id: str = typer.Argument(..., help="ID of the KMS key to import"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """Import a specific KMS key into Terraform state."""
    import_kms_key(key_id, output_dir)


@app.command("import-alias")
def import_alias(
    alias_name: str = typer.Argument(..., help="Name of the KMS alias to import (e.g., alias/my-key)"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """Import a specific KMS alias into Terraform state."""
    import_kms_alias(alias_name, output_dir)


def register():
    """Register KMS scan functions with the cross-scan registry."""
    from terraback.utils.cross_scan_registry import register_scan_function
    from terraback.core.license import Tier

    register_scan_function(
        "aws_kms_keys",
        scan_kms_keys,
        tier=Tier.COMMUNITY
    )

    register_scan_function(
        "aws_kms_aliases",
        scan_kms_aliases,
        tier=Tier.COMMUNITY
    )
