from pathlib import Path

from terraback.cli.aws.apigateway.rest_apis import ApiGatewayResources, generate_terraform_files


def test_duplicate_apis_deduplicated(tmp_path: Path):
    resources = ApiGatewayResources(
        apis=[{"id": "api1", "name": "demo"}, {"id": "api1", "name": "demo"}]
    )

    generate_terraform_files(resources, tmp_path)

    content = (tmp_path / "api_gateway_rest_api.tf").read_text()
    assert content.count('resource "aws_api_gateway_rest_api"') == 1


def test_duplicate_api_names_get_suffix(tmp_path: Path):
    resources = ApiGatewayResources(
        apis=[
            {"id": "api1", "name": "Terraback License API"},
            {"id": "api2", "name": "Terraback License API"},
        ]
    )

    generate_terraform_files(resources, tmp_path)

    content = (tmp_path / "api_gateway_rest_api.tf").read_text()
    assert content.count('resource "aws_api_gateway_rest_api"') == 2
    assert '"terraback_license_api"' in content
    assert '"terraback_license_api_2"' in content
