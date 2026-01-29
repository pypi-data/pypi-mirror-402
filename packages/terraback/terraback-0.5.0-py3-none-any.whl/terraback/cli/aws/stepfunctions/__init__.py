import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(name="stepfunctions", help="Work with Step Functions resources")

from .state_machines import scan_state_machines, list_state_machines, import_state_machine
from .activities import scan_activities, list_activities, import_activity


@app.command("scan")
def scan(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory to save Terraform files"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile name"),
    region: str = typer.Option("us-east-1", "--region", "-r", help="AWS region"),
):
    """Scan Step Functions resources (state machines and activities) and generate Terraform code."""
    scan_state_machines(output_dir, profile, region)
    scan_activities(output_dir, profile, region)


@app.command("list")
def list_resources(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """List all scanned Step Functions resources."""
    typer.echo("Step Functions State Machines:")
    list_state_machines(output_dir)
    typer.echo("\nStep Functions Activities:")
    list_activities(output_dir)


@app.command("import-state-machine")
def import_machine(
    state_machine_arn: str = typer.Argument(..., help="ARN of the state machine to import"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """Import a specific Step Functions state machine into Terraform state."""
    import_state_machine(state_machine_arn, output_dir)


@app.command("import-activity")
def import_act(
    activity_arn: str = typer.Argument(..., help="ARN of the activity to import"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """Import a specific Step Functions activity into Terraform state."""
    import_activity(activity_arn, output_dir)


def register():
    """Register Step Functions scan functions with the cross-scan registry."""
    from terraback.utils.cross_scan_registry import register_scan_function
    from terraback.core.license import Tier

    register_scan_function(
        "aws_sfn_state_machines",
        scan_state_machines,
        tier=Tier.COMMUNITY
    )

    register_scan_function(
        "aws_sfn_activities",
        scan_activities,
        tier=Tier.COMMUNITY
    )
