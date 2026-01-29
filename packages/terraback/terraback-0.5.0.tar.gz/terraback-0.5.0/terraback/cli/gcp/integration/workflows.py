from pathlib import Path
from terraback.cli.gcp.session import get_gcp_client
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.gcp.common.error_handler import safe_gcp_operation

def scan_workflows(output_dir: Path, project_id: str = None, location: str = None, region: str = None, zone: str = None, **kwargs):
    """
    Scans for Workflows and generates Terraform code.
    """
    # Use region parameter if location is not provided
    if not location and region:
        location = region
    
    def _scan_workflows():
        workflows_client = get_gcp_client("workflows", "v1")
        
        print(f"Scanning for Workflows...")
        
        # Get all workflows
        workflows = []
        # List all locations first
        if location:
            locations = [f"projects/{project_id or workflows_client.project}/locations/{location}"]
        else:
            # Get all available locations
            locations_response = workflows_client.projects().locations().list(
                name=f"projects/{project_id or workflows_client.project}"
            ).execute()
            locations = [loc['name'] for loc in locations_response.get('locations', [])]
        
        for loc in locations:
            try:
                # List workflows in each location
                request = workflows_client.projects().locations().workflows().list(parent=loc)
                
                while request is not None:
                    response = request.execute()
                    
                    for workflow in response.get('workflows', []):
                        # Extract workflow details
                        workflow_data = {
                            'name': workflow['name'].split('/')[-1],
                            'name_sanitized': workflow['name'].split('/')[-1].replace('-', '_').replace('.', '_').lower(),
                            'region': loc.split('/')[-1],
                            'description': workflow.get('description'),
                            'service_account': workflow.get('serviceAccount'),
                            'source_contents': workflow.get('sourceContents', ''),
                            'revision_id': workflow.get('revisionId'),
                            'create_time': workflow.get('createTime'),
                            'update_time': workflow.get('updateTime'),
                            'revision_create_time': workflow.get('revisionCreateTime'),
                            'labels': workflow.get('labels', {}),
                            'state': workflow.get('state'),
                            'state_error': workflow.get('stateError'),
                            'call_log_level': workflow.get('callLogLevel'),
                            'user_env_vars': workflow.get('userEnvVars', {}),
                            'crypto_key_name': workflow.get('cryptoKeyName'),
                        }
                        
                        workflows.append(workflow_data)
                    
                    request = workflows_client.projects().locations().workflows().list_next(
                        previous_request=request, previous_response=response
                    )
            except Exception as e:
                print(f"  - Warning: Could not scan location {loc}: {e}")
    
        return workflows
    
    # Use safe operation wrapper
    workflows = safe_gcp_operation(
        _scan_workflows, 
        "Workflows API", 
        project_id or "default"
    )
    
    if not workflows:
        print(f"Skipping gcp_workflows_workflow - no resources found")
        return

    output_file = output_dir / "gcp_workflows_workflow.tf"
    generate_tf(workflows, "gcp_workflows_workflow", output_file)
    print(f"Generated Terraform for {len(workflows)} Workflows -> {output_file}")
    
    # Generate imports file
    imports = []
    for workflow in workflows:
        project = project_id or workflows_client.project
        region = workflow['region']
        imports.append({
            "resource_type": "google_workflows_workflow",
            "resource_name": workflow['name_sanitized'],
            "resource_id": f"projects/{project}/locations/{region}/workflows/{workflow['name']}"
        })
    
    generate_imports_file(
        "gcp_workflows_workflow",
        workflows,
        "name",
        output_dir,
        provider="gcp"
    )

def list_workflows(output_dir: Path):
    """List scanned Workflows."""
    tf_file = output_dir / "gcp_workflows_workflow.tf"
    if not tf_file.exists():
        print("No Workflows found. Run 'scan-workflows' first.")
        return
    
    print("Scanned Workflows:")
    print(f"  - Check {tf_file} for details")

def import_workflow(workflow_id: str, output_dir: Path):
    """Import a specific Workflow."""
    imports_file = output_dir / "gcp_workflows_workflow_imports.tf"
    
    if not imports_file.exists():
        print(f"Imports file not found. Run 'scan-workflows' first.")
        return
    
    manager = ImportManager(imports_file)
    manager.run_import("google_workflows_workflow", workflow_id)