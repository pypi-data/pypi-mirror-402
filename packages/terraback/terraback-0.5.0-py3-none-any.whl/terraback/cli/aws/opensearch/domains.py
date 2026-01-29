from pathlib import Path
from typing import Optional
from terraback.cli.aws.session import get_boto_session
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.aws.resource_processor import process_resources


def scan_opensearch_domains(output_dir: Path, profile: Optional[str] = None, region: str = "us-east-1"):
    """
    Scans for OpenSearch domains and generates Terraform code.
    """
    boto_session = get_boto_session(profile, region)
    opensearch_client = boto_session.client("opensearch")

    print(f"Scanning for OpenSearch Domains in region {region}...")

    # List all domain names
    try:
        response = opensearch_client.list_domain_names()
        domain_names = [domain['DomainName'] for domain in response.get('DomainNames', [])]
    except Exception as e:
        print(f"Error listing OpenSearch domains: {e}")
        return

    if not domain_names:
        print("No OpenSearch domains found")
        return

    print(f"Found {len(domain_names)} OpenSearch domains")

    # Get detailed information for each domain
    detailed_domains = []
    for domain_name in domain_names:
        try:
            # Get domain status
            response = opensearch_client.describe_domain(DomainName=domain_name)
            domain = response['DomainStatus']

            # Get tags
            try:
                tags_response = opensearch_client.list_tags(ARN=domain['ARN'])
                if tags_response.get('TagList'):
                    domain['Tags'] = {tag['Key']: tag['Value'] for tag in tags_response['TagList']}
            except Exception as e:
                print(f"  - Could not get tags for domain {domain_name}: {e}")

            detailed_domains.append(domain)

        except Exception as e:
            print(f"  - Could not retrieve details for domain {domain_name}: {e}")
            continue

    # Process resources to ensure proper naming
    detailed_domains = process_resources(detailed_domains, 'domains')

    # Generate Terraform files
    output_file = output_dir / "opensearch_domain.tf"
    generate_tf(detailed_domains, "aws_opensearch_domain", output_file)
    print(f"Generated Terraform for {len(detailed_domains)} OpenSearch Domains -> {output_file}")

    # Generate import file
    generate_imports_file(
        "opensearch_domain",
        detailed_domains,
        remote_resource_id_key="DomainName",
        output_dir=output_dir,
        provider="aws"
    )


def list_opensearch_domains(output_dir: Path):
    """Lists all OpenSearch Domain resources previously generated."""
    ImportManager(output_dir, "opensearch_domain").list_all()


def import_opensearch_domain(domain_name: str, output_dir: Path):
    """Runs terraform import for a specific OpenSearch Domain by its name."""
    ImportManager(output_dir, "opensearch_domain").find_and_import(domain_name)
