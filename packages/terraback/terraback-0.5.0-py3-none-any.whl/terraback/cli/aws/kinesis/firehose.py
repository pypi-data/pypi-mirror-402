from pathlib import Path
from typing import Optional
from terraback.cli.aws.session import get_boto_session
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.aws.resource_processor import process_resources


def scan_firehose_delivery_streams(output_dir: Path, profile: Optional[str] = None, region: str = "us-east-1"):
    """
    Scans for Kinesis Firehose Delivery Streams and generates Terraform code.
    """
    boto_session = get_boto_session(profile, region)
    firehose_client = boto_session.client("firehose")

    print(f"Scanning for Kinesis Firehose Delivery Streams in region {region}...")

    # List all delivery streams
    try:
        response = firehose_client.list_delivery_streams(
            Limit=100
        )
        stream_names = response.get('DeliveryStreamNames', [])

        # Handle pagination if there are more than 100 streams
        while response.get('HasMoreDeliveryStreams', False):
            response = firehose_client.list_delivery_streams(
                Limit=100,
                ExclusiveStartDeliveryStreamName=stream_names[-1]
            )
            stream_names.extend(response.get('DeliveryStreamNames', []))

    except Exception as e:
        print(f"Error listing Firehose delivery streams: {e}")
        return

    if not stream_names:
        print("No Kinesis Firehose delivery streams found")
        return

    print(f"Found {len(stream_names)} Kinesis Firehose delivery streams")

    # Get detailed information for each delivery stream
    detailed_streams = []
    for stream_name in stream_names:
        try:
            # Get delivery stream description
            response = firehose_client.describe_delivery_stream(
                DeliveryStreamName=stream_name
            )
            stream_desc = response['DeliveryStreamDescription']

            # Get tags
            try:
                tags_response = firehose_client.list_tags_for_delivery_stream(
                    DeliveryStreamName=stream_name
                )
                if tags_response.get('Tags'):
                    stream_desc['Tags'] = {tag['Key']: tag['Value'] for tag in tags_response['Tags']}
            except Exception as e:
                print(f"  - Could not get tags for delivery stream {stream_name}: {e}")

            detailed_streams.append(stream_desc)

        except Exception as e:
            print(f"  - Could not retrieve details for delivery stream {stream_name}: {e}")
            continue

    # Process resources to ensure proper naming
    detailed_streams = process_resources(detailed_streams, 'delivery_streams')

    # Generate Terraform files
    output_file = output_dir / "kinesis_firehose_delivery_stream.tf"
    generate_tf(detailed_streams, "aws_kinesis_firehose_delivery_stream", output_file)
    print(f"Generated Terraform for {len(detailed_streams)} Kinesis Firehose Delivery Streams -> {output_file}")

    # Generate import file
    generate_imports_file(
        "kinesis_firehose_delivery_stream",
        detailed_streams,
        remote_resource_id_key="DeliveryStreamName",
        output_dir=output_dir,
        provider="aws"
    )


def list_firehose_delivery_streams(output_dir: Path):
    """Lists all Kinesis Firehose Delivery Stream resources previously generated."""
    ImportManager(output_dir, "kinesis_firehose_delivery_stream").list_all()


def import_firehose_delivery_stream(stream_name: str, output_dir: Path):
    """Runs terraform import for a specific Kinesis Firehose Delivery Stream by its name."""
    ImportManager(output_dir, "kinesis_firehose_delivery_stream").find_and_import(stream_name)
