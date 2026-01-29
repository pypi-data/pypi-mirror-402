from pathlib import Path
from typing import Optional
from terraback.cli.aws.session import get_boto_session
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.aws.resource_processor import process_resources


def scan_event_buses(output_dir: Path, profile: Optional[str] = None, region: str = "us-east-1"):
    """
    Scans for EventBridge event buses (excluding default) and generates Terraform code.
    """
    boto_session = get_boto_session(profile, region)
    events_client = boto_session.client("events")

    print(f"Scanning for EventBridge Event Buses in region {region}...")

    # List all event buses
    try:
        response = events_client.list_event_buses()
        event_buses = response.get('EventBuses', [])
    except Exception as e:
        print(f"Error listing event buses: {e}")
        return

    # Filter out the default event bus (not managed by Terraform typically)
    custom_buses = []
    for bus in event_buses:
        bus_name = bus.get('Name', '')

        # Skip default bus
        if bus_name == 'default':
            continue

        # Get tags for the bus
        try:
            tags_response = events_client.list_tags_for_resource(
                ResourceARN=bus['Arn']
            )
            if tags_response.get('Tags'):
                bus['Tags'] = {tag['Key']: tag['Value'] for tag in tags_response['Tags']}
        except Exception as e:
            print(f"  - Could not get tags for event bus {bus_name}: {e}")

        custom_buses.append(bus)

    if not custom_buses:
        print("No custom EventBridge event buses found (default bus excluded)")
        return

    # Process resources to ensure proper naming
    custom_buses = process_resources(custom_buses, 'event_buses')

    # Generate Terraform files
    output_file = output_dir / "eventbridge_event_bus.tf"
    generate_tf(custom_buses, "aws_cloudwatch_event_bus", output_file)
    print(f"Generated Terraform for {len(custom_buses)} EventBridge Event Buses -> {output_file}")

    # Generate import file
    generate_imports_file(
        "eventbridge_event_bus",
        custom_buses,
        remote_resource_id_key="Name",
        output_dir=output_dir,
        provider="aws"
    )


def list_event_buses(output_dir: Path):
    """Lists all EventBridge Event Bus resources previously generated."""
    ImportManager(output_dir, "eventbridge_event_bus").list_all()


def import_event_bus(bus_name: str, output_dir: Path):
    """Runs terraform import for a specific EventBridge Event Bus by its name."""
    ImportManager(output_dir, "eventbridge_event_bus").find_and_import(bus_name)
