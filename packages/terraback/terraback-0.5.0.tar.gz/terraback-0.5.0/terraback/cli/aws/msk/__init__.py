import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(name="msk", help="Work with MSK (Managed Streaming for Kafka) resources")

from .clusters import scan_msk_clusters, list_msk_clusters, import_msk_cluster


@app.command("scan")
def scan(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory to save Terraform files"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile name"),
    region: str = typer.Option("us-east-1", "--region", "-r", help="AWS region"),
):
    """Scan MSK clusters and generate Terraform code."""
    scan_msk_clusters(output_dir, profile, region)


@app.command("list")
def list_clusters(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """List all scanned MSK clusters."""
    list_msk_clusters(output_dir)


@app.command("import")
def import_cluster(
    cluster_arn: str = typer.Argument(..., help="ARN of the MSK cluster to import"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """Import a specific MSK cluster into Terraform state."""
    import_msk_cluster(cluster_arn, output_dir)


def register():
    """Register MSK scan functions with the cross-scan registry."""
    from terraback.utils.cross_scan_registry import register_scan_function
    from terraback.core.license import Tier

    register_scan_function(
        "aws_msk_clusters",
        scan_msk_clusters,
        tier=Tier.COMMUNITY
    )
