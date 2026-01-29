from pathlib import Path

KEYVAULT_SECRET_VARIABLE_BLOCK = (
    'variable "keyvault_secret_value" {\n'
    '  type        = string\n'
    '  description = "Value used for Key Vault secret placeholder content"\n'
    '  sensitive   = true\n'
    '}\n'
)

VM_SSH_KEY_VARIABLE_BLOCK = (
    'variable "vm_ssh_public_key" {\n'
    '  type        = string\n'
    '  description = "SSH public key for Azure Linux VMs"\n'
    '  default     = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7Q1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ user@example.com"\n'
    '}\n'
)

STORAGE_ACCOUNT_KEY_VARIABLE_BLOCK = (
    'variable "storage_account_key" {\n'
    '  type        = string\n'
    '  description = "Storage account access key for Azure resources"\n'
    '  sensitive   = true\n'
    '}\n'
)

CERTIFICATE_PASSWORD_VARIABLE_BLOCK = (
    'variable "certificate_password" {\n'
    '  type        = string\n'
    '  description = "Password for certificates in Azure resources"\n'
    '  sensitive   = true\n'
    '}\n'
)

SSL_CERTIFICATE_PASSWORD_VARIABLE_BLOCK = (
    'variable "ssl_certificate_password" {\n'
    '  type        = string\n'
    '  description = "Password for SSL certificates in Application Gateway"\n'
    '  sensitive   = true\n'
    '}\n'
)

ADMIN_PASSWORD_VARIABLE_BLOCK = (
    'variable "admin_password" {\n'
    '  type        = string\n'
    '  description = "Administrator password for Azure resources"\n'
    '  default     = "ChangeMe123!"\n'
    '  sensitive   = true\n'
    '}\n'
)

FUNCTION_APP_STORAGE_ACCOUNT_NAME_VARIABLE_BLOCK = (
    'variable "function_app_storage_account_name" {\n'
    '  type        = string\n'
    '  description = "Storage account name for Azure Function Apps"\n'
    '  default     = "changeme123storage"\n'
    '}\n'
)

def ensure_keyvault_secret_variable_stub(output_dir: Path) -> None:
    """Ensure variables.tf includes the keyvault_secret_value variable block."""
    _ensure_variable_stub(output_dir, 'variable "keyvault_secret_value"', 
                         KEYVAULT_SECRET_VARIABLE_BLOCK,
                         "keyvault_secret_value")

def ensure_vm_ssh_key_variable_stub(output_dir: Path) -> None:
    """Ensure variables.tf includes the vm_ssh_public_key variable block."""
    _ensure_variable_stub(output_dir, 'variable "vm_ssh_public_key"', 
                         VM_SSH_KEY_VARIABLE_BLOCK,
                         "vm_ssh_public_key")

def ensure_storage_account_key_variable_stub(output_dir: Path) -> None:
    """Ensure variables.tf includes the storage_account_key variable block."""
    _ensure_variable_stub(output_dir, 'variable "storage_account_key"', 
                         STORAGE_ACCOUNT_KEY_VARIABLE_BLOCK,
                         "storage_account_key")

def ensure_certificate_password_variable_stub(output_dir: Path) -> None:
    """Ensure variables.tf includes the certificate_password variable block."""
    _ensure_variable_stub(output_dir, 'variable "certificate_password"', 
                         CERTIFICATE_PASSWORD_VARIABLE_BLOCK,
                         "certificate_password")

def ensure_admin_password_variable_stub(output_dir: Path) -> None:
    """Ensure variables.tf includes the admin_password variable block."""
    _ensure_variable_stub(output_dir, 'variable "admin_password"', 
                         ADMIN_PASSWORD_VARIABLE_BLOCK,
                         "admin_password")

def ensure_function_app_storage_account_name_variable_stub(output_dir: Path) -> None:
    """Ensure variables.tf includes the function_app_storage_account_name variable block."""
    _ensure_variable_stub(output_dir, 'variable "function_app_storage_account_name"', 
                         FUNCTION_APP_STORAGE_ACCOUNT_NAME_VARIABLE_BLOCK,
                         "function_app_storage_account_name")

def _ensure_variable_stub(output_dir: Path, search_string: str, 
                         variable_block: str, variable_name: str) -> None:
    """Generic function to ensure a variable exists in variables.tf."""
    variables_file = output_dir / "variables.tf"
    updated = False
    try:
        if variables_file.exists():
            content = variables_file.read_text()
            if search_string in content:
                # Special case: replace invalid SSH key placeholders
                if variable_name == "vm_ssh_public_key" and 'ssh-rsa AAAAB3... user@example.com' in content:
                    content = content.replace(
                        'default     = "ssh-rsa AAAAB3... user@example.com"',
                        'default     = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDTgvwjlRHZ2Y9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p9Z9p user@example.com"'
                    )
                    variables_file.write_text(content)
                    print(f"Updated invalid SSH key placeholder in variable '{variable_name}'")
                return
            if content and not content.endswith("\n"):
                content += "\n"
            content += variable_block + "\n"
            updated = True
        else:
            content = variable_block + "\n"
            updated = True
        variables_file.write_text(content)
        if updated:
            print(
                f"Added placeholder variable '{variable_name}' to variables.tf. "
                "Update this value before applying Terraform."
            )
    except Exception as e:
        print(f"Warning: could not update {variables_file}: {e}")