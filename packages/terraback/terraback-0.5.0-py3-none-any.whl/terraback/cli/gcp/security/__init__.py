from terraback.core.license import require_professional
import typer
from pathlib import Path

from .kms import scan_kms_key_rings, scan_kms_crypto_keys, list_kms_resources, import_kms_resource
from .certificate_authority import scan_certificate_authorities, list_certificate_authorities, import_certificate_authority
from .binary_authorization import scan_binary_authorization_policies, list_binary_authorization_policies, import_binary_authorization_policy

from terraback.utils.cross_scan_registry import register_scan_function, cross_scan_registry

app = typer.Typer(
    name="security",
    help="Manage GCP security resources like KMS, Certificate Authority, and Binary Authorization.",
    no_args_is_help=True
)

# --- KMS Commands ---
@app.command(name="scan-kms", help="Scan KMS key rings and crypto keys.")
@require_professional
def scan_kms_command(
    output_dir: Path = typer.Option("generated", help="Directory to save Terraform files"),
    project_id: str = typer.Option(None, help="GCP Project ID"),
    location: str = typer.Option(None, help="GCP location/region")
):
    scan_kms_key_rings(output_dir, project_id, location)
    scan_kms_crypto_keys(output_dir, project_id, location)

@app.command(name="list-kms", help="List scanned KMS resources.")
@require_professional
def list_kms_command(output_dir: Path = typer.Option("generated")):
    list_kms_resources(output_dir)

@app.command(name="import-kms", help="Import a KMS resource by ID.")
@require_professional
def import_kms_command(
    resource_id: str,
    resource_type: str = typer.Option(..., help="Resource type: key_ring or crypto_key"),
    output_dir: Path = typer.Option("generated")
):
    import_kms_resource(resource_id, resource_type, output_dir)

# --- Certificate Authority Commands ---
@app.command(name="scan-ca", help="Scan Certificate Authorities.")
@require_professional
def scan_ca_command(
    output_dir: Path = typer.Option("generated", help="Directory to save Terraform files"),
    project_id: str = typer.Option(None, help="GCP Project ID"),
    location: str = typer.Option(None, help="GCP location/region")
):
    scan_certificate_authorities(output_dir, project_id, location)

@app.command(name="list-ca", help="List scanned Certificate Authorities.")
@require_professional
def list_ca_command(output_dir: Path = typer.Option("generated")):
    list_certificate_authorities(output_dir)

@app.command(name="import-ca", help="Import a Certificate Authority by ID.")
@require_professional
def import_ca_command(
    ca_id: str,
    output_dir: Path = typer.Option("generated")
):
    import_certificate_authority(ca_id, output_dir)

# --- Binary Authorization Commands ---
@app.command(name="scan-binary-auth", help="Scan Binary Authorization policies.")
@require_professional
def scan_binary_auth_command(
    output_dir: Path = typer.Option("generated", help="Directory to save Terraform files"),
    project_id: str = typer.Option(None, help="GCP Project ID")
):
    scan_binary_authorization_policies(output_dir, project_id)

@app.command(name="list-binary-auth", help="List scanned Binary Authorization policies.")
@require_professional
def list_binary_auth_command(output_dir: Path = typer.Option("generated")):
    list_binary_authorization_policies(output_dir)

@app.command(name="import-binary-auth", help="Import a Binary Authorization policy.")
@require_professional
def import_binary_auth_command(
    policy_id: str,
    output_dir: Path = typer.Option("generated")
):
    import_binary_authorization_policy(policy_id, output_dir)

# --- Combined Commands ---
@app.command(name="scan-all", help="Scan all security resources.")
@require_professional
def scan_all_security_command(
    output_dir: Path = typer.Option("generated", help="Directory to save Terraform files"),
    project_id: str = typer.Option(None, help="GCP Project ID"),
    location: str = typer.Option(None, help="GCP location/region")
):
    scan_kms_key_rings(output_dir, project_id, location)
    scan_kms_crypto_keys(output_dir, project_id, location)
    scan_certificate_authorities(output_dir, project_id, location)
    scan_binary_authorization_policies(output_dir, project_id)

# --- Registration ---
def register():
    """Registers scan functions and dependencies for the security module."""
    register_scan_function("gcp_kms_key_ring", scan_kms_key_rings)
    register_scan_function("gcp_kms_crypto_key", scan_kms_crypto_keys)
    register_scan_function("gcp_certificate_authority", scan_certificate_authorities)
    register_scan_function("gcp_binary_authorization_policy", scan_binary_authorization_policies)

    # Define security dependencies
    # Crypto keys depend on key rings
    cross_scan_registry.register_dependency("gcp_kms_crypto_key", "gcp_kms_key_ring")
    
    # Certificate authorities may use KMS for key management
    cross_scan_registry.register_dependency("gcp_certificate_authority", "gcp_kms_crypto_key")
    
    # Binary authorization may depend on container analysis
    cross_scan_registry.register_dependency("gcp_binary_authorization_policy", "gcp_container_registry")