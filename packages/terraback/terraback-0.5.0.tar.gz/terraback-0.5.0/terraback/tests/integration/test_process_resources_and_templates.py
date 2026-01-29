import re

from terraback.cli.aws.resource_processor import process_resources as aws_process_resources
from terraback.cli.azure.resource_processor import process_resources as azure_process_resources
from terraback.terraform_generator import writer


def test_aws_process_resources_and_template_rendering():
    """AWS roles should be filtered and rendered with consistent spacing."""
    writer.reset_template_loader()

    roles = [
        {"RoleName": "Custom Role", "Path": "/", "AssumeRolePolicyDocument": {}},
        {"RoleName": "AnotherRole", "Path": "/", "AssumeRolePolicyDocument": {}},
        {"RoleName": "AWSServiceRoleForSupport", "Path": "/", "AssumeRolePolicyDocument": {}},
    ]

    processed = aws_process_resources(roles, "roles")

    # AWS-managed role should be filtered out
    assert all(r["RoleName"] != "AWSServiceRoleForSupport" for r in processed)
    # Sanitized name added by processor
    assert all("name_sanitized" in r for r in processed)

    loader = writer.get_template_loader()
    loader.env.globals["resource_spacer"] = writer._make_joiner("\n\n")
    output = loader.render_template("aws_iam_roles", processed, "aws")

    assert "AWSServiceRoleForSupport" not in output
    assert 'resource "aws_iam_role" "custom_role"' in output
    assert 'resource "aws_iam_role" "anotherrole"' in output

    # Ensure exactly one blank line separates resources
    assert re.search(r'}\n\nresource "aws_iam_role"', output)
    assert '}\n\n\nresource "aws_iam_role"' not in output


def test_azure_process_resources_and_template_rendering():
    """Azure resource groups should be filtered and rendered with consistent spacing."""
    writer.reset_template_loader()

    resource_groups = [
        {"name": "prod-rg", "location": "eastus", "tags": {"env": "prod"}},
        {"name": "dev rg", "location": "eastus"},
        {"name": "NetworkWatcherRG", "location": "eastus"},
    ]

    processed = azure_process_resources(resource_groups, "azure_resource_group")

    # Azure managed group should be filtered out
    assert all(r["name"] != "NetworkWatcherRG" for r in processed)
    # Sanitized names should be present
    assert all("name_sanitized" in r for r in processed)

    loader = writer.get_template_loader()
    loader.env.globals["resource_spacer"] = writer._make_joiner("\n\n")
    output = loader.render_template("azure_resource_group", processed, "azure")

    assert "NetworkWatcherRG" not in output
    assert 'resource "azurerm_resource_group" "prod_rg"' in output
    assert 'resource "azurerm_resource_group" "dev_rg"' in output

    # Ensure exactly one blank line separates resources
    assert re.search(r'}\n\nresource "azurerm_resource_group"', output)
    assert '}\n\n\nresource "azurerm_resource_group"' not in output
