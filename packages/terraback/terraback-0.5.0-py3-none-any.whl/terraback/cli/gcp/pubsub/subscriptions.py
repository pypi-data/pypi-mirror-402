# terraback/cli/gcp/pubsub/subscriptions.py
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from google.cloud import pubsub_v1
from google.api_core import exceptions

from terraback.cli.gcp.session import get_gcp_credentials, get_default_project_id
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager

app = typer.Typer(name="subscription", help="Scan and import GCP Pub/Sub subscriptions.")

def get_pubsub_subscription_data(project_id: str) -> List[Dict[str, Any]]:
    """Fetch Pub/Sub subscription data from GCP."""
    session = get_gcp_credentials()
    subscriber_client = pubsub_v1.SubscriberClient(credentials=session)
    
    subscriptions = []
    
    try:
        # List all subscriptions in the project
        project_path = f"projects/{project_id}"
        
        for subscription in subscriber_client.list_subscriptions(request={"project": project_path}):
            subscription_name = subscription.name.split('/')[-1]
            topic_name = subscription.topic.split('/')[-1] if subscription.topic else None
            
            # Get subscription details
            subscription_data = {
                "name": subscription_name,
                "project": project_id,
                "topic": topic_name,
                "name_sanitized": subscription_name.replace('-', '_').lower(),
                "labels": dict(subscription.labels) if subscription.labels else {},
            }
            
            # Get ack deadline
            if hasattr(subscription, 'ack_deadline_seconds'):
                subscription_data["ack_deadline_seconds"] = subscription.ack_deadline_seconds
            
            # Get message retention duration
            if hasattr(subscription, 'message_retention_duration') and subscription.message_retention_duration:
                duration = subscription.message_retention_duration
                subscription_data["message_retention_duration"] = f"{int(duration.total_seconds())}s"
            
            # Get retain acked messages setting
            if hasattr(subscription, 'retain_acked_messages'):
                subscription_data["retain_acked_messages"] = subscription.retain_acked_messages
            
            # Get expiration policy
            if hasattr(subscription, 'expiration_policy') and subscription.expiration_policy:
                exp_policy = subscription.expiration_policy
                if hasattr(exp_policy, 'ttl') and exp_policy.ttl:
                    subscription_data["expiration_policy"] = {
                        "ttl": f"{int(exp_policy.ttl.total_seconds())}s"
                    }
            
            # Get retry policy
            if hasattr(subscription, 'retry_policy') and subscription.retry_policy:
                retry = subscription.retry_policy
                retry_data = {}
                if hasattr(retry, 'minimum_backoff') and retry.minimum_backoff:
                    retry_data["minimum_backoff"] = f"{int(retry.minimum_backoff.total_seconds())}s"
                if hasattr(retry, 'maximum_backoff') and retry.maximum_backoff:
                    retry_data["maximum_backoff"] = f"{int(retry.maximum_backoff.total_seconds())}s"
                if retry_data:
                    subscription_data["retry_policy"] = retry_data
            
            # Get dead letter policy
            if hasattr(subscription, 'dead_letter_policy') and subscription.dead_letter_policy:
                dl_policy = subscription.dead_letter_policy
                if dl_policy.dead_letter_topic:
                    dead_letter_topic = dl_policy.dead_letter_topic.split('/')[-1]
                    subscription_data["dead_letter_policy"] = {
                        "dead_letter_topic": dead_letter_topic,
                        "max_delivery_attempts": dl_policy.max_delivery_attempts if hasattr(dl_policy, 'max_delivery_attempts') else 5
                    }
            
            # Get push config
            if hasattr(subscription, 'push_config') and subscription.push_config:
                push = subscription.push_config
                if push.push_endpoint:
                    push_data = {"push_endpoint": push.push_endpoint}
                    
                    # Get push attributes
                    if push.attributes:
                        push_data["attributes"] = dict(push.attributes)
                    
                    # Get OIDC token if configured
                    if hasattr(push, 'oidc_token') and push.oidc_token:
                        push_data["oidc_token"] = {
                            "service_account_email": push.oidc_token.service_account_email,
                            "audience": push.oidc_token.audience if hasattr(push.oidc_token, 'audience') else ""
                        }
                    
                    subscription_data["push_config"] = push_data
            
            # Get enable_message_ordering
            if hasattr(subscription, 'enable_message_ordering'):
                subscription_data["enable_message_ordering"] = subscription.enable_message_ordering
            
            # Get enable_exactly_once_delivery
            if hasattr(subscription, 'enable_exactly_once_delivery'):
                subscription_data["enable_exactly_once_delivery"] = subscription.enable_exactly_once_delivery
            
            # Get bigquery config
            if hasattr(subscription, 'bigquery_config') and subscription.bigquery_config:
                bq_config = subscription.bigquery_config
                subscription_data["bigquery_config"] = {
                    "table": bq_config.table,
                    "write_metadata": bq_config.write_metadata if hasattr(bq_config, 'write_metadata') else False
                }
            
            subscriptions.append(subscription_data)
            
    except exceptions.PermissionDenied:
        typer.echo(f"Error: Permission denied accessing Pub/Sub subscriptions in project {project_id}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error fetching Pub/Sub subscriptions: {str(e)}", err=True)
        raise typer.Exit(code=1)
    
    return subscriptions

@app.command("scan")
def scan_pubsub_subscriptions(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p", help="GCP Project ID.", envvar="GCP_PROJECT_ID"),
    with_deps: bool = typer.Option(False, "--with-deps", help="Scan dependencies")
):
    """Scans GCP Pub/Sub subscriptions and generates Terraform code."""
    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found. Please run 'gcloud config set project' or set GCP_PROJECT_ID", err=True)
            raise typer.Exit(code=1)
    
    if with_deps:
        from terraback.utils.cross_scan_registry import recursive_scan
        typer.echo("Scanning GCP Pub/Sub subscriptions with dependencies...")
        recursive_scan("gcp_pubsub_subscription", output_dir=output_dir, project_id=project_id)
    else:
        typer.echo(f"Scanning for Pub/Sub subscriptions in project '{project_id}'...")
        
        subscriptions_data = get_pubsub_subscription_data(project_id)
        
        if not subscriptions_data:
            typer.echo("No Pub/Sub subscriptions found.")
            return
        
        # Generate Terraform files
        output_file = output_dir / "gcp_pubsub_subscription.tf"
        generate_tf(subscriptions_data, "gcp_pubsub_subscription", output_file, provider="gcp", project_id=project_id)
        typer.echo(f"Generated Terraform for {len(subscriptions_data)} Pub/Sub subscriptions -> {output_file}")
        
        # Generate import file
        generate_imports_file(
            "gcp_pubsub_subscription",
            subscriptions_data,
            remote_resource_id_key="name",
            output_dir=output_dir, provider="gcp"
        )

# Scan function for cross-scan registry
def scan_gcp_pubsub_subscriptions(output_dir: Path, project_id: Optional[str] = None, **kwargs):
    """Scan function to be registered with cross-scan registry."""
    if not project_id:
        project_id = get_default_project_id()
    
    typer.echo(f"[Cross-scan] Scanning GCP Pub/Sub subscriptions in project {project_id}")
    
    subscriptions_data = get_pubsub_subscription_data(project_id)
    
    if subscriptions_data:
        output_file = output_dir / "gcp_pubsub_subscription.tf"
        generate_tf(subscriptions_data, "gcp_pubsub_subscription", output_file, provider="gcp", project_id=project_id)
        
        generate_imports_file(
            "gcp_pubsub_subscription",
            subscriptions_data,
            remote_resource_id_key="name",
            output_dir=output_dir, provider="gcp"
        )
        
        typer.echo(f"[Cross-scan] Generated Terraform for {len(subscriptions_data)} Pub/Sub subscriptions")

@app.command("list")
def list_pubsub_subscriptions(output_dir: Path = typer.Option("generated", "-o", "--output-dir")):
    """List all GCP Pub/Sub subscription resources previously generated."""
    ImportManager(output_dir, "gcp_pubsub_subscription").list_all()

@app.command("import")
def import_pubsub_subscription(
    subscription_id: str = typer.Argument(..., help="GCP Pub/Sub subscription ID"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir")
):
    """Run terraform import for a specific GCP Pub/Sub subscription."""
    ImportManager(output_dir, "gcp_pubsub_subscription").find_and_import(subscription_id)
