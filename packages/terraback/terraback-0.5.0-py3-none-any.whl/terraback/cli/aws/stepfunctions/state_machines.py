from pathlib import Path
from typing import Optional
from terraback.cli.aws.session import get_boto_session
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.aws.resource_processor import process_resources


def scan_state_machines(output_dir: Path, profile: Optional[str] = None, region: str = "us-east-1"):
    """
    Scans for Step Functions state machines and generates Terraform code.
    """
    boto_session = get_boto_session(profile, region)
    sfn_client = boto_session.client("stepfunctions")

    print(f"Scanning for Step Functions State Machines in region {region}...")

    # List all state machines with pagination
    state_machines = []
    paginator = sfn_client.get_paginator('list_state_machines')

    for page in paginator.paginate():
        state_machines.extend(page['stateMachines'])

    if not state_machines:
        print("No Step Functions state machines found")
        return

    print(f"Found {len(state_machines)} Step Functions state machines")

    # Get detailed information for each state machine
    detailed_machines = []
    for machine in state_machines:
        machine_arn = machine['stateMachineArn']

        try:
            # Get state machine details
            response = sfn_client.describe_state_machine(
                stateMachineArn=machine_arn
            )

            # Get tags
            try:
                tags_response = sfn_client.list_tags_for_resource(
                    resourceArn=machine_arn
                )
                if tags_response.get('tags'):
                    response['Tags'] = {tag['key']: tag['value'] for tag in tags_response['tags']}
            except Exception as e:
                print(f"  - Could not get tags for state machine {machine['name']}: {e}")

            detailed_machines.append(response)

        except Exception as e:
            print(f"  - Could not retrieve details for state machine {machine['name']}: {e}")
            continue

    # Process resources to ensure proper naming
    detailed_machines = process_resources(detailed_machines, 'state_machines')

    # Generate Terraform files
    output_file = output_dir / "sfn_state_machine.tf"
    generate_tf(detailed_machines, "aws_sfn_state_machine", output_file)
    print(f"Generated Terraform for {len(detailed_machines)} Step Functions State Machines -> {output_file}")

    # Generate import file
    generate_imports_file(
        "sfn_state_machine",
        detailed_machines,
        remote_resource_id_key="stateMachineArn",
        output_dir=output_dir,
        provider="aws"
    )


def list_state_machines(output_dir: Path):
    """Lists all Step Functions State Machine resources previously generated."""
    ImportManager(output_dir, "sfn_state_machine").list_all()


def import_state_machine(state_machine_arn: str, output_dir: Path):
    """Runs terraform import for a specific Step Functions State Machine by its ARN."""
    ImportManager(output_dir, "sfn_state_machine").find_and_import(state_machine_arn)
