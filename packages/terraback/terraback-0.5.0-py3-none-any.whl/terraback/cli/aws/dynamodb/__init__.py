import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(name="dynamodb", help="Work with DynamoDB resources")

from .tables import scan_dynamodb_tables, list_dynamodb_tables, import_dynamodb_table


@app.command("scan")
def scan(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory to save Terraform files"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile name"),
    region: str = typer.Option("us-east-1", "--region", "-r", help="AWS region"),
):
    """Scan DynamoDB tables and generate Terraform code."""
    scan_dynamodb_tables(output_dir, profile, region)


@app.command("list")
def list_tables(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """List all scanned DynamoDB tables."""
    list_dynamodb_tables(output_dir)


@app.command("import")
def import_table(
    table_name: str = typer.Argument(..., help="Name of the DynamoDB table to import"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """Import a specific DynamoDB table into Terraform state."""
    import_dynamodb_table(table_name, output_dir)


def register():
    """Register DynamoDB scan functions with the cross-scan registry."""
    from terraback.utils.cross_scan_registry import register_scan_function
    from terraback.core.license import Tier

    register_scan_function(
        "aws_dynamodb_tables",
        scan_dynamodb_tables,
        tier=Tier.COMMUNITY
    )
