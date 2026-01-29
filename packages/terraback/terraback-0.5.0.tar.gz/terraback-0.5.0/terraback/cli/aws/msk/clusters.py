from pathlib import Path
from typing import Optional
from terraback.cli.aws.session import get_boto_session
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.aws.resource_processor import process_resources


def scan_msk_clusters(output_dir: Path, profile: Optional[str] = None, region: str = "us-east-1"):
    """
    Scans for MSK (Managed Streaming for Kafka) clusters and generates Terraform code.
    """
    boto_session = get_boto_session(profile, region)
    kafka_client = boto_session.client("kafka")

    print(f"Scanning for MSK Clusters in region {region}...")

    # List all clusters with pagination
    cluster_arns = []
    paginator = kafka_client.get_paginator('list_clusters_v2')

    for page in paginator.paginate():
        for cluster in page.get('ClusterInfoList', []):
            cluster_arns.append(cluster['ClusterArn'])

    if not cluster_arns:
        print("No MSK clusters found")
        return

    print(f"Found {len(cluster_arns)} MSK clusters")

    # Get detailed information for each cluster
    detailed_clusters = []
    for cluster_arn in cluster_arns:
        try:
            # Get cluster details
            response = kafka_client.describe_cluster_v2(ClusterArn=cluster_arn)
            cluster = response['ClusterInfo']

            # Get tags
            try:
                tags_response = kafka_client.list_tags_for_resource(ResourceArn=cluster_arn)
                if tags_response.get('Tags'):
                    cluster['Tags'] = tags_response['Tags']
            except Exception as e:
                print(f"  - Could not get tags for cluster {cluster.get('ClusterName')}: {e}")

            detailed_clusters.append(cluster)

        except Exception as e:
            print(f"  - Could not retrieve details for cluster {cluster_arn}: {e}")
            continue

    # Process resources to ensure proper naming
    detailed_clusters = process_resources(detailed_clusters, 'clusters')

    # Generate Terraform files
    output_file = output_dir / "msk_cluster.tf"
    generate_tf(detailed_clusters, "aws_msk_cluster", output_file)
    print(f"Generated Terraform for {len(detailed_clusters)} MSK Clusters -> {output_file}")

    # Generate import file
    generate_imports_file(
        "msk_cluster",
        detailed_clusters,
        remote_resource_id_key="ClusterArn",
        output_dir=output_dir,
        provider="aws"
    )


def list_msk_clusters(output_dir: Path):
    """Lists all MSK Cluster resources previously generated."""
    ImportManager(output_dir, "msk_cluster").list_all()


def import_msk_cluster(cluster_arn: str, output_dir: Path):
    """Runs terraform import for a specific MSK Cluster by its ARN."""
    ImportManager(output_dir, "msk_cluster").find_and_import(cluster_arn)
