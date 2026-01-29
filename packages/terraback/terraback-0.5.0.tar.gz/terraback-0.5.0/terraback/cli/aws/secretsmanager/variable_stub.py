from pathlib import Path

VARIABLE_BLOCK = (
    'variable "secret_value" {\n'
    '  type        = string\n'
    '  description = "Value used for Secrets Manager placeholder content"\n'
    '  default     = "CHANGE_ME"\n'
    '}\n'
)

def ensure_variable_stub(output_dir: Path) -> None:
    """Ensure variables.tf includes the secret_value variable block."""
    variables_file = output_dir / "variables.tf"
    updated = False
    try:
        if variables_file.exists():
            content = variables_file.read_text()
            if 'variable "secret_value"' in content:
                return
            if content and not content.endswith("\n"):
                content += "\n"
            content += VARIABLE_BLOCK + "\n"
            updated = True
        else:
            content = VARIABLE_BLOCK + "\n"
            updated = True
        variables_file.write_text(content)
        if updated:
            print(
                "Added placeholder variable 'secret_value' to variables.tf. "
                "Update this value before applying Terraform."
            )
    except Exception as e:
        print(f"Warning: could not update {variables_file}: {e}")
