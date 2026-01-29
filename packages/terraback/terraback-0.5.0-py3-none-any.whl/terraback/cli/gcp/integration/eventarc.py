from pathlib import Path
from terraback.cli.gcp.session import get_gcp_client
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.gcp.common.error_handler import safe_gcp_operation
from terraback.cli.gcp.common.error_handler import safe_gcp_operation

def scan_eventarc_triggers(output_dir: Path, project_id: str = None, location: str = None, region: str = None, zone: str = None, **kwargs):
    """
    Scans for Eventarc triggers and generates Terraform code.
    """
    # Use region parameter if location is not provided
    if not location and region:
        location = region
    
    def _scan_eventarc_triggers():
        eventarc_client = get_gcp_client("eventarc", "v1")
        
        print(f"Scanning for Eventarc triggers...")
        
        # Get all triggers
        triggers = []
        # List all locations first
        if location:
            locations = [f"projects/{project_id or eventarc_client.project}/locations/{location}"]
        else:
            # Get all available locations
            locations_response = eventarc_client.projects().locations().list(
                name=f"projects/{project_id or eventarc_client.project}"
            ).execute()
            locations = [loc['name'] for loc in locations_response.get('locations', [])]
        
        for loc in locations:
            try:
                # List triggers in each location
                request = eventarc_client.projects().locations().triggers().list(parent=loc)
                
                while request is not None:
                    response = request.execute()
                    
                    for trigger in response.get('triggers', []):
                        # Extract trigger details
                        trigger_data = {
                            'name': trigger['name'].split('/')[-1],
                            'name_sanitized': trigger['name'].split('/')[-1].replace('-', '_').replace('.', '_').lower(),
                            'location': loc.split('/')[-1],
                            'service_account': trigger.get('serviceAccount'),
                            'event_data_content_type': trigger.get('eventDataContentType'),
                            'create_time': trigger.get('createTime'),
                            'update_time': trigger.get('updateTime'),
                            'etag': trigger.get('etag'),
                            'uid': trigger.get('uid'),
                            'labels': trigger.get('labels', {}),
                            'matching_criteria': [],
                            'destination': {},
                        }
                        
                        # Handle event filters (matching criteria)
                        if trigger.get('eventFilters'):
                            for filter in trigger['eventFilters']:
                                criteria = {
                                    'attribute': filter.get('attribute'),
                                    'value': filter.get('value'),
                                }
                                if filter.get('operator'):
                                    criteria['operator'] = filter['operator']
                                trigger_data['matching_criteria'].append(criteria)
                        
                        # Handle destination
                        destination = trigger.get('destination', {})
                        if destination.get('cloudRunService'):
                            service = destination['cloudRunService']
                            trigger_data['destination']['cloud_run_service'] = {
                                'service': service.get('service'),
                                'region': service.get('region'),
                                'path': service.get('path'),
                            }
                        elif destination.get('cloudFunction'):
                            trigger_data['destination']['cloud_function'] = destination['cloudFunction']
                        elif destination.get('workflow'):
                            trigger_data['destination']['workflow'] = destination['workflow']
                        elif destination.get('gke'):
                            gke = destination['gke']
                            trigger_data['destination']['gke'] = {
                                'cluster': gke.get('cluster'),
                                'location': gke.get('location'),
                                'namespace': gke.get('namespace'),
                                'service': gke.get('service'),
                                'path': gke.get('path'),
                            }
                        elif destination.get('httpEndpoint'):
                            trigger_data['destination']['http_endpoint'] = {
                                'uri': destination['httpEndpoint'].get('uri')
                            }
                        
                        # Handle network config in destination
                        if destination.get('networkConfig'):
                            trigger_data['destination']['network_config'] = {
                                'network_attachment': destination['networkConfig'].get('networkAttachment')
                            }
                        
                        # Handle transport
                        if trigger.get('transport'):
                            transport = trigger['transport']
                            trigger_data['transport'] = {}
                            
                            if transport.get('pubsub'):
                                pubsub = transport['pubsub']
                                trigger_data['transport']['pubsub'] = {}
                                if pubsub.get('topic'):
                                    trigger_data['transport']['pubsub']['topic'] = pubsub['topic']
                                if pubsub.get('subscription'):
                                    trigger_data['transport']['pubsub']['subscription'] = pubsub['subscription']
                        
                        # Handle channel if present
                        if trigger.get('channel'):
                            trigger_data['channel'] = trigger['channel']
                        
                        # Handle conditions
                        if trigger.get('conditions'):
                            trigger_data['conditions'] = trigger['conditions']
                        
                        triggers.append(trigger_data)
                    
                    request = eventarc_client.projects().locations().triggers().list_next(
                        previous_request=request, previous_response=response
                    )
            except Exception as e:
                print(f"  - Warning: Could not scan location {loc}: {e}")
    
        return triggers
    
    # Use safe operation wrapper
    triggers = safe_gcp_operation(
        _scan_eventarc_triggers, 
        "Eventarc API", 
        project_id or "default"
    )
    
    if not triggers:
        print(f"Skipping gcp_eventarc_trigger - no resources found")
        return

    output_file = output_dir / "gcp_eventarc_trigger.tf"
    generate_tf(triggers, "gcp_eventarc_trigger", output_file)
    print(f"Generated Terraform for {len(triggers)} Eventarc triggers -> {output_file}")
    
    # Generate imports file
    imports = []
    for trigger in triggers:
        project = project_id or eventarc_client.project
        location = trigger['location']
        imports.append({
            "resource_type": "google_eventarc_trigger",
            "resource_name": trigger['name_sanitized'],
            "resource_id": f"projects/{project}/locations/{location}/triggers/{trigger['name']}"
        })
    
    generate_imports_file(
        "gcp_eventarc_trigger",
        triggers,
        "name",
        output_dir,
        provider="gcp"
    )

def list_eventarc_triggers(output_dir: Path):
    """List scanned Eventarc triggers."""
    tf_file = output_dir / "gcp_eventarc_trigger.tf"
    if not tf_file.exists():
        print("No Eventarc triggers found. Run 'scan-eventarc' first.")
        return
    
    print("Scanned Eventarc triggers:")
    print(f"  - Check {tf_file} for details")

def import_eventarc_trigger(trigger_id: str, output_dir: Path):
    """Import a specific Eventarc trigger."""
    imports_file = output_dir / "gcp_eventarc_trigger_imports.tf"
    
    if not imports_file.exists():
        print(f"Imports file not found. Run 'scan-eventarc' first.")
        return
    
    manager = ImportManager(imports_file)
    manager.run_import("google_eventarc_trigger", trigger_id)