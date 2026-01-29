from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import concurrent.futures
from dataclasses import dataclass, field
import json
from terraback.cli.aws.session import get_boto_session
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.terraform_generator.filters import terraform_name
from terraback.utils.importer import ImportManager


def deduplicate_by_key(seq: List[Dict[str, Any]], key):
    """Return a new list with items unique by the given key or keys."""
    seen = set()
    unique = []
    for item in seq:
        if isinstance(key, (list, tuple)):
            key_val = tuple(item.get(k) for k in key)
        else:
            key_val = item.get(key)
        if key_val not in seen:
            seen.add(key_val)
            unique.append(item)
    return unique


@dataclass
class ApiGatewayResources:
    """Container for all API Gateway resources discovered during scanning."""
    apis: List[Dict[str, Any]] = field(default_factory=list)
    resources: List[Dict[str, Any]] = field(default_factory=list)
    methods: List[Dict[str, Any]] = field(default_factory=list)
    integrations: List[Dict[str, Any]] = field(default_factory=list)
    deployments: List[Dict[str, Any]] = field(default_factory=list)
    stages: List[Dict[str, Any]] = field(default_factory=list)
    lambda_permissions: List[Dict[str, Any]] = field(default_factory=list)
    
    def extend(self, other: 'ApiGatewayResources'):
        """Extend this container with resources from another container."""
        self.apis.extend(other.apis)
        self.resources.extend(other.resources)
        self.methods.extend(other.methods)
        self.integrations.extend(other.integrations)
        self.deployments.extend(other.deployments)
        self.stages.extend(other.stages)
        self.lambda_permissions.extend(other.lambda_permissions)


class ApiGatewayScanner:
    """Scanner for API Gateway resources with optimized processing."""

    def __init__(self, apigw_client, lambda_client, region: str):
        self.client = apigw_client
        self.lambda_client = lambda_client
        self.region = region
    
    def get_all_apis(self) -> List[Dict[str, Any]]:
        """Fetch all REST APIs efficiently."""
        apis = []
        paginator = self.client.get_paginator('get_rest_apis')
        for page in paginator.paginate():
            for api in page.get('items', []):
                # Use ID as part of the name to ensure uniqueness
                api['name_sanitized'] = terraform_name(f"{api.get('name', 'api')}_{api['id']}")
                apis.append(api)
        return apis
    
    def get_api_resources(self, api_id: str) -> List[Dict[str, Any]]:
        """Fetch all resources for an API with proper ID mapping."""
        resources = []
        paginator = self.client.get_paginator('get_resources')
        
        for page in paginator.paginate(restApiId=api_id):
            for resource in page.get('items', []):
                resource['rest_api_id'] = api_id  # Add for composite keys
                resource['name_sanitized'] = f"{api_id}_{resource['id']}"
                resources.append(resource)
        
        return resources
    
    def get_deployments_and_stages(self, api_id: str) -> Tuple[List[Dict], List[Dict]]:
        """Fetch deployments and stages with proper ID mapping."""
        try:
            # Get deployments
            deployments_response = self.client.get_deployments(restApiId=api_id)
            deployments = []
            for dep in deployments_response.get('items', []):
                dep_with_api = {**dep, 'rest_api_id': api_id}
                dep_with_api['name_sanitized'] = f"{api_id}_deployment_{dep['id']}"
                deployments.append(dep_with_api)
            
            # Get stages
            stages_response = self.client.get_stages(restApiId=api_id)
            stages = [
                {**stage, 'rest_api_id': api_id} 
                for stage in stages_response.get('items', [])
            ]
            
            return deployments, stages
            
        except Exception as e:
            print(f"  - Warning: Could not fetch deployments/stages for API {api_id}: {e}")
            return [], []
    
    def extract_lambda_function_name(self, uri: str) -> Optional[str]:
        """Extract Lambda function name from integration URI."""
        try:
            if 'lambda' not in uri:
                return None
            # URI format: arn:aws:apigateway:region:lambda:path/2015-03-31/functions/arn:aws:lambda:region:account:function:FunctionName/invocations
            # Extract the function name which comes after ":function:"
            if ':function:' in uri:
                parts = uri.split(':function:')
                if len(parts) > 1:
                    # Get everything after :function: and before /invocations
                    function_part = parts[1]
                    return function_part.split('/')[0]
            return None
        except (IndexError, AttributeError):
            return None
    
    def process_method_integration(self, api_id: str, resource_id: str, 
                                 method_name: str, method_details: Dict) -> Tuple[Dict, Optional[Dict], Optional[Dict]]:
        """Process a single method and its integration."""
        # Get full method details
        try:
            full_method = self.client.get_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=method_name
            )
        except Exception:
            full_method = method_details
        
        # Build method info
        method_info = {
            "rest_api_id": api_id,
            "resource_id": resource_id,
            "http_method": method_name,
            "name_sanitized": f"{api_id}_{resource_id}_{method_name.lower()}",
            "authorizationType": full_method.get('authorizationType', 'NONE'),
            "authorizerId": full_method.get('authorizerId'),
            "apiKeyRequired": full_method.get('apiKeyRequired', False),
            "requestValidatorId": full_method.get('requestValidatorId'),
            "authorizationScopes": full_method.get('authorizationScopes'),
            "requestModels": full_method.get('requestModels'),
            "requestParameters": full_method.get('requestParameters')
        }
        
        integration_info = None
        lambda_permission_info = None
        
        # Process integration if present
        integration_data = full_method.get('methodIntegration')
        if integration_data:
            integration_info = {
                "rest_api_id": api_id,
                "resource_id": resource_id,
                "http_method": method_name,
                "name_sanitized": f"{api_id}_{resource_id}_{method_name.lower()}",
                **integration_data
            }
            
            # Create Lambda permission for Lambda integrations
            if (integration_data.get('type') == 'AWS_PROXY' and
                integration_data.get('uri')):

                function_name = self.extract_lambda_function_name(integration_data['uri'])
                if function_name:
                    # Extract the qualifier (version/alias) if present
                    qualifier = None
                    if ':' in function_name and not function_name.endswith(':$LATEST'):
                        parts = function_name.split(':')
                        if len(parts) == 2:
                            function_name, qualifier = parts
                    
                    try:
                        # Get the policy using the base function name
                        policy_response = self.lambda_client.get_policy(FunctionName=function_name)
                        policy_doc = json.loads(policy_response.get('Policy', '{}'))
                        statements = policy_doc.get('Statement', [])
                        
                        # Find the matching statement for this API Gateway
                        for stmt in statements:
                            principal = stmt.get('Principal')
                            if isinstance(principal, dict):
                                principal = principal.get('Service')
                            if principal != 'apigateway.amazonaws.com':
                                continue
                                
                            # Check if this statement matches our API
                            condition = stmt.get('Condition', {})
                            source_arn = None
                            source_account = None
                            
                            # Extract source ARN
                            for arn_key in ('ArnLike', 'ArnEquals'):
                                arn_dict = condition.get(arn_key, {})
                                if 'AWS:SourceArn' in arn_dict:
                                    source_arn = arn_dict['AWS:SourceArn']
                                    break
                            
                            # Extract source account
                            for acct_key in ('StringEquals', 'StringLike'):
                                acct_dict = condition.get(acct_key, {})
                                if 'AWS:SourceAccount' in acct_dict:
                                    source_account = acct_dict['AWS:SourceAccount']
                                    break
                            
                            # Check if this statement is for our API
                            if source_arn and api_id in source_arn:
                                sid = stmt.get('Sid')
                                if sid:
                                    lambda_permission_info = {
                                        "rest_api_id": api_id,
                                        "function_name": function_name,
                                        "statement_id": sid,
                                        "source_arn": source_arn,
                                        "source_account": source_account,
                                        "qualifier": qualifier,
                                        "name_sanitized": terraform_name(f"{function_name}_{sid}")
                                    }
                                    break
                    except self.lambda_client.exceptions.ResourceNotFoundException:
                        print(f"    - Warning: Lambda function {function_name} not found")
                    except Exception as e:
                        print(f"    - Warning: Could not retrieve policy for function {function_name}: {e}")
        
        return method_info, integration_info, lambda_permission_info
    
    def process_resource_methods(self, api_id: str, resource: Dict[str, Any]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Process all methods for a single resource."""
        methods, integrations, lambda_permissions = [], [], []
        resource_id = resource['id']
        
        for method_name, method_details in resource.get('resourceMethods', {}).items():
            method, integration, lambda_perm = self.process_method_integration(
                api_id, resource_id, method_name, method_details
            )
            
            methods.append(method)
            if integration:
                integrations.append(integration)
            if lambda_perm:
                lambda_permissions.append(lambda_perm)
        
        return methods, integrations, lambda_permissions
    
    def scan_single_api(self, api: Dict[str, Any]) -> ApiGatewayResources:
        """Scan a single API and return all its resources."""
        api_id = api['id']
        api_name = api.get('name', 'Unknown')
        
        print(f"  - Processing API: {api_name} ({api_id})")
        
        resources = ApiGatewayResources(apis=[api])
        
        # Get API resources
        api_resources = self.get_api_resources(api_id)
        # Filter out root resources (path "/") as they already exist
        resources.resources = [r for r in api_resources if r.get('path') != '/']
        
        # Process methods and integrations
        for resource in api_resources:
            methods, integrations, lambda_permissions = self.process_resource_methods(api_id, resource)
            resources.methods.extend(methods)
            resources.integrations.extend(integrations)
            resources.lambda_permissions.extend(lambda_permissions)
        
        # Get deployments and stages
        deployments, stages = self.get_deployments_and_stages(api_id)
        resources.deployments = deployments
        resources.stages = stages
        
        return resources


def scan_apis_parallel(scanner: ApiGatewayScanner, apis: List[Dict[str, Any]], max_workers: int = 5) -> ApiGatewayResources:
    """Process multiple APIs in parallel using the scanner."""
    combined_resources = ApiGatewayResources()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all API processing tasks
        future_to_api = {
            executor.submit(scanner.scan_single_api, api): api 
            for api in apis
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_api):
            api = future_to_api[future]
            try:
                api_resources = future.result()
                combined_resources.extend(api_resources)
            except Exception as exc:
                api_name = api.get('name', 'Unknown')
                print(f"  - Error processing API {api_name}: {exc}")
    
    return combined_resources


# Configuration for Terraform file generation
TERRAFORM_CONFIGS = [
    ("apis", "api_gateway_rest_api", "id", None),
    ("resources", "api_gateway_resource", "id", ['rest_api_id', 'id']),
    ("methods", "api_gateway_method", "http_method", ['rest_api_id', 'resource_id', 'http_method']),
    ("integrations", "api_gateway_integration", "http_method", ['rest_api_id', 'resource_id', 'http_method']),
    ("deployments", "api_gateway_deployment", "id", ['rest_api_id', 'id']),
    ("stages", "api_gateway_stage", "stageName", ['rest_api_id', 'stageName']),
    ("lambda_permissions", "lambda_permission", "statement_id", ['function_name', 'statement_id'])
]


def generate_terraform_files(resources: ApiGatewayResources, output_dir: Path):
    """Generate all Terraform files and import files efficiently."""
    for attr_name, resource_type, id_key, composite_keys in TERRAFORM_CONFIGS:
        resource_list = getattr(resources, attr_name)

        if not resource_list:
            continue

        dedup_key = composite_keys if composite_keys else id_key
        if attr_name == "apis":
            dedup_key = ("id", "name_sanitized")
        if dedup_key:
            resource_list = deduplicate_by_key(resource_list, dedup_key)
            setattr(resources, attr_name, resource_list)
            
        output_file = output_dir / f"{resource_type}.tf"
        generate_tf(resource_list, resource_type, output_file)
        
        # Generate imports file if we have an ID key
        if id_key:
            generate_imports_file(
                resource_type, 
                resource_list, 
                id_key, 
                output_dir, 
                composite_keys=composite_keys, provider="aws"
            )
        
        resource_name = resource_type.replace('_', ' ').title()
        print(f"Generated Terraform for {len(resource_list)} {resource_name}s.")


def print_scan_summary(resources: ApiGatewayResources):
    """Print a summary of the scan results."""
    print(f"\nScan complete! Summary:")
    print(f"  - APIs: {len(resources.apis)}")
    print(f"  - Resources: {len(resources.resources)}")
    print(f"  - Methods: {len(resources.methods)}")
    print(f"  - Integrations: {len(resources.integrations)}")
    print(f"  - Deployments: {len(resources.deployments)}")
    print(f"  - Stages: {len(resources.stages)}")
    print(f"  - Lambda Permissions: {len(resources.lambda_permissions)}")


def scan_rest_apis(output_dir: Path, profile: str = None, region: str = "us-east-1", max_workers: int = 5):
    """
    Scan API Gateway REST APIs and generate Terraform code efficiently.
    
    Args:
        output_dir: Directory to write Terraform files
        profile: AWS profile to use
        region: AWS region to scan
        max_workers: Maximum number of parallel workers for API processing
    """
    boto_session = get_boto_session(profile, region)
    apigw_client = boto_session.client("apigateway")
    lambda_client = boto_session.client("lambda")
    
    print(f"Scanning for API Gateway REST APIs in region {region}...")
    
    # Initialize scanner
    scanner = ApiGatewayScanner(apigw_client, lambda_client, region)
    
    # Get all APIs
    apis = scanner.get_all_apis()
    if not apis:
        print("No REST APIs found in the region")
        return
    
    print(f"Found {len(apis)} APIs to process")
    
    # Process APIs in parallel
    all_resources = scan_apis_parallel(scanner, apis, max_workers)
    
    # Generate Terraform files
    generate_terraform_files(all_resources, output_dir)
    
    # Print summary
    print_scan_summary(all_resources)


# List and import functions
def list_rest_apis(output_dir: Path):
    """Lists all API Gateway REST API resources previously generated."""
    ImportManager(output_dir, "api_gateway_rest_api").list_all()


def import_rest_api(api_id: str, output_dir: Path):
    """Runs terraform import for a specific REST API by its ID."""
    ImportManager(output_dir, "api_gateway_rest_api").find_and_import(api_id)


def list_api_gateway_resources(output_dir: Path):
    """Lists all API Gateway Resource resources previously generated."""
    ImportManager(output_dir, "api_gateway_resource").list_all()


def list_api_gateway_methods(output_dir: Path):
    """Lists all API Gateway Method resources previously generated."""
    ImportManager(output_dir, "api_gateway_method").list_all()


def list_api_gateway_integrations(output_dir: Path):
    """Lists all API Gateway Integration resources previously generated."""
    ImportManager(output_dir, "api_gateway_integration").list_all()


def list_api_gateway_stages(output_dir: Path):
    """Lists all API Gateway Stage resources previously generated."""
    ImportManager(output_dir, "api_gateway_stage").list_all()


def import_api_gateway_method(composite_id: str, output_dir: Path):
    """
    Runs terraform import for a specific API Gateway Method.
    composite_id format: "rest_api_id/resource_id/http_method"
    """
    ImportManager(output_dir, "api_gateway_method").find_and_import(composite_id)


def import_api_gateway_integration(composite_id: str, output_dir: Path):
    """
    Runs terraform import for a specific API Gateway Integration.
    composite_id format: "rest_api_id/resource_id/http_method"
    """
    ImportManager(output_dir, "api_gateway_integration").find_and_import(composite_id)


def import_api_gateway_stage(composite_id: str, output_dir: Path):
    """
    Runs terraform import for a specific API Gateway Stage.
    composite_id format: "rest_api_id/stage_name"
    """
    ImportManager(output_dir, "api_gateway_stage").find_and_import(composite_id)


# Note: Sub-resource imports require composite keys (e.g., "api_id/resource_id/method").
# The generated import files contain the correct format for each resource type.
