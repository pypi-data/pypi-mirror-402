from terraback.cli.aws.secretsmanager.variable_stub import ensure_variable_stub


def test_ensure_variable_stub_creates_file(tmp_path):
    ensure_variable_stub(tmp_path)
    variables_file = tmp_path / "variables.tf"
    assert variables_file.exists()
    content = variables_file.read_text()
    assert 'variable "secret_value"' in content
    assert 'description = "Value used for Secrets Manager placeholder content"' in content

