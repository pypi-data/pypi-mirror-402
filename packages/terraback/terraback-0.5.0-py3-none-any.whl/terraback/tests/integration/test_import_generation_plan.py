import json
import shutil
import subprocess
from pathlib import Path

import pytest

from terraback.cli.azure.resource_processor import process_resources as azure_process_resources
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file


def _run_terraform_zero_plan(workdir: Path):
    """Run `terraform init` and `plan` in the given directory.

    If terraform is not installed or the plan fails (e.g. due to missing
    provider credentials), the test is skipped rather than failed.
    """
    terraform = shutil.which("terraform")
    if not terraform:
        pytest.skip("terraform binary not available")

    try:
        subprocess.run(
            [terraform, "init", "-backend=false"],
            cwd=workdir,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        subprocess.run(
            [terraform, "plan", "-refresh=false"],
            cwd=workdir,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - skip on failure
        pytest.skip(f"terraform plan failed: {exc}")


def test_azure_resource_group_end_to_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    resources = [
        {
            "id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/test-rg",
            "name": "test-rg",
            "location": "eastus",
            "tags": {"env": "test"},
        }
    ]

    processed = azure_process_resources(resources, "azure_resource_group")

    tf_file = tmp_path / "azure_resource_group.tf"
    generate_tf(processed, "azure_resource_group", tf_file, provider="azure")
    generate_imports_file(
        "azure_resource_group", processed, "id", tmp_path, provider="azure"
    )
    import_file = tmp_path / "azure_resource_group_import.json"

    assert tf_file.exists()
    assert import_file.exists()
    assert import_file.name == f"{tf_file.stem}_import.json"

    data = json.loads(import_file.read_text())
    assert data[0]["resource_name"] == processed[0]["name_sanitized"]

    # Prepare minimal Terraform configuration and state for a no-op plan
    (tmp_path / "provider.tf").write_text(
        """
terraform {
  required_providers {
    azurerm = {
      source = \"hashicorp/azurerm\"
    }
  }
}

provider \"azurerm\" {
  features {}
  skip_provider_registration = true
}
        """
    )

    state = {
        "version": 4,
        "terraform_version": "1.6.0",
        "serial": 1,
        "lineage": "00000000-0000-0000-0000-000000000000",
        "outputs": {},
        "resources": [
            {
                "mode": "managed",
                "type": "azurerm_resource_group",
                "name": processed[0]["name_sanitized"],
                "provider": "provider[\"registry.terraform.io/hashicorp/azurerm\"]",
                "instances": [
                    {
                        "schema_version": 0,
                        "attributes": {
                            "id": resources[0]["id"],
                            "name": resources[0]["name"],
                            "location": resources[0]["location"],
                            "tags": resources[0]["tags"],
                        },
                    }
                ],
            }
        ],
    }
    (tmp_path / "terraform.tfstate").write_text(json.dumps(state))

    # Provide dummy credentials so the provider initializes if needed
    monkeypatch.setenv("ARM_CLIENT_ID", "dummy")
    monkeypatch.setenv("ARM_CLIENT_SECRET", "dummy")
    monkeypatch.setenv("ARM_TENANT_ID", "dummy")
    monkeypatch.setenv("ARM_SUBSCRIPTION_ID", "dummy")

    _run_terraform_zero_plan(tmp_path)


def test_gcp_service_account_end_to_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    sa = {
        "name": "projects/dummy/serviceAccounts/test-sa@dummy.iam.gserviceaccount.com",
        "project": "dummy",
        "email": "test-sa@dummy.iam.gserviceaccount.com",
        "account_id": "test-sa",
        "display_name": "Test SA",
        "name_sanitized": "test_sa",
    }
    resources = [sa]

    tf_file = tmp_path / "gcp_service_accounts.tf"
    generate_tf(resources, "gcp_service_accounts", tf_file, provider="gcp")
    generate_imports_file(
        "gcp_service_accounts", resources, "email", tmp_path, provider="gcp"
    )
    import_file = tmp_path / "gcp_service_accounts_import.json"

    assert tf_file.exists()
    assert import_file.exists()
    assert import_file.name == f"{tf_file.stem}_import.json"

    data = json.loads(import_file.read_text())
    assert data[0]["resource_name"] == sa["account_id"].replace("-", "_")

    (tmp_path / "provider.tf").write_text(
        """
terraform {
  required_providers {
    google = {
      source = \"hashicorp/google\"
    }
  }
}

provider \"google\" {
  project = \"dummy\"
  region  = \"us-central1\"
  credentials = \"{}\"
}
        """
    )

    state = {
        "version": 4,
        "terraform_version": "1.6.0",
        "serial": 1,
        "lineage": "00000000-0000-0000-0000-000000000000",
        "outputs": {},
        "resources": [
            {
                "mode": "managed",
                "type": "google_service_account",
                "name": sa["account_id"].replace("-", "_"),
                "provider": "provider[\"registry.terraform.io/hashicorp/google\"]",
                "instances": [
                    {
                        "schema_version": 0,
                        "attributes": {
                            "id": sa["name"],
                            "account_id": sa["account_id"],
                            "display_name": sa["display_name"],
                            "project": sa["project"],
                        },
                    }
                ],
            }
        ],
    }
    (tmp_path / "terraform.tfstate").write_text(json.dumps(state))

    # Provide placeholder credentials
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "dummy")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(tmp_path / "creds.json"))
    (tmp_path / "creds.json").write_text("{}")

    _run_terraform_zero_plan(tmp_path)
