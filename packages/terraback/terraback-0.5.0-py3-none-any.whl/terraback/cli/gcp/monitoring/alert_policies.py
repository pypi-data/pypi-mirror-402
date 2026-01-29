from pathlib import Path
from typing import List, Dict, Any, Optional
from terraback.cli.gcp.session import get_gcp_credentials
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from google.cloud import monitoring_v3
from google.api_core.exceptions import GoogleAPIError


def _process_alert_policy_data(policy: Any, project_id: str) -> Dict[str, Any]:
    """Process GCP alert policy data for Terraform generation."""
    policy_data = {
        'display_name': policy.display_name,
        'combiner': policy.combiner.name,
        'enabled': policy.enabled.value if hasattr(policy.enabled, 'value') else policy.enabled,
        'project': project_id,
        'name': policy.name,
        'conditions': [],
        'documentation': {},
        'notification_channels': list(policy.notification_channels) if policy.notification_channels else []
    }
    
    # Process conditions
    for condition in policy.conditions:
        cond_data = {
            'display_name': condition.display_name,
            'name': condition.name
        }
        
        if hasattr(condition, 'condition_threshold'):
            threshold = condition.condition_threshold
            cond_data['condition_threshold'] = {
                'filter': threshold.filter,
                'duration': threshold.duration.seconds if hasattr(threshold.duration, 'seconds') else 0,
                'comparison': threshold.comparison.name,
                'threshold_value': threshold.threshold_value if hasattr(threshold, 'threshold_value') else None
            }
            
            if threshold.aggregations:
                cond_data['condition_threshold']['aggregations'] = []
                for agg in threshold.aggregations:
                    agg_data = {
                        'alignment_period': agg.alignment_period.seconds if hasattr(agg.alignment_period, 'seconds') else 0,
                        'per_series_aligner': agg.per_series_aligner.name if hasattr(agg, 'per_series_aligner') else 'ALIGN_NONE'
                    }
                    cond_data['condition_threshold']['aggregations'].append(agg_data)
                    
        policy_data['conditions'].append(cond_data)
    
    # Process documentation
    if policy.documentation:
        policy_data['documentation'] = {
            'content': policy.documentation.content,
            'mime_type': policy.documentation.mime_type
        }
    
    # Extract labels if available
    if policy.user_labels:
        policy_data['labels'] = dict(policy.user_labels)
    
    return policy_data


def get_alert_policy_data(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch Alert Policy data from GCP.
    
    Args:
        project_id: GCP project ID. If not provided, uses default from credentials.
    
    Returns:
        List of alert policy data dictionaries
    """
    credentials, default_project = get_gcp_credentials()
    project_id = project_id or default_project
    
    client = monitoring_v3.AlertPolicyServiceClient(credentials=credentials)
    policies_data = []
    
    try:
        # List alert policies for the project
        project_name = f"projects/{project_id}"
        
        for policy in client.list_alert_policies(name=project_name):
            policy_data = _process_alert_policy_data(policy, project_id)
            policies_data.append(policy_data)
                
    except GoogleAPIError as e:
        print(f"Error fetching GCP alert policies: {e}")
        
    return policies_data


def scan_alert_policies(output_dir: Path, project_id: Optional[str] = None):
    """
    Scan GCP alert policies and generate Terraform configuration.
    
    Args:
        output_dir: Directory to save Terraform files
        project_id: GCP project ID
    """
    policies = get_alert_policy_data(project_id)
    
    if not policies:
        print("No alert policies found.")
        return
        
    output_file = output_dir / "gcp_monitoring_alert_policies.tf"
    generate_tf(policies, "gcp_monitoring_alert_policies", output_file)
    print(f"Generated Terraform for {len(policies)} GCP Alert Policies -> {output_file}")
    
    # Generate import file
    generate_imports_file(
        "gcp_monitoring_alert_policies", 
        policies, 
        remote_resource_id_key="name",
        output_dir=output_dir, provider="gcp"
    )


def list_alert_policies(output_dir: Path):
    """List all imported GCP alert policies."""
    ImportManager(output_dir, "gcp_monitoring_alert_policies").list_all()


def import_alert_policy(policy_name: str, output_dir: Path):
    """Import a specific GCP alert policy."""
    ImportManager(output_dir, "gcp_monitoring_alert_policies").find_and_import(policy_name)