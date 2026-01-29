from pathlib import Path
from terraback.cli.gcp.session import get_gcp_client
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.gcp.common.error_handler import safe_gcp_operation

def scan_cloud_tasks_queues(output_dir: Path, project_id: str = None, location: str = None, region: str = None, zone: str = None, **kwargs):
    """
    Scans for Cloud Tasks queues and generates Terraform code.
    """
    # Use region parameter if location is not provided
    if not location and region:
        location = region
    
    def _scan_cloud_tasks_queues():
        tasks_client = get_gcp_client("cloudtasks", "v2")
        
        print(f"Scanning for Cloud Tasks queues...")
        
        # Get all queues
        queues = []
        
        # List all locations first
        if location:
            locations = [f"projects/{project_id or tasks_client.project}/locations/{location}"]
        else:
            # Get all available locations
            locations_response = tasks_client.projects().locations().list(
                name=f"projects/{project_id or tasks_client.project}"
            ).execute()
            locations = [loc['name'] for loc in locations_response.get('locations', [])]
        
        for loc in locations:
            try:
                # List queues in each location
                request = tasks_client.projects().locations().queues().list(parent=loc)
                
                while request is not None:
                    response = request.execute()
                    
                    for queue in response.get('queues', []):
                        # Extract queue details
                        queue_data = {
                            'name': queue['name'].split('/')[-1],
                            'name_sanitized': queue['name'].split('/')[-1].replace('-', '_').replace('.', '_').lower(),
                            'location': loc.split('/')[-1],
                            'state': queue.get('state'),
                            'purge_time': queue.get('purgeTime'),
                            'labels': queue.get('labels', {}),
                        }
                        
                        # Handle rate limits
                        if queue.get('rateLimits'):
                            queue_data['rate_limits'] = {
                                'max_dispatches_per_second': queue['rateLimits'].get('maxDispatchesPerSecond'),
                                'max_burst_size': queue['rateLimits'].get('maxBurstSize'),
                                'max_concurrent_dispatches': queue['rateLimits'].get('maxConcurrentDispatches')
                            }
                        
                        # Handle retry config
                        if queue.get('retryConfig'):
                            retry_config = queue['retryConfig']
                            queue_data['retry_config'] = {
                                'max_attempts': retry_config.get('maxAttempts'),
                                'max_retry_duration': retry_config.get('maxRetryDuration'),
                                'min_backoff': retry_config.get('minBackoff'),
                                'max_backoff': retry_config.get('maxBackoff'),
                                'max_doublings': retry_config.get('maxDoublings')
                            }
                        
                        # Handle stackdriver logging config
                        if queue.get('stackdriverLoggingConfig'):
                            queue_data['stackdriver_logging_config'] = {
                                'sampling_ratio': queue['stackdriverLoggingConfig'].get('samplingRatio', 0.0)
                            }
                        
                        # Handle app engine routing override (if applicable)
                        if queue.get('appEngineRoutingOverride'):
                            routing = queue['appEngineRoutingOverride']
                            queue_data['app_engine_routing_override'] = {
                                'service': routing.get('service'),
                                'version': routing.get('version'),
                                'instance': routing.get('instance'),
                                'host': routing.get('host')
                            }
                        
                        queues.append(queue_data)
                    
                    request = tasks_client.projects().locations().queues().list_next(
                        request, response
                    )
            except Exception as e:
                print(f"  - Warning: Could not scan location {loc}: {e}")
        
        return queues
    
    # Use safe operation wrapper
    queues = safe_gcp_operation(
        _scan_cloud_tasks_queues, 
        "Cloud Tasks API", 
        project_id or "default"
    )
    
    if queues:
        output_file = output_dir / "gcp_cloud_tasks_queue.tf"
        generate_tf(queues, "gcp_cloud_tasks_queue", output_file, provider="gcp")
        print(f"Generated Terraform for {len(queues)} Cloud Tasks queues -> {output_file}")
        
        # Generate imports file
        generate_imports_file(
            "gcp_cloud_tasks_queue",
            queues,
            "name",
            output_dir,
            provider="gcp"
        )
        print(f"Generated imports file with {len(queues)} resources")
    else:
        print("No Cloud Tasks queues found.")

def list_cloud_tasks_queues(output_dir: Path):
    """List scanned Cloud Tasks queues."""
    import json
    
    tf_file = output_dir / "gcp_cloud_tasks_queue.tf"
    if not tf_file.exists():
        print("No Cloud Tasks queues found. Run 'scan-queues' first.")
        return
    
    # Read the generated file to extract queue information
    # This is a simplified implementation - in practice, you'd parse the TF file
    print("Scanned Cloud Tasks queues:")
    print(f"  - Check {tf_file} for details")

def import_cloud_tasks_queue(queue_id: str, output_dir: Path):
    """Import a specific Cloud Tasks queue."""
    imports_file = output_dir / "gcp_cloud_tasks_queue_imports.tf"
    
    if not imports_file.exists():
        print(f"Imports file not found. Run 'scan-queues' first.")
        return
    
    manager = ImportManager(imports_file)
    manager.run_import("google_cloud_tasks_queue", queue_id)