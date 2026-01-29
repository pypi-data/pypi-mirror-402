import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(name="eventbridge", help="Work with EventBridge resources")

from .event_buses import scan_event_buses, list_event_buses, import_event_bus
from .rules import scan_event_rules, list_event_rules, import_event_rule, list_event_targets, import_event_target


@app.command("scan")
def scan(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory to save Terraform files"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile name"),
    region: str = typer.Option("us-east-1", "--region", "-r", help="AWS region"),
):
    """Scan EventBridge resources (buses, rules, targets) and generate Terraform code."""
    scan_event_buses(output_dir, profile, region)
    scan_event_rules(output_dir, profile, region)


@app.command("list")
def list_resources(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """List all scanned EventBridge resources."""
    typer.echo("EventBridge Event Buses:")
    list_event_buses(output_dir)
    typer.echo("\nEventBridge Rules:")
    list_event_rules(output_dir)
    typer.echo("\nEventBridge Targets:")
    list_event_targets(output_dir)


@app.command("import-bus")
def import_bus(
    bus_name: str = typer.Argument(..., help="Name of the event bus to import"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """Import a specific EventBridge event bus into Terraform state."""
    import_event_bus(bus_name, output_dir)


@app.command("import-rule")
def import_rule(
    rule_name: str = typer.Argument(..., help="Name of the rule to import"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """Import a specific EventBridge rule into Terraform state."""
    import_event_rule(rule_name, output_dir)


@app.command("import-target")
def import_target(
    rule_target_id: str = typer.Argument(..., help="Rule and target ID (format: rule-name/target-id)"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files"),
):
    """Import a specific EventBridge target into Terraform state."""
    import_event_target(rule_target_id, output_dir)


def register():
    """Register EventBridge scan functions with the cross-scan registry."""
    from terraback.utils.cross_scan_registry import register_scan_function
    from terraback.core.license import Tier

    register_scan_function(
        "aws_eventbridge_event_buses",
        scan_event_buses,
        tier=Tier.COMMUNITY
    )

    register_scan_function(
        "aws_eventbridge_rules",
        scan_event_rules,
        tier=Tier.COMMUNITY
    )
