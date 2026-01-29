from pathlib import Path
from typing import Optional
from terraback.cli.aws.session import get_boto_session
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.aws.resource_processor import process_resources


def scan_kinesis_streams(output_dir: Path, profile: Optional[str] = None, region: str = "us-east-1"):
    """
    Scans for Kinesis Data Streams and generates Terraform code.
    """
    boto_session = get_boto_session(profile, region)
    kinesis_client = boto_session.client("kinesis")

    print(f"Scanning for Kinesis Data Streams in region {region}...")

    # List all streams with pagination
    stream_names = []
    paginator = kinesis_client.get_paginator('list_streams')

    for page in paginator.paginate():
        stream_names.extend(page['StreamNames'])

    if not stream_names:
        print("No Kinesis streams found")
        return

    print(f"Found {len(stream_names)} Kinesis streams")

    # Get detailed information for each stream
    detailed_streams = []
    for stream_name in stream_names:
        try:
            # Get stream description
            response = kinesis_client.describe_stream(
                StreamName=stream_name
            )
            stream_desc = response['StreamDescription']

            # Get tags
            try:
                tags_response = kinesis_client.list_tags_for_stream(
                    StreamName=stream_name
                )
                if tags_response.get('Tags'):
                    stream_desc['Tags'] = {tag['Key']: tag['Value'] for tag in tags_response['Tags']}
            except Exception as e:
                print(f"  - Could not get tags for stream {stream_name}: {e}")

            # Get stream summary (for enhanced monitoring and encryption)
            try:
                summary_response = kinesis_client.describe_stream_summary(
                    StreamName=stream_name
                )
                if summary_response.get('StreamDescriptionSummary'):
                    summary = summary_response['StreamDescriptionSummary']
                    # Add encryption info
                    if 'EncryptionType' in summary:
                        stream_desc['EncryptionType'] = summary['EncryptionType']
                    if 'KeyId' in summary:
                        stream_desc['KeyId'] = summary['KeyId']
                    # Add enhanced monitoring
                    if 'EnhancedMonitoring' in summary:
                        stream_desc['EnhancedMonitoring'] = summary['EnhancedMonitoring']
            except Exception as e:
                print(f"  - Could not get summary for stream {stream_name}: {e}")

            detailed_streams.append(stream_desc)

        except Exception as e:
            print(f"  - Could not retrieve details for stream {stream_name}: {e}")
            continue

    # Process resources to ensure proper naming
    detailed_streams = process_resources(detailed_streams, 'streams')

    # Generate Terraform files
    output_file = output_dir / "kinesis_stream.tf"
    generate_tf(detailed_streams, "aws_kinesis_stream", output_file)
    print(f"Generated Terraform for {len(detailed_streams)} Kinesis Streams -> {output_file}")

    # Generate import file
    generate_imports_file(
        "aws_kinesis_stream",
        detailed_streams,
        remote_resource_id_key="StreamName",
        output_dir=output_dir,
        provider="aws"
    )


def list_kinesis_streams(output_dir: Path):
    """Lists all Kinesis Stream resources previously generated."""
    ImportManager(output_dir, "kinesis_stream").list_all()


def import_kinesis_stream(stream_name: str, output_dir: Path):
    """Runs terraform import for a specific Kinesis Stream by its name."""
    ImportManager(output_dir, "kinesis_stream").find_and_import(stream_name)
