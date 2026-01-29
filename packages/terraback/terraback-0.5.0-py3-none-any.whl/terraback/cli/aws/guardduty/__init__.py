import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(name="guardduty", help="Work with GuardDuty resources")

from .detectors import scan_guardduty_detectors, list_guardduty_detectors, import_guardduty_detector


@app.command("scan")
def scan(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory to save Terraform files"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile name"),
    region: str = typer.Option("us-east-1", "--region", "-r", help="AWS region"),
):
    """Scan GuardDuty detectors and generate Terraform code."""
    scan_guardduty_detectors(output_dir, profile, region)


@app.command("list")
def list_detectors(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """List all scanned GuardDuty detectors."""
    list_guardduty_detectors(output_dir)


@app.command("import")
def import_detector(
    detector_id: str = typer.Argument(..., help="ID of the GuardDuty detector to import"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """Import a specific GuardDuty detector into Terraform state."""
    import_guardduty_detector(detector_id, output_dir)


def register():
    """Register GuardDuty scan functions with the cross-scan registry."""
    from terraback.utils.cross_scan_registry import register_scan_function
    from terraback.core.license import Tier

    register_scan_function(
        "aws_guardduty_detectors",
        scan_guardduty_detectors,
        tier=Tier.COMMUNITY
    )
