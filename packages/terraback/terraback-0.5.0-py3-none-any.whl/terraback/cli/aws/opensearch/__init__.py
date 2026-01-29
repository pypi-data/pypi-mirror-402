import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(name="opensearch", help="Work with OpenSearch resources")

from .domains import scan_opensearch_domains, list_opensearch_domains, import_opensearch_domain


@app.command("scan")
def scan(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory to save Terraform files"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile name"),
    region: str = typer.Option("us-east-1", "--region", "-r", help="AWS region"),
):
    """Scan OpenSearch domains and generate Terraform code."""
    scan_opensearch_domains(output_dir, profile, region)


@app.command("list")
def list_domains(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """List all scanned OpenSearch domains."""
    list_opensearch_domains(output_dir)


@app.command("import")
def import_domain(
    domain_name: str = typer.Argument(..., help="Name of the OpenSearch domain to import"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """Import a specific OpenSearch domain into Terraform state."""
    import_opensearch_domain(domain_name, output_dir)


def register():
    """Register OpenSearch scan functions with the cross-scan registry."""
    from terraback.utils.cross_scan_registry import register_scan_function
    from terraback.core.license import Tier

    register_scan_function(
        "aws_opensearch_domains",
        scan_opensearch_domains,
        tier=Tier.COMMUNITY
    )
