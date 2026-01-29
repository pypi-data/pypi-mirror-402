from pathlib import Path
import json
from terraback.cli.aws.session import get_boto_session
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager

def scan_policies(output_dir: Path, profile: str = None, region: str = "us-east-1"):
    boto_session = get_boto_session(profile, region)
    iam_client = boto_session.client("iam")

    paginator = iam_client.get_paginator("list_policies")
    policies = []
    
    # We only want to scan customer-managed policies ('Local')
    for page in paginator.paginate(Scope='Local'):
        for policy_meta in page['Policies']:
            # For each policy, we must get its default version to find the policy document
            try:
                version_data = iam_client.get_policy_version(
                    PolicyArn=policy_meta["Arn"],
                    VersionId=policy_meta["DefaultVersionId"],
                )

                # Fetch additional details like description
                policy_details = iam_client.get_policy(PolicyArn=policy_meta["Arn"])
                policy_meta["Description"] = policy_details.get("Policy", {}).get("Description")

                # Fetch tags if available
                try:
                    tags_data = iam_client.list_policy_tags(PolicyArn=policy_meta["Arn"])
                except Exception:
                    tags_data = iam_client.list_tags_for_resource(ResourceArn=policy_meta["Arn"])
                policy_meta["Tags"] = tags_data.get("Tags", [])

                # Add the policy document to our policy object
                policy_meta["PolicyDocument"] = json.dumps(
                    version_data["PolicyVersion"]["Document"], indent=2
                )
                policies.append(policy_meta)
            except Exception as e:
                print(
                    f"Could not retrieve details for policy {policy_meta['Arn']}: {e}"
                )

    output_file = output_dir / "iam_policies.tf"
    generate_tf(policies, "aws_iam_policies", output_file)
    print(f"Generated Terraform for {len(policies)} IAM Policies -> {output_file}")
    generate_imports_file("iam_policy", policies, remote_resource_id_key="Arn", output_dir=output_dir, provider="aws")

def list_policies(output_dir: Path):
    ImportManager(output_dir, "iam_policy").list_all()

def import_policy(policy_arn: str, output_dir: Path):
    ImportManager(output_dir, "iam_policy").find_and_import(policy_arn)
