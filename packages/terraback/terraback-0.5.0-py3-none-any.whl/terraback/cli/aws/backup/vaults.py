from pathlib import Path
from typing import Optional
from terraback.cli.aws.session import get_boto_session
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.aws.resource_processor import process_resources


def scan_backup_vaults(output_dir: Path, profile: Optional[str] = None, region: str = "us-east-1"):
    """
    Scans for AWS Backup vaults, plans, and selections and generates Terraform code.
    """
    boto_session = get_boto_session(profile, region)
    backup_client = boto_session.client("backup")

    print(f"Scanning for AWS Backup Vaults in region {region}...")

    # List all backup vaults
    vaults = []
    try:
        paginator = backup_client.get_paginator('list_backup_vaults')
        for page in paginator.paginate():
            vaults.extend(page.get('BackupVaultList', []))
    except Exception as e:
        print(f"Error listing backup vaults: {e}")
        return

    if not vaults:
        print("No AWS Backup vaults found")
        return

    print(f"Found {len(vaults)} AWS Backup vaults")

    # Process vaults
    detailed_vaults = process_resources(vaults, 'vaults')

    # Generate Terraform for vaults
    output_file = output_dir / "backup_vault.tf"
    generate_tf(detailed_vaults, "aws_backup_vault", output_file)
    print(f"Generated Terraform for {len(detailed_vaults)} Backup Vaults -> {output_file}")

    generate_imports_file(
        "backup_vault",
        detailed_vaults,
        remote_resource_id_key="BackupVaultName",
        output_dir=output_dir,
        provider="aws"
    )

    # Scan backup plans
    print(f"Scanning for AWS Backup Plans...")
    plans = []
    try:
        paginator = backup_client.get_paginator('list_backup_plans')
        for page in paginator.paginate():
            for plan_summary in page.get('BackupPlansList', []):
                try:
                    plan_response = backup_client.get_backup_plan(BackupPlanId=plan_summary['BackupPlanId'])
                    plan = plan_response['BackupPlan']
                    plan['BackupPlanId'] = plan_summary['BackupPlanId']
                    plan['VersionId'] = plan_summary.get('VersionId')
                    plans.append(plan)
                except Exception as e:
                    print(f"  - Could not get details for plan {plan_summary.get('BackupPlanName')}: {e}")
    except Exception as e:
        print(f"Error listing backup plans: {e}")

    if plans:
        detailed_plans = process_resources(plans, 'plans')
        output_file = output_dir / "backup_plan.tf"
        generate_tf(detailed_plans, "aws_backup_plan", output_file)
        print(f"Generated Terraform for {len(detailed_plans)} Backup Plans -> {output_file}")

        generate_imports_file(
            "backup_plan",
            detailed_plans,
            remote_resource_id_key="BackupPlanId",
            output_dir=output_dir,
            provider="aws"
        )

    # Scan backup selections
    print(f"Scanning for AWS Backup Selections...")
    selections = []
    for plan in plans:
        plan_id = plan['BackupPlanId']
        try:
            paginator = backup_client.get_paginator('list_backup_selections')
            for page in paginator.paginate(BackupPlanId=plan_id):
                for selection_summary in page.get('BackupSelectionsList', []):
                    try:
                        selection_response = backup_client.get_backup_selection(
                            BackupPlanId=plan_id,
                            SelectionId=selection_summary['SelectionId']
                        )
                        selection = selection_response['BackupSelection']
                        selection['SelectionId'] = selection_summary['SelectionId']
                        selection['BackupPlanId'] = plan_id
                        selections.append(selection)
                    except Exception as e:
                        print(f"  - Could not get selection details: {e}")
        except Exception as e:
            print(f"  - Error listing selections for plan {plan_id}: {e}")

    if selections:
        detailed_selections = process_resources(selections, 'selections')
        output_file = output_dir / "backup_selection.tf"
        generate_tf(detailed_selections, "aws_backup_selection", output_file)
        print(f"Generated Terraform for {len(detailed_selections)} Backup Selections -> {output_file}")

        # For selections, the import ID is plan_id|selection_id
        for selection in detailed_selections:
            selection['ImportId'] = f"{selection['BackupPlanId']}|{selection['SelectionId']}"

        generate_imports_file(
            "backup_selection",
            detailed_selections,
            remote_resource_id_key="ImportId",
            output_dir=output_dir,
            provider="aws"
        )


def list_backup_vaults(output_dir: Path):
    """Lists all AWS Backup Vault resources previously generated."""
    ImportManager(output_dir, "backup_vault").list_all()


def import_backup_vault(vault_name: str, output_dir: Path):
    """Runs terraform import for a specific AWS Backup Vault by its name."""
    ImportManager(output_dir, "backup_vault").find_and_import(vault_name)
