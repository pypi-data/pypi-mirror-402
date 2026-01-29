from pathlib import Path
from typing import Optional
from terraback.cli.aws.session import get_boto_session
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.aws.resource_processor import process_resources


def scan_cloudtrail_trails(output_dir: Path, profile: Optional[str] = None, region: str = "us-east-1"):
    """
    Scans for CloudTrail trails and generates Terraform code.
    """
    boto_session = get_boto_session(profile, region)
    cloudtrail_client = boto_session.client("cloudtrail")

    print(f"Scanning for CloudTrail Trails in region {region}...")

    # List all trails
    try:
        response = cloudtrail_client.list_trails()
        trails = response.get('Trails', [])
    except Exception as e:
        print(f"Error listing CloudTrail trails: {e}")
        return

    if not trails:
        print("No CloudTrail trails found")
        return

    trail_names = [trail['Name'] for trail in trails]
    print(f"Found {len(trail_names)} CloudTrail trails")

    # Get detailed information for each trail
    detailed_trails = []
    for trail_name in trail_names:
        try:
            # Get trail details
            response = cloudtrail_client.describe_trails(trailNameList=[trail_name])
            if response.get('trailList'):
                trail = response['trailList'][0]

                # Get trail status
                try:
                    status_response = cloudtrail_client.get_trail_status(Name=trail_name)
                    trail['IsLogging'] = status_response.get('IsLogging', False)
                except Exception as e:
                    print(f"  - Could not get status for trail {trail_name}: {e}")
                    trail['IsLogging'] = False

                # Get event selectors
                try:
                    selectors_response = cloudtrail_client.get_event_selectors(TrailName=trail_name)
                    if selectors_response.get('EventSelectors'):
                        trail['EventSelectors'] = selectors_response['EventSelectors']
                except Exception as e:
                    print(f"  - Could not get event selectors for trail {trail_name}: {e}")

                # Get tags
                try:
                    tags_response = cloudtrail_client.list_tags(ResourceIdList=[trail['TrailARN']])
                    if tags_response.get('ResourceTagList'):
                        tag_list = tags_response['ResourceTagList'][0].get('TagsList', [])
                        trail['Tags'] = {tag['Key']: tag['Value'] for tag in tag_list}
                except Exception as e:
                    print(f"  - Could not get tags for trail {trail_name}: {e}")

                detailed_trails.append(trail)

        except Exception as e:
            print(f"  - Could not retrieve details for trail {trail_name}: {e}")
            continue

    # Process resources to ensure proper naming
    detailed_trails = process_resources(detailed_trails, 'trails')

    # Generate Terraform files
    output_file = output_dir / "cloudtrail.tf"
    generate_tf(detailed_trails, "aws_cloudtrail", output_file)
    print(f"Generated Terraform for {len(detailed_trails)} CloudTrail Trails -> {output_file}")

    # Generate import file
    generate_imports_file(
        "cloudtrail",
        detailed_trails,
        remote_resource_id_key="Name",
        output_dir=output_dir,
        provider="aws"
    )


def list_cloudtrail_trails(output_dir: Path):
    """Lists all CloudTrail Trail resources previously generated."""
    ImportManager(output_dir, "cloudtrail").list_all()


def import_cloudtrail_trail(trail_name: str, output_dir: Path):
    """Runs terraform import for a specific CloudTrail Trail by its name."""
    ImportManager(output_dir, "cloudtrail").find_and_import(trail_name)
