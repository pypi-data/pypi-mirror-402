from pathlib import Path
from typing import List, Dict, Any, Optional
from terraback.cli.gcp.session import get_gcp_credentials
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from google.cloud import compute_v1
from google.api_core.exceptions import GoogleAPIError


def _process_backend_bucket_data(bucket: Any, project_id: str) -> Dict[str, Any]:
    """Process GCP backend bucket data for Terraform generation."""
    bucket_data = {
        'name': bucket.name,
        'description': bucket.description if hasattr(bucket, 'description') else '',
        'bucket_name': bucket.bucket_name,
        'project': project_id,
        'enable_cdn': bucket.enable_cdn if hasattr(bucket, 'enable_cdn') else False,
        'self_link': bucket.self_link if hasattr(bucket, 'self_link') else ''
    }
    
    # Extract CDN policy if available
    if hasattr(bucket, 'cdn_policy') and bucket.cdn_policy:
        cdn_policy = bucket.cdn_policy
        bucket_data['cdn_policy'] = {
            'cache_mode': cdn_policy.cache_mode if hasattr(cdn_policy, 'cache_mode') else None,
            'client_ttl': cdn_policy.client_ttl if hasattr(cdn_policy, 'client_ttl') else None,
            'default_ttl': cdn_policy.default_ttl if hasattr(cdn_policy, 'default_ttl') else None,
            'max_ttl': cdn_policy.max_ttl if hasattr(cdn_policy, 'max_ttl') else None,
            'negative_caching': cdn_policy.negative_caching if hasattr(cdn_policy, 'negative_caching') else False,
            'serve_while_stale': cdn_policy.serve_while_stale if hasattr(cdn_policy, 'serve_while_stale') else None
        }
        
        # Negative caching policies
        if hasattr(cdn_policy, 'negative_caching_policy') and cdn_policy.negative_caching_policy:
            bucket_data['cdn_policy']['negative_caching_policy'] = []
            for policy in cdn_policy.negative_caching_policy:
                bucket_data['cdn_policy']['negative_caching_policy'].append({
                    'code': policy.code,
                    'ttl': policy.ttl if hasattr(policy, 'ttl') else 0
                })
    
    # Extract custom headers if available
    if hasattr(bucket, 'custom_response_headers') and bucket.custom_response_headers:
        bucket_data['custom_response_headers'] = list(bucket.custom_response_headers)
    
    return bucket_data


def get_backend_bucket_data(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch Backend Bucket data from GCP.
    
    Args:
        project_id: GCP project ID. If not provided, uses default from credentials.
    
    Returns:
        List of backend bucket data dictionaries
    """
    credentials, default_project = get_gcp_credentials()
    project_id = project_id or default_project
    
    client = compute_v1.BackendBucketsClient(credentials=credentials)
    buckets_data = []
    
    try:
        # List backend buckets for the project
        request = compute_v1.ListBackendBucketsRequest(project=project_id)
        
        for bucket in client.list(request=request):
            bucket_data = _process_backend_bucket_data(bucket, project_id)
            buckets_data.append(bucket_data)
                
    except GoogleAPIError as e:
        print(f"Error fetching GCP backend buckets: {e}")
        
    return buckets_data


def scan_backend_buckets(output_dir: Path, project_id: Optional[str] = None):
    """
    Scan GCP backend buckets and generate Terraform configuration.
    
    Args:
        output_dir: Directory to save Terraform files
        project_id: GCP project ID
    """
    buckets = get_backend_bucket_data(project_id)
    
    if not buckets:
        print("No backend buckets found.")
        return
        
    output_file = output_dir / "gcp_backend_buckets.tf"
    generate_tf(buckets, "gcp_backend_buckets", output_file)
    print(f"Generated Terraform for {len(buckets)} GCP Backend Buckets -> {output_file}")
    
    # Generate import file
    generate_imports_file(
        "gcp_backend_buckets", 
        buckets, 
        remote_resource_id_key="name",
        output_dir=output_dir, provider="gcp"
    )


def list_backend_buckets(output_dir: Path):
    """List all imported GCP backend buckets."""
    ImportManager(output_dir, "gcp_backend_buckets").list_all()


def import_backend_bucket(bucket_name: str, output_dir: Path):
    """Import a specific GCP backend bucket."""
    ImportManager(output_dir, "gcp_backend_buckets").find_and_import(bucket_name)