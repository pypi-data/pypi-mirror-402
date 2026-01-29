from pathlib import Path
from terraback.cli.gcp.session import get_gcp_client
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.gcp.common.error_handler import safe_gcp_operation

def scan_binary_authorization_policies(output_dir: Path, project_id: str = None, region: str = None, zone: str = None, **kwargs):
    """
    Scans for Binary Authorization policies and generates Terraform code.
    """
    def _scan_binary_authorization_policies():
        binary_auth_client = get_gcp_client("binaryauthorization", "v1")
        
        print(f"Scanning for Binary Authorization policies...")
        
        # Get the policy for the project
        policies = []
        # Binary Authorization has one policy per project
        policy_name = f"projects/{project_id or binary_auth_client.project}/policy"
        
        try:
            policy_response = binary_auth_client.projects().getPolicy(name=policy_name).execute()
            
            # Extract policy details
            policy_data = {
                'name': 'default',  # Binary Authorization has one policy per project
                'name_sanitized': 'default',
                'project': project_id or binary_auth_client.project,
                'description': policy_response.get('description'),
                'global_policy_evaluation_mode': policy_response.get('globalPolicyEvaluationMode'),
                'update_time': policy_response.get('updateTime'),
            }
            
            # Handle admission whitelist patterns
            if policy_response.get('admissionWhitelistPatterns'):
                policy_data['admission_whitelist_patterns'] = []
                for pattern in policy_response['admissionWhitelistPatterns']:
                    policy_data['admission_whitelist_patterns'].append({
                        'name_pattern': pattern.get('namePattern')
                    })
            
            # Handle cluster admission rules
            if policy_response.get('clusterAdmissionRules'):
                policy_data['cluster_admission_rules'] = {}
                for cluster, rule in policy_response['clusterAdmissionRules'].items():
                    policy_data['cluster_admission_rules'][cluster] = {
                        'evaluation_mode': rule.get('evaluationMode'),
                        'enforcement_mode': rule.get('enforcementMode'),
                        'require_attestations_by': rule.get('requireAttestationsBy', [])
                    }
            
            # Handle default admission rule
            if policy_response.get('defaultAdmissionRule'):
                policy_data['default_admission_rule'] = {
                    'evaluation_mode': policy_response['defaultAdmissionRule'].get('evaluationMode'),
                    'enforcement_mode': policy_response['defaultAdmissionRule'].get('enforcementMode'),
                    'require_attestations_by': policy_response['defaultAdmissionRule'].get('requireAttestationsBy', [])
                }
            
            # Handle Istio service identity admission rules
            if policy_response.get('istioServiceIdentityAdmissionRules'):
                policy_data['istio_service_identity_admission_rules'] = {}
                for identity, rule in policy_response['istioServiceIdentityAdmissionRules'].items():
                    policy_data['istio_service_identity_admission_rules'][identity] = {
                        'evaluation_mode': rule.get('evaluationMode'),
                        'enforcement_mode': rule.get('enforcementMode'),
                        'require_attestations_by': rule.get('requireAttestationsBy', [])
                    }
            
            # Handle Kubernetes namespace admission rules
            if policy_response.get('kubernetesNamespaceAdmissionRules'):
                policy_data['kubernetes_namespace_admission_rules'] = {}
                for namespace, rule in policy_response['kubernetesNamespaceAdmissionRules'].items():
                    policy_data['kubernetes_namespace_admission_rules'][namespace] = {
                        'evaluation_mode': rule.get('evaluationMode'),
                        'enforcement_mode': rule.get('enforcementMode'),
                        'require_attestations_by': rule.get('requireAttestationsBy', [])
                    }
            
            # Handle Kubernetes service account admission rules
            if policy_response.get('kubernetesServiceAccountAdmissionRules'):
                policy_data['kubernetes_service_account_admission_rules'] = {}
                for account, rule in policy_response['kubernetesServiceAccountAdmissionRules'].items():
                    policy_data['kubernetes_service_account_admission_rules'][account] = {
                        'evaluation_mode': rule.get('evaluationMode'),
                        'enforcement_mode': rule.get('enforcementMode'),
                        'require_attestations_by': rule.get('requireAttestationsBy', [])
                    }
            
            policies.append(policy_data)
            
        except Exception as e:
            print(f"  - No Binary Authorization policy found or error accessing: {e}")
        
        return policies
    
    # Use safe operation wrapper
    policies = safe_gcp_operation(
        _scan_binary_authorization_policies, 
        "Binary Authorization API", 
        project_id or "default"
    )
    
    if policies:
        output_file = output_dir / "gcp_binary_authorization_policy.tf"
        generate_tf(policies, "gcp_binary_authorization_policy", output_file)
        print(f"Generated Terraform for {len(policies)} Binary Authorization policies -> {output_file}")
        
        # Generate imports file - use the correct function signature
        generate_imports_file(
            resource_type="gcp_binary_authorization_policy",
            resources=policies,
            remote_resource_id_key="project", 
            output_dir=output_dir,
            provider="gcp"
        )
        print(f"Generated imports file -> gcp_binary_authorization_policy_import.json")

def list_binary_authorization_policies(output_dir: Path):
    """List scanned Binary Authorization policies."""
    tf_file = output_dir / "gcp_binary_authorization_policy.tf"
    if not tf_file.exists():
        print("No Binary Authorization policies found. Run 'scan-binary-auth' first.")
        return
    
    print("Scanned Binary Authorization policies:")
    print(f"  - Check {tf_file} for details")

def import_binary_authorization_policy(policy_id: str, output_dir: Path):
    """Import a specific Binary Authorization policy."""
    imports_file = output_dir / "gcp_binary_authorization_policy_imports.tf"
    
    if not imports_file.exists():
        print(f"Imports file not found. Run 'scan-binary-auth' first.")
        return
    
    manager = ImportManager(imports_file)
    manager.run_import("google_binary_authorization_policy", policy_id)