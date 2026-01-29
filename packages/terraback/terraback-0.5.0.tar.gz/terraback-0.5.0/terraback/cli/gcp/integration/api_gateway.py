from pathlib import Path
from terraback.cli.gcp.session import get_gcp_client
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.gcp.common.error_handler import safe_gcp_operation

def scan_api_gateways(output_dir: Path, project_id: str = None, location: str = None, region: str = None, zone: str = None, **kwargs):
    """
    Scans for API Gateway resources and generates Terraform code.
    """
    # Use region parameter if location is not provided
    if not location and region:
        location = region
    
    def _scan_api_gateways():
        apigateway_client = get_gcp_client("apigateway", "v1")
        
        print(f"Scanning for API Gateway resources...")
        
        # Get all API Gateway APIs
        apis = []
        
        # List all locations first
        if location:
            locations = [f"projects/{project_id or apigateway_client.project}/locations/{location}"]
        else:
            # For API Gateway, we typically use 'global' location
            locations = [f"projects/{project_id or apigateway_client.project}/locations/global"]
        
        for loc in locations:
            try:
                # List APIs
                request = apigateway_client.projects().locations().apis().list(parent=loc)
                
                while request is not None:
                    response = request.execute()
                    
                    for api in response.get('apis', []):
                        # Extract API details
                        api_data = {
                            'api_id': api['name'].split('/')[-1],
                            'name_sanitized': api['name'].split('/')[-1].replace('-', '_').replace('.', '_').lower(),
                            'display_name': api.get('displayName'),
                            'managed_service': api.get('managedService'),
                            'create_time': api.get('createTime'),
                            'update_time': api.get('updateTime'),
                            'state': api.get('state'),
                            'labels': api.get('labels', {}),
                            'api_configs': [],
                            'gateways': []
                        }
                        
                        # Get API configs for this API
                        try:
                            configs_request = apigateway_client.projects().locations().apis().configs().list(
                                parent=api['name']
                            )
                            
                            while configs_request is not None:
                                configs_response = configs_request.execute()
                                
                                for config in configs_response.get('apiConfigs', []):
                                    config_data = {
                                        'api_config_id': config['name'].split('/')[-1],
                                        'name_sanitized': config['name'].split('/')[-1].replace('-', '_').replace('.', '_').lower(),
                                        'display_name': config.get('displayName'),
                                        'service_config_id': config.get('serviceConfigId'),
                                        'state': config.get('state'),
                                        'create_time': config.get('createTime'),
                                        'update_time': config.get('updateTime'),
                                        'labels': config.get('labels', {}),
                                    }
                                    
                                    # Handle OpenAPI specs
                                    if config.get('openapiDocuments'):
                                        config_data['openapi_documents'] = []
                                        for doc in config['openapiDocuments']:
                                            config_data['openapi_documents'].append({
                                                'document': {
                                                    'path': doc['document'].get('path'),
                                                    'contents': doc['document'].get('contents', '')
                                                }
                                            })
                                    
                                    # Handle gRPC services
                                    if config.get('grpcServices'):
                                        config_data['grpc_services'] = []
                                        for service in config['grpcServices']:
                                            service_data = {}
                                            if service.get('fileDescriptorSet'):
                                                service_data['file_descriptor_set'] = {
                                                    'path': service['fileDescriptorSet'].get('path'),
                                                    'contents': service['fileDescriptorSet'].get('contents', '')
                                                }
                                            if service.get('source'):
                                                service_data['source'] = []
                                                for src in service['source']:
                                                    service_data['source'].append({
                                                        'path': src.get('path'),
                                                        'contents': src.get('contents', '')
                                                    })
                                            config_data['grpc_services'].append(service_data)
                                    
                                    # Handle managed service configs
                                    if config.get('managedServiceConfigs'):
                                        config_data['managed_service_configs'] = []
                                        for ms_config in config['managedServiceConfigs']:
                                            config_data['managed_service_configs'].append({
                                                'path': ms_config.get('path'),
                                                'contents': ms_config.get('contents', '')
                                            })
                                    
                                    # Handle gateway config
                                    if config.get('gatewayConfig'):
                                        config_data['gateway_config'] = {
                                            'backend_config': {
                                                'google_service_account': config['gatewayConfig']['backendConfig'].get('googleServiceAccount')
                                            }
                                        }
                                    
                                    api_data['api_configs'].append(config_data)
                                
                                configs_request = apigateway_client.projects().locations().apis().configs().list_next(
                                    configs_request, configs_response
                                )
                        except Exception as e:
                            print(f"  - Warning: Could not get configs for API {api['name']}: {e}")
                        
                        # Get gateways for this API
                        try:
                            gateways_request = apigateway_client.projects().locations().gateways().list(
                                parent=loc,
                                filter=f"api=\"{api['name']}\""
                            )
                            
                            while gateways_request is not None:
                                gateways_response = gateways_request.execute()
                                
                                for gateway in gateways_response.get('gateways', []):
                                    gateway_data = {
                                        'gateway_id': gateway['name'].split('/')[-1],
                                        'name_sanitized': gateway['name'].split('/')[-1].replace('-', '_').replace('.', '_').lower(),
                                        'display_name': gateway.get('displayName'),
                                        'api_config': gateway.get('apiConfig'),
                                        'state': gateway.get('state'),
                                        'default_hostname': gateway.get('defaultHostname'),
                                        'create_time': gateway.get('createTime'),
                                        'update_time': gateway.get('updateTime'),
                                        'labels': gateway.get('labels', {}),
                                    }
                                    
                                    # Map the api_config to the sanitized name
                                    if gateway_data['api_config']:
                                        config_id = gateway_data['api_config'].split('/')[-1]
                                        for config in api_data['api_configs']:
                                            if config['api_config_id'] == config_id:
                                                gateway_data['api_config_name_sanitized'] = config['name_sanitized']
                                                break
                                    
                                    api_data['gateways'].append(gateway_data)
                                
                                gateways_request = apigateway_client.projects().locations().gateways().list_next(
                                    gateways_request, gateways_response
                                )
                        except Exception as e:
                            print(f"  - Warning: Could not get gateways for API {api['name']}: {e}")
                        
                        apis.append(api_data)
                    
                    request = apigateway_client.projects().locations().apis().list_next(
                        request, response
                    )
            except Exception as e:
                print(f"  - Warning: Could not scan location {loc}: {e}")
        
        return apis
    
    # Use safe operation wrapper
    apis = safe_gcp_operation(
        _scan_api_gateways, 
        "API Gateway API", 
        project_id or "default"
    )
    
    output_file = output_dir / "gcp_api_gateway_api.tf"
    generate_tf(apis, "gcp_api_gateway_api", output_file)
    print(f"Generated Terraform for {len(apis)} API Gateway APIs -> {output_file}")
    
    # Generate imports file
    imports = []
    for api in apis:
        project = project_id or "default"
        imports.append({
            "resource_type": "google_api_gateway_api",
            "resource_name": api['name_sanitized'],
            "resource_id": f"projects/{project}/locations/global/apis/{api['api_id']}"
        })
        
        # Add imports for API configs
        for config in api.get('api_configs', []):
            imports.append({
                "resource_type": "google_api_gateway_api_config",
                "resource_name": f"{api['name_sanitized']}_{config['name_sanitized']}",
                "resource_id": f"projects/{project}/locations/global/apis/{api['api_id']}/configs/{config['api_config_id']}"
            })
        
        # Add imports for gateways
        for gateway in api.get('gateways', []):
            region = gateway.get('region', 'us-central1')  # Default region
            imports.append({
                "resource_type": "google_api_gateway_gateway",
                "resource_name": f"{api['name_sanitized']}_{gateway['name_sanitized']}",
                "resource_id": f"projects/{project}/locations/{region}/gateways/{gateway['gateway_id']}"
            })
    
    if apis:
        imports_file = output_dir / "gcp_api_gateway_api_imports.json"
        generate_imports_file(imports, "resource_id", output_dir)
        print(f"Generated imports file with {len(imports)} resources")

def list_api_gateways(output_dir: Path):
    """List scanned API Gateway resources."""
    tf_file = output_dir / "gcp_api_gateway_api.tf"
    if not tf_file.exists():
        print("No API Gateway resources found. Run 'scan-api-gateway' first.")
        return
    
    print("Scanned API Gateway resources:")
    print(f"  - Check {tf_file} for details")

def import_api_gateway(resource_id: str, output_dir: Path):
    """Import a specific API Gateway resource."""
    imports_file = output_dir / "gcp_api_gateway_api_imports.tf"
    
    if not imports_file.exists():
        print(f"Imports file not found. Run 'scan-api-gateway' first.")
        return
    
    manager = ImportManager(imports_file)
    manager.run_import("google_api_gateway_api", resource_id)