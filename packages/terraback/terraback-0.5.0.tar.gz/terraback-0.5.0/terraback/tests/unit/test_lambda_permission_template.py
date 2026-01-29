import json
from pathlib import Path

from terraback.terraform_generator.writer import get_template_loader, generate_tf
from terraback.terraform_generator.imports import generate_imports_file


def test_lambda_permission_template_and_import(tmp_path: Path):
    loader = get_template_loader()
    resource = {
        "statement_id": "sid1",
        "function_name": "my_function",
        "name_sanitized": "my_function_sid1",
        "source_arn": "arn:aws:execute-api:region:acct:api-id/*/GET/resource",
        "source_account": "123456789012",
    }

    # ensure canonical template is found for full resource type
    template_path = loader.get_template_path("aws_lambda_permission", "aws")
    assert template_path.endswith("aws/compute/lambda_permission.tf.j2")

    output = loader.render_template("aws_lambda_permission", [resource], "aws")
    assert 'resource "aws_lambda_permission" "my_function_sid1"' in output
    assert 'source_arn    = "arn:aws:execute-api:region:acct:api-id/*/GET/resource"' in output
    assert 'source_account = "123456789012"' in output

    tf_path = tmp_path / "lambda_permission.tf"
    generate_tf([resource], "lambda_permission", tf_path)
    tf_content = tf_path.read_text()
    assert 'resource "aws_lambda_permission" "my_function_sid1"' in tf_content

    generate_imports_file(
        "lambda_permission",
        [resource],
        "statement_id",
        tmp_path,
        ["function_name", "statement_id"],
    )
    import_file = tmp_path / "import" / "lambda_permission_import.json"
    data = json.loads(import_file.read_text())
    assert data[0]["resource_type"] == "aws_lambda_permission"
    assert data[0]["resource_name"] == "my_function_sid1"
    assert data[0]["remote_id"] == "my_function/sid1"
    
def test_lambda_permission_with_qualifier(tmp_path: Path):
    loader = get_template_loader()
    resource = {
        "statement_id": "sid2",
        "function_name": "my_function",
        "qualifier": "prod",
        "name_sanitized": "my_function_sid2",
        "source_arn": "arn:aws:execute-api:region:acct:api-id/*/GET/resource",
        "source_account": "123456789012",
    }

    output = loader.render_template("aws_lambda_permission", [resource], "aws")
    assert 'resource "aws_lambda_permission" "my_function_sid2"' in output
    assert 'qualifier     = "prod"' in output

    generate_imports_file(
        "lambda_permission",
        [resource],
        "statement_id",
        tmp_path,
        ["function_name", "statement_id"],
    )
    import_file = tmp_path / "import" / "lambda_permission_import.json"
    data = json.loads(import_file.read_text())
    assert data[0]["remote_id"] == "my_function:prod/sid2"
