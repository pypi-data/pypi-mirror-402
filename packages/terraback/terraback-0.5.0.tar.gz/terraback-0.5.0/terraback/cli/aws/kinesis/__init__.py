import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(name="kinesis", help="Work with Kinesis resources")

from .streams import scan_kinesis_streams, list_kinesis_streams, import_kinesis_stream
from .firehose import scan_firehose_delivery_streams, list_firehose_delivery_streams, import_firehose_delivery_stream


@app.command("scan")
def scan(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory to save Terraform files"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile name"),
    region: str = typer.Option("us-east-1", "--region", "-r", help="AWS region"),
):
    """Scan Kinesis resources (streams and firehose) and generate Terraform code."""
    scan_kinesis_streams(output_dir, profile, region)
    scan_firehose_delivery_streams(output_dir, profile, region)


@app.command("list")
def list_resources(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """List all scanned Kinesis resources."""
    typer.echo("Kinesis Data Streams:")
    list_kinesis_streams(output_dir)
    typer.echo("\nKinesis Firehose Delivery Streams:")
    list_firehose_delivery_streams(output_dir)


@app.command("import-stream")
def import_stream(
    stream_name: str = typer.Argument(..., help="Name of the Kinesis stream to import"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """Import a specific Kinesis stream into Terraform state."""
    import_kinesis_stream(stream_name, output_dir)


@app.command("import-firehose")
def import_firehose(
    stream_name: str = typer.Argument(..., help="Name of the Firehose delivery stream to import"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """Import a specific Kinesis Firehose delivery stream into Terraform state."""
    import_firehose_delivery_stream(stream_name, output_dir)


def register():
    """Register Kinesis scan functions with the cross-scan registry."""
    from terraback.utils.cross_scan_registry import register_scan_function
    from terraback.core.license import Tier

    register_scan_function(
        "aws_kinesis_streams",
        scan_kinesis_streams,
        tier=Tier.COMMUNITY
    )

    register_scan_function(
        "aws_kinesis_firehose_delivery_streams",
        scan_firehose_delivery_streams,
        tier=Tier.COMMUNITY
    )
