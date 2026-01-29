# terraback/cli/gcp/secrets/secrets.py
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from google.cloud import secretmanager_v1
from google.api_core import exceptions

from terraback.cli.gcp.session import get_gcp_credentials, get_default_project_id
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager

app = typer.Typer(name="secret", help="Scan and import GCP Secret Manager secrets.")

def get_secret_data(project_id: str) -> List[Dict[str, Any]]:
    """Fetch Secret Manager secret data from GCP."""
    session = get_gcp_credentials()
    client = secretmanager_v1.SecretManagerServiceClient(credentials=session)
    
    secrets = []
    
    try:
        # List all secrets in the project
        parent = f"projects/{project_id}"
        
        for secret in client.list_secrets(request={"parent": parent}):
            secret_name = secret.name.split('/')[-1]
            
            # Get secret details (without accessing the actual secret value)
            secret_data = {
                "secret_id": secret_name,
                "project": project_id,
                "name_sanitized": secret_name.replace('-', '_').lower(),
            }
            
            # Get labels
            if secret.labels:
                secret_data["labels"] = dict(secret.labels)
            
            # Get replication policy
            if hasattr(secret, 'replication') and secret.replication:
                replication = secret.replication
                
                # Check if it's automatic replication
                if hasattr(replication, 'automatic') and replication.automatic:
                    secret_data["replication"] = {
                        "automatic": True
                    }
                    # Get KMS key if customer managed encryption is used
                    if hasattr(replication.automatic, 'customer_managed_encryption') and replication.automatic.customer_managed_encryption:
                        if replication.automatic.customer_managed_encryption.kms_key_name:
                            secret_data["replication"]["automatic_kms_key_name"] = replication.automatic.customer_managed_encryption.kms_key_name
                
                # Check if it's user managed replication
                elif hasattr(replication, 'user_managed') and replication.user_managed:
                    replicas = []
                    for replica in replication.user_managed.replicas:
                        replica_data = {"location": replica.location}
                        
                        # Get KMS key for this replica if set
                        if hasattr(replica, 'customer_managed_encryption') and replica.customer_managed_encryption:
                            if replica.customer_managed_encryption.kms_key_name:
                                replica_data["kms_key_name"] = replica.customer_managed_encryption.kms_key_name
                        
                        replicas.append(replica_data)
                    
                    if replicas:
                        secret_data["replication"] = {
                            "user_managed": {
                                "replicas": replicas
                            }
                        }
            
            # Get rotation settings
            if hasattr(secret, 'rotation') and secret.rotation:
                rotation = secret.rotation
                rotation_data = {}
                
                # Next rotation time
                if hasattr(rotation, 'next_rotation_time') and rotation.next_rotation_time:
                    rotation_data["next_rotation_time"] = rotation.next_rotation_time.isoformat()
                
                # Rotation period
                if hasattr(rotation, 'rotation_period') and rotation.rotation_period:
                    rotation_data["rotation_period"] = f"{int(rotation.rotation_period.total_seconds())}s"
                
                if rotation_data:
                    secret_data["rotation"] = rotation_data
            
            # Get topics for event notifications
            if hasattr(secret, 'topics') and secret.topics:
                topics = []
                for topic in secret.topics:
                    topic_name = topic.name.split('/')[-1] if hasattr(topic, 'name') else None
                    if topic_name:
                        topics.append(topic_name)
                if topics:
                    secret_data["topics"] = topics
            
            # Get expiration time if set
            if hasattr(secret, 'expire_time') and secret.expire_time:
                secret_data["expire_time"] = secret.expire_time.isoformat()
            
            # Get TTL if set
            if hasattr(secret, 'ttl') and secret.ttl:
                secret_data["ttl"] = f"{int(secret.ttl.total_seconds())}s"
            
            # Get version aliases
            if hasattr(secret, 'version_aliases') and secret.version_aliases:
                secret_data["version_aliases"] = dict(secret.version_aliases)
            
            # Get annotations
            if hasattr(secret, 'annotations') and secret.annotations:
                secret_data["annotations"] = dict(secret.annotations)
            
            secrets.append(secret_data)
            
    except exceptions.PermissionDenied:
        typer.echo(f"Error: Permission denied accessing Secret Manager secrets in project {project_id}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error fetching Secret Manager secrets: {str(e)}", err=True)
        raise typer.Exit(code=1)
    
    return secrets

@app.command("scan")
def scan_secrets(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p", help="GCP Project ID.", envvar="GCP_PROJECT_ID"),
    with_deps: bool = typer.Option(False, "--with-deps", help="Scan dependencies")
):
    """Scans GCP Secret Manager secrets and generates Terraform code."""
    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found. Please run 'gcloud config set project' or set GCP_PROJECT_ID", err=True)
            raise typer.Exit(code=1)
    
    if with_deps:
        from terraback.utils.cross_scan_registry import recursive_scan
        typer.echo("Scanning GCP Secret Manager secrets with dependencies...")
        recursive_scan("gcp_secret", output_dir=output_dir, project_id=project_id)
    else:
        typer.echo(f"Scanning for Secret Manager secrets in project '{project_id}'...")
        
        secrets_data = get_secret_data(project_id)
        
        if not secrets_data:
            typer.echo("No Secret Manager secrets found.")
            return
        
        # Generate Terraform files
        output_file = output_dir / "gcp_secret.tf"
        generate_tf(secrets_data, "gcp_secret", output_file, provider="gcp", project_id=project_id)
        typer.echo(f"Generated Terraform for {len(secrets_data)} secrets -> {output_file}")
        
        # Generate import file
        generate_imports_file(
            "gcp_secret",
            secrets_data,
            output_dir=output_dir, provider="gcp"
        )
        
        # Generate variable stub for secret values
        typer.echo("\n[!]  Note: Secret values are not exported. You'll need to set them manually or reference existing versions.")

# Scan function for cross-scan registry
def scan_gcp_secrets(output_dir: Path, project_id: Optional[str] = None, **kwargs):
    """Scan function to be registered with cross-scan registry."""
    if not project_id:
        project_id = get_default_project_id()
    
    typer.echo(f"[Cross-scan] Scanning GCP Secret Manager secrets in project {project_id}")
    
    secrets_data = get_secret_data(project_id)
    
    if secrets_data:
        output_file = output_dir / "gcp_secret.tf"
        generate_tf(secrets_data, "gcp_secret", output_file, provider="gcp", project_id=project_id)
        
        generate_imports_file(
            "gcp_secret",
            secrets_data,
            output_dir=output_dir, provider="gcp"
        )
        
        typer.echo(f"[Cross-scan] Generated Terraform for {len(secrets_data)} secrets")

@app.command("list")
def list_secrets(output_dir: Path = typer.Option("generated", "-o", "--output-dir")):
    """List all GCP Secret Manager resources previously generated."""
    ImportManager(output_dir, "gcp_secret").list_all()

@app.command("import")
def import_secret(
    secret_id: str = typer.Argument(..., help="GCP Secret Manager secret ID"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir")
):
    """Run terraform import for a specific GCP secret."""
    ImportManager(output_dir, "gcp_secret").find_and_import(secret_id)
