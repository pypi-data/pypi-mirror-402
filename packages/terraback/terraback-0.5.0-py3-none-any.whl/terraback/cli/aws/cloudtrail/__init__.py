import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(name="cloudtrail", help="Work with CloudTrail resources")

from .trails import scan_cloudtrail_trails, list_cloudtrail_trails, import_cloudtrail_trail


@app.command("scan")
def scan(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory to save Terraform files"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile name"),
    region: str = typer.Option("us-east-1", "--region", "-r", help="AWS region"),
):
    """Scan CloudTrail trails and generate Terraform code."""
    scan_cloudtrail_trails(output_dir, profile, region)


@app.command("list")
def list_trails(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """List all scanned CloudTrail trails."""
    list_cloudtrail_trails(output_dir)


@app.command("import")
def import_trail(
    trail_name: str = typer.Argument(..., help="Name of the CloudTrail trail to import"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """Import a specific CloudTrail trail into Terraform state."""
    import_cloudtrail_trail(trail_name, output_dir)


def register():
    """Register CloudTrail scan functions with the cross-scan registry."""
    from terraback.utils.cross_scan_registry import register_scan_function
    from terraback.core.license import Tier

    register_scan_function(
        "aws_cloudtrail_trails",
        scan_cloudtrail_trails,
        tier=Tier.COMMUNITY
    )
