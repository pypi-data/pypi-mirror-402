from pathlib import Path
from typing import Optional, List, Dict, Any
from terraback.cli.aws.session import get_boto_session
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.aws.resource_processor import process_resources


def scan_event_rules(output_dir: Path, profile: Optional[str] = None, region: str = "us-east-1"):
    """
    Scans for EventBridge rules and their targets, generates Terraform code.
    """
    boto_session = get_boto_session(profile, region)
    events_client = boto_session.client("events")

    print(f"Scanning for EventBridge Rules in region {region}...")

    # Get all event buses first
    try:
        buses_response = events_client.list_event_buses()
        event_buses = buses_response.get('EventBuses', [])
    except Exception as e:
        print(f"Error listing event buses: {e}")
        return

    all_rules = []
    all_targets = []

    # Scan rules for each event bus
    for bus in event_buses:
        bus_name = bus.get('Name', 'default')

        try:
            # List rules with pagination
            paginator = events_client.get_paginator('list_rules')

            for page in paginator.paginate(EventBusName=bus_name):
                for rule in page['Rules']:
                    rule_name = rule['Name']

                    try:
                        # Get detailed rule information
                        detailed_rule = events_client.describe_rule(
                            Name=rule_name,
                            EventBusName=bus_name
                        )

                        # Add event bus name to the rule
                        detailed_rule['EventBusName'] = bus_name

                        # Get tags for the rule
                        try:
                            tags_response = events_client.list_tags_for_resource(
                                ResourceARN=detailed_rule['Arn']
                            )
                            if tags_response.get('Tags'):
                                detailed_rule['Tags'] = {tag['Key']: tag['Value'] for tag in tags_response['Tags']}
                        except Exception as e:
                            print(f"  - Could not get tags for rule {rule_name}: {e}")

                        all_rules.append(detailed_rule)

                        # Get targets for this rule
                        try:
                            targets_response = events_client.list_targets_by_rule(
                                Rule=rule_name,
                                EventBusName=bus_name
                            )

                            for target in targets_response.get('Targets', []):
                                target['Rule'] = rule_name
                                target['EventBusName'] = bus_name
                                all_targets.append(target)

                        except Exception as e:
                            print(f"  - Could not get targets for rule {rule_name}: {e}")

                    except Exception as e:
                        print(f"  - Could not retrieve details for rule {rule_name}: {e}")
                        continue

        except Exception as e:
            print(f"  - Error scanning rules for bus {bus_name}: {e}")
            continue

    # Process resources
    all_rules = process_resources(all_rules, 'rules')
    all_targets = process_resources(all_targets, 'targets')

    # Generate Terraform for rules
    if all_rules:
        output_file = output_dir / "eventbridge_rule.tf"
        generate_tf(all_rules, "aws_cloudwatch_event_rule", output_file)
        print(f"Generated Terraform for {len(all_rules)} EventBridge Rules -> {output_file}")

        # For rules, the import ID format depends on the event bus:
        # - Default bus: rule-name
        # - Non-default bus: event-bus-name/rule-name
        for rule in all_rules:
            event_bus = rule.get('EventBusName', 'default')
            if event_bus == 'default':
                rule['ImportId'] = rule['Name']
            else:
                rule['ImportId'] = f"{event_bus}/{rule['Name']}"

        generate_imports_file(
            "eventbridge_rule",
            all_rules,
            remote_resource_id_key="ImportId",
            output_dir=output_dir,
            provider="aws"
        )

    # Generate Terraform for targets
    if all_targets:
        output_file = output_dir / "eventbridge_target.tf"
        generate_tf(all_targets, "aws_cloudwatch_event_target", output_file)
        print(f"Generated Terraform for {len(all_targets)} EventBridge Targets -> {output_file}")

        # For targets, the import ID format depends on the event bus:
        # - Default bus: rule-name/target-id
        # - Non-default bus: event-bus-name/rule-name/target-id
        for target in all_targets:
            event_bus = target.get('EventBusName', 'default')
            if event_bus == 'default':
                target['ImportId'] = f"{target['Rule']}/{target['Id']}"
            else:
                target['ImportId'] = f"{event_bus}/{target['Rule']}/{target['Id']}"

        generate_imports_file(
            "eventbridge_target",
            all_targets,
            remote_resource_id_key="ImportId",
            output_dir=output_dir,
            provider="aws"
        )


def list_event_rules(output_dir: Path):
    """Lists all EventBridge Rule resources previously generated."""
    ImportManager(output_dir, "eventbridge_rule").list_all()


def import_event_rule(rule_name: str, output_dir: Path):
    """Runs terraform import for a specific EventBridge Rule by its name."""
    ImportManager(output_dir, "eventbridge_rule").find_and_import(rule_name)


def list_event_targets(output_dir: Path):
    """Lists all EventBridge Target resources previously generated."""
    ImportManager(output_dir, "eventbridge_target").list_all()


def import_event_target(rule_target_id: str, output_dir: Path):
    """Runs terraform import for a specific EventBridge Target by rule-name/target-id."""
    ImportManager(output_dir, "eventbridge_target").find_and_import(rule_target_id)
