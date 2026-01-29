from pathlib import Path
from typing import Optional
from terraback.cli.aws.session import get_boto_session
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.aws.resource_processor import process_resources


def scan_guardduty_detectors(output_dir: Path, profile: Optional[str] = None, region: str = "us-east-1"):
    """
    Scans for GuardDuty detectors and generates Terraform code.
    """
    boto_session = get_boto_session(profile, region)
    guardduty_client = boto_session.client("guardduty")

    print(f"Scanning for GuardDuty Detectors in region {region}...")

    # List all detectors
    try:
        response = guardduty_client.list_detectors()
        detector_ids = response.get('DetectorIds', [])
    except Exception as e:
        print(f"Error listing GuardDuty detectors: {e}")
        return

    if not detector_ids:
        print("No GuardDuty detectors found")
        return

    print(f"Found {len(detector_ids)} GuardDuty detectors")

    # Get detailed information for each detector
    detailed_detectors = []
    for detector_id in detector_ids:
        try:
            # Get detector details
            response = guardduty_client.get_detector(DetectorId=detector_id)
            detector = response.copy()
            detector['DetectorId'] = detector_id

            # Get tags
            try:
                tags_response = guardduty_client.list_tags_for_resource(
                    ResourceArn=f"arn:aws:guardduty:{region}:{boto_session.client('sts').get_caller_identity()['Account']}:detector/{detector_id}"
                )
                if tags_response.get('Tags'):
                    detector['Tags'] = tags_response['Tags']
            except Exception as e:
                print(f"  - Could not get tags for detector {detector_id}: {e}")

            detailed_detectors.append(detector)

        except Exception as e:
            print(f"  - Could not retrieve details for detector {detector_id}: {e}")
            continue

    # Process resources to ensure proper naming
    detailed_detectors = process_resources(detailed_detectors, 'detectors')

    # Generate Terraform files
    output_file = output_dir / "guardduty_detector.tf"
    generate_tf(detailed_detectors, "aws_guardduty_detector", output_file)
    print(f"Generated Terraform for {len(detailed_detectors)} GuardDuty Detectors -> {output_file}")

    # Generate import file
    generate_imports_file(
        "aws_guardduty_detector",
        detailed_detectors,
        remote_resource_id_key="DetectorId",
        output_dir=output_dir,
        provider="aws"
    )


def list_guardduty_detectors(output_dir: Path):
    """Lists all GuardDuty Detector resources previously generated."""
    ImportManager(output_dir, "guardduty_detector").list_all()


def import_guardduty_detector(detector_id: str, output_dir: Path):
    """Runs terraform import for a specific GuardDuty Detector by its ID."""
    ImportManager(output_dir, "guardduty_detector").find_and_import(detector_id)
