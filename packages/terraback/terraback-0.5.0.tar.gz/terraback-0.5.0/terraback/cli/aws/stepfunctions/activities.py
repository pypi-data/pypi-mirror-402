from pathlib import Path
from typing import Optional
from terraback.cli.aws.session import get_boto_session
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.aws.resource_processor import process_resources


def scan_activities(output_dir: Path, profile: Optional[str] = None, region: str = "us-east-1"):
    """
    Scans for Step Functions activities and generates Terraform code.
    """
    boto_session = get_boto_session(profile, region)
    sfn_client = boto_session.client("stepfunctions")

    print(f"Scanning for Step Functions Activities in region {region}...")

    # List all activities with pagination
    activities = []
    paginator = sfn_client.get_paginator('list_activities')

    for page in paginator.paginate():
        activities.extend(page['activities'])

    if not activities:
        print("No Step Functions activities found")
        return

    print(f"Found {len(activities)} Step Functions activities")

    # Get detailed information for each activity
    detailed_activities = []
    for activity in activities:
        activity_arn = activity['activityArn']

        try:
            # Get activity details
            response = sfn_client.describe_activity(
                activityArn=activity_arn
            )

            # Get tags
            try:
                tags_response = sfn_client.list_tags_for_resource(
                    resourceArn=activity_arn
                )
                if tags_response.get('tags'):
                    response['Tags'] = {tag['key']: tag['value'] for tag in tags_response['tags']}
            except Exception as e:
                print(f"  - Could not get tags for activity {activity['name']}: {e}")

            detailed_activities.append(response)

        except Exception as e:
            print(f"  - Could not retrieve details for activity {activity['name']}: {e}")
            continue

    # Process resources to ensure proper naming
    detailed_activities = process_resources(detailed_activities, 'activities')

    # Generate Terraform files
    output_file = output_dir / "sfn_activity.tf"
    generate_tf(detailed_activities, "aws_sfn_activity", output_file)
    print(f"Generated Terraform for {len(detailed_activities)} Step Functions Activities -> {output_file}")

    # Generate import file
    generate_imports_file(
        "sfn_activity",
        detailed_activities,
        remote_resource_id_key="activityArn",
        output_dir=output_dir,
        provider="aws"
    )


def list_activities(output_dir: Path):
    """Lists all Step Functions Activity resources previously generated."""
    ImportManager(output_dir, "sfn_activity").list_all()


def import_activity(activity_arn: str, output_dir: Path):
    """Runs terraform import for a specific Step Functions Activity by its ARN."""
    ImportManager(output_dir, "sfn_activity").find_and_import(activity_arn)
