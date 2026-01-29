# terraback/cli/gcp/pubsub/topics.py
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from google.cloud import pubsub_v1
from google.api_core import exceptions

from terraback.cli.gcp.session import get_gcp_credentials, get_default_project_id
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager

app = typer.Typer(name="topic", help="Scan and import GCP Pub/Sub topics.")

def get_pubsub_topic_data(project_id: str) -> List[Dict[str, Any]]:
    """Fetch Pub/Sub topic data from GCP."""
    session = get_gcp_credentials()
    publisher_client = pubsub_v1.PublisherClient(credentials=session)
    
    topics = []
    
    try:
        # List all topics in the project
        project_path = f"projects/{project_id}"
        
        for topic in publisher_client.list_topics(request={"project": project_path}):
            topic_name = topic.name.split('/')[-1]
            
            # Get topic details
            topic_data = {
                "name": topic_name,
                "project": project_id,
                "name_sanitized": topic_name.replace('-', '_').lower(),
                "labels": dict(topic.labels) if topic.labels else {},
            }
            
            # Get message retention duration if set
            if hasattr(topic, 'message_retention_duration') and topic.message_retention_duration:
                # Convert duration to string format
                duration = topic.message_retention_duration
                topic_data["message_retention_duration"] = f"{int(duration.total_seconds())}s"
            
            # Get KMS key if encryption is enabled
            if hasattr(topic, 'kms_key_name') and topic.kms_key_name:
                topic_data["kms_key_name"] = topic.kms_key_name
            
            # Get schema settings if configured
            if hasattr(topic, 'schema_settings') and topic.schema_settings:
                schema_settings = topic.schema_settings
                topic_data["schema_settings"] = {
                    "schema": schema_settings.schema,
                    "encoding": schema_settings.encoding.name if hasattr(schema_settings, 'encoding') else None
                }
            
            # Get message storage policy if configured
            if hasattr(topic, 'message_storage_policy') and topic.message_storage_policy:
                if topic.message_storage_policy.allowed_persistence_regions:
                    topic_data["message_storage_policy"] = {
                        "allowed_persistence_regions": list(topic.message_storage_policy.allowed_persistence_regions)
                    }
            
            topics.append(topic_data)
            
    except exceptions.PermissionDenied:
        typer.echo(f"Error: Permission denied accessing Pub/Sub topics in project {project_id}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error fetching Pub/Sub topics: {str(e)}", err=True)
        raise typer.Exit(code=1)
    
    return topics

@app.command("scan")
def scan_pubsub_topics(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p", help="GCP Project ID.", envvar="GCP_PROJECT_ID"),
    with_deps: bool = typer.Option(False, "--with-deps", help="Scan dependencies")
):
    """Scans GCP Pub/Sub topics and generates Terraform code."""
    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found. Please run 'gcloud config set project' or set GCP_PROJECT_ID", err=True)
            raise typer.Exit(code=1)
    
    if with_deps:
        from terraback.utils.cross_scan_registry import recursive_scan
        typer.echo("Scanning GCP Pub/Sub topics with dependencies...")
        recursive_scan("gcp_pubsub_topic", output_dir=output_dir, project_id=project_id)
    else:
        typer.echo(f"Scanning for Pub/Sub topics in project '{project_id}'...")
        
        topics_data = get_pubsub_topic_data(project_id)
        
        if not topics_data:
            typer.echo("No Pub/Sub topics found.")
            return
        
        # Generate Terraform files
        output_file = output_dir / "gcp_pubsub_topic.tf"
        generate_tf(topics_data, "gcp_pubsub_topic", output_file, provider="gcp", project_id=project_id)
        typer.echo(f"Generated Terraform for {len(topics_data)} Pub/Sub topics -> {output_file}")
        
        # Generate import file
        generate_imports_file(
            "gcp_pubsub_topic",
            topics_data,
            remote_resource_id_key="name",
            output_dir=output_dir, provider="gcp"
        )

# Scan function for cross-scan registry
def scan_gcp_pubsub_topics(output_dir: Path, project_id: Optional[str] = None, **kwargs):
    """Scan function to be registered with cross-scan registry."""
    if not project_id:
        project_id = get_default_project_id()
    
    typer.echo(f"[Cross-scan] Scanning GCP Pub/Sub topics in project {project_id}")
    
    topics_data = get_pubsub_topic_data(project_id)
    
    if topics_data:
        output_file = output_dir / "gcp_pubsub_topic.tf"
        generate_tf(topics_data, "gcp_pubsub_topic", output_file, provider="gcp", project_id=project_id)
        
        generate_imports_file(
            "gcp_pubsub_topic",
            topics_data,
            remote_resource_id_key="name",
            output_dir=output_dir, provider="gcp"
        )
        
        typer.echo(f"[Cross-scan] Generated Terraform for {len(topics_data)} Pub/Sub topics")

@app.command("list")
def list_pubsub_topics(output_dir: Path = typer.Option("generated", "-o", "--output-dir")):
    """List all GCP Pub/Sub topic resources previously generated."""
    ImportManager(output_dir, "gcp_pubsub_topic").list_all()

@app.command("import")
def import_pubsub_topic(
    topic_id: str = typer.Argument(..., help="GCP Pub/Sub topic ID"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir")
):
    """Run terraform import for a specific GCP Pub/Sub topic."""
    ImportManager(output_dir, "gcp_pubsub_topic").find_and_import(topic_id)
