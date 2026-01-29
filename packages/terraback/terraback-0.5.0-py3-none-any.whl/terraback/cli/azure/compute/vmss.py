from typing import Dict, List, Any, Optional
from pathlib import Path
from azure.mgmt.compute import ComputeManagementClient
from azure.core.exceptions import HttpResponseError
from terraback.utils.logging import get_logger
from terraback.cli.cache import cache_result

logger = get_logger(__name__)


class VMScaleSetsScanner:
    def __init__(self, credentials, subscription_id: str):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.client = ComputeManagementClient(credentials, subscription_id)

    @cache_result(ttl=300)
    def list_vm_scale_sets(self) -> List[Dict[str, Any]]:
        """List all VM Scale Sets in the subscription."""
        vm_scale_sets = []
        
        try:
            # List all VM Scale Sets
            for vmss in self.client.virtual_machine_scale_sets.list_all():
                try:
                    vm_scale_sets.append(self._process_vm_scale_set(vmss))
                except Exception as e:
                    logger.error(f"Error processing VM Scale Set {vmss.name}: {str(e)}")
                    continue
                    
        except HttpResponseError as e:
            logger.error(f"Error listing VM Scale Sets: {str(e)}")
            
        return vm_scale_sets

    def _process_vm_scale_set(self, vmss) -> Dict[str, Any]:
        """Process a single VM Scale Set resource."""
        # Determine if it's Linux or Windows
        is_linux = True
        if vmss.virtual_machine_profile and vmss.virtual_machine_profile.os_profile:
            if hasattr(vmss.virtual_machine_profile.os_profile, 'windows_configuration') and vmss.virtual_machine_profile.os_profile.windows_configuration:
                is_linux = False
        
        resource_type = "azure_linux_virtual_machine_scale_set" if is_linux else "azure_windows_virtual_machine_scale_set"
        
        vmss_data = {
            "id": vmss.id,
            "name": vmss.name,
            "type": resource_type,
            "resource_type": resource_type,
            "resource_group_name": vmss.id.split('/')[4],
            "location": vmss.location,
            "properties": {
                "name": vmss.name,
                "location": vmss.location,
                "resource_group_name": vmss.id.split('/')[4],
                "sku": vmss.sku.name,
                "instances": vmss.sku.capacity,
            }
        }
        
        # Process virtual machine profile
        if vmss.virtual_machine_profile:
            profile = vmss.virtual_machine_profile
            
            # OS Profile
            if profile.os_profile:
                if profile.os_profile.computer_name_prefix:
                    vmss_data["properties"]["computer_name_prefix"] = profile.os_profile.computer_name_prefix
                if profile.os_profile.admin_username:
                    vmss_data["properties"]["admin_username"] = profile.os_profile.admin_username
                if hasattr(profile.os_profile, 'custom_data') and profile.os_profile.custom_data:
                    vmss_data["properties"]["custom_data"] = profile.os_profile.custom_data
                
                # Linux specific
                if is_linux and hasattr(profile.os_profile, 'linux_configuration') and profile.os_profile.linux_configuration:
                    linux_config = profile.os_profile.linux_configuration
                    if hasattr(linux_config, 'disable_password_authentication'):
                        vmss_data["properties"]["disable_password_authentication"] = linux_config.disable_password_authentication
            
            # Storage Profile
            if profile.storage_profile:
                # Image reference
                if profile.storage_profile.image_reference:
                    if hasattr(profile.storage_profile.image_reference, 'id'):
                        vmss_data["properties"]["source_image_id"] = profile.storage_profile.image_reference.id
                    else:
                        vmss_data["properties"]["source_image_reference"] = {
                            "publisher": profile.storage_profile.image_reference.publisher,
                            "offer": profile.storage_profile.image_reference.offer,
                            "sku": profile.storage_profile.image_reference.sku,
                            "version": profile.storage_profile.image_reference.version
                        }
                
                # OS Disk
                if profile.storage_profile.os_disk:
                    os_disk = profile.storage_profile.os_disk
                    vmss_data["properties"]["os_disk"] = {
                        "caching": os_disk.caching if os_disk.caching else "ReadWrite",
                        "storage_account_type": os_disk.managed_disk.storage_account_type if os_disk.managed_disk else "Standard_LRS"
                    }
                    if os_disk.disk_size_gb:
                        vmss_data["properties"]["os_disk"]["disk_size_gb"] = os_disk.disk_size_gb
                    if hasattr(os_disk, 'disk_encryption_set') and os_disk.disk_encryption_set:
                        vmss_data["properties"]["os_disk"]["disk_encryption_set_id"] = os_disk.disk_encryption_set.id
            
            # Network Profile
            if profile.network_profile and profile.network_profile.network_interface_configurations:
                network_interfaces = []
                for nic_config in profile.network_profile.network_interface_configurations:
                    interface = {
                        "name": nic_config.name,
                        "primary": nic_config.primary if hasattr(nic_config, 'primary') else False,
                        "ip_configurations": []
                    }
                    
                    if nic_config.network_security_group:
                        interface["network_security_group_id"] = nic_config.network_security_group.id
                    if hasattr(nic_config, 'enable_accelerated_networking'):
                        interface["enable_accelerated_networking"] = nic_config.enable_accelerated_networking
                    if hasattr(nic_config, 'enable_ip_forwarding'):
                        interface["enable_ip_forwarding"] = nic_config.enable_ip_forwarding
                    
                    # IP Configurations
                    if nic_config.ip_configurations:
                        for ip_config in nic_config.ip_configurations:
                            ip_conf_data = {
                                "name": ip_config.name,
                                "primary": ip_config.primary if hasattr(ip_config, 'primary') else False,
                                "subnet_id": ip_config.subnet.id if ip_config.subnet else ""
                            }
                            
                            # Public IP configuration
                            if hasattr(ip_config, 'public_ip_address_configuration') and ip_config.public_ip_address_configuration:
                                pub_ip = ip_config.public_ip_address_configuration
                                ip_conf_data["public_ip_address"] = {
                                    "name": pub_ip.name
                                }
                                if hasattr(pub_ip, 'domain_name_label'):
                                    ip_conf_data["public_ip_address"]["domain_name_label"] = pub_ip.domain_name_label
                            
                            # Load balancer configurations
                            if hasattr(ip_config, 'load_balancer_backend_address_pools') and ip_config.load_balancer_backend_address_pools:
                                ip_conf_data["load_balancer_backend_address_pool_ids"] = [pool.id for pool in ip_config.load_balancer_backend_address_pools]
                            
                            if hasattr(ip_config, 'load_balancer_inbound_nat_rules') and ip_config.load_balancer_inbound_nat_rules:
                                ip_conf_data["load_balancer_inbound_nat_rules_ids"] = [rule.id for rule in ip_config.load_balancer_inbound_nat_rules]
                            
                            if hasattr(ip_config, 'application_gateway_backend_address_pools') and ip_config.application_gateway_backend_address_pools:
                                ip_conf_data["application_gateway_backend_address_pool_ids"] = [pool.id for pool in ip_config.application_gateway_backend_address_pools]
                            
                            if hasattr(ip_config, 'application_security_groups') and ip_config.application_security_groups:
                                ip_conf_data["application_security_group_ids"] = [asg.id for asg in ip_config.application_security_groups]
                            
                            interface["ip_configurations"].append(ip_conf_data)
                    
                    network_interfaces.append(interface)
                
                vmss_data["properties"]["network_interfaces"] = network_interfaces
            
            # Diagnostics Profile
            if hasattr(profile, 'diagnostics_profile') and profile.diagnostics_profile:
                if profile.diagnostics_profile.boot_diagnostics:
                    boot_diag = profile.diagnostics_profile.boot_diagnostics
                    if boot_diag.enabled:
                        vmss_data["properties"]["boot_diagnostics"] = {}
                        if boot_diag.storage_uri:
                            vmss_data["properties"]["boot_diagnostics"]["storage_account_uri"] = boot_diag.storage_uri
        
        # Identity
        if vmss.identity:
            identity_data = {
                "type": vmss.identity.type
            }
            if vmss.identity.user_assigned_identities:
                identity_data["identity_ids"] = list(vmss.identity.user_assigned_identities.keys())
            vmss_data["properties"]["identity"] = identity_data
        
        # Plan
        if vmss.plan:
            vmss_data["properties"]["plan"] = {
                "name": vmss.plan.name,
                "publisher": vmss.plan.publisher,
                "product": vmss.plan.product
            }
        
        # Upgrade Policy
        if vmss.upgrade_policy:
            if vmss.upgrade_policy.automatic_os_upgrade_policy:
                vmss_data["properties"]["automatic_os_upgrade_policy"] = {
                    "disable_automatic_rollback": vmss.upgrade_policy.automatic_os_upgrade_policy.disable_automatic_rollback,
                    "enable_automatic_os_upgrade": vmss.upgrade_policy.automatic_os_upgrade_policy.enable_automatic_os_upgrade
                }
            
            if vmss.upgrade_policy.rolling_upgrade_policy:
                rup = vmss.upgrade_policy.rolling_upgrade_policy
                vmss_data["properties"]["rolling_upgrade_policy"] = {
                    "max_batch_instance_percent": rup.max_batch_instance_percent,
                    "max_unhealthy_instance_percent": rup.max_unhealthy_instance_percent,
                    "max_unhealthy_upgraded_instance_percent": rup.max_unhealthy_upgraded_instance_percent,
                    "pause_time_between_batches": rup.pause_time_between_batches
                }
        
        # Additional configurations
        if hasattr(vmss, 'automatic_repairs_policy') and vmss.automatic_repairs_policy:
            vmss_data["properties"]["automatic_instance_repair"] = {
                "enabled": vmss.automatic_repairs_policy.enabled,
                "grace_period": vmss.automatic_repairs_policy.grace_period
            }
        
        if hasattr(vmss, 'scale_in_policy') and vmss.scale_in_policy:
            vmss_data["properties"]["scale_in"] = {
                "rule": vmss.scale_in_policy.rules[0] if vmss.scale_in_policy.rules else "Default",
                "force_deletion_enabled": getattr(vmss.scale_in_policy, 'force_deletion', False)
            }
        
        # Other properties
        if hasattr(vmss, 'overprovision'):
            vmss_data["properties"]["overprovision"] = vmss.overprovision
        
        if hasattr(vmss, 'single_placement_group'):
            vmss_data["properties"]["single_placement_group"] = vmss.single_placement_group
        
        if hasattr(vmss, 'zone_balance'):
            vmss_data["properties"]["zone_balance"] = vmss.zone_balance
        
        if vmss.zones:
            vmss_data["properties"]["zones"] = vmss.zones
        
        if hasattr(vmss, 'proximity_placement_group') and vmss.proximity_placement_group:
            vmss_data["properties"]["proximity_placement_group_id"] = vmss.proximity_placement_group.id
        
        # Tags
        if vmss.tags:
            vmss_data["properties"]["tags"] = vmss.tags
            
        return vmss_data

    def scan(self) -> List[Dict[str, Any]]:
        """Main scan method to retrieve all VM Scale Sets."""
        logger.info(f"Scanning VM Scale Sets in subscription {self.subscription_id}")
        return self.list_vm_scale_sets()


def scan_vm_scale_sets(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Scan VM Scale Sets in the subscription."""
    from terraback.cli.azure.session import get_azure_credential, get_default_subscription_id
    from terraback.cli.azure.resource_processor import process_resources
    from terraback.terraform_generator.writer import generate_tf_auto
    from terraback.terraform_generator.imports import generate_imports_file
    
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    credentials = get_azure_credential()
    scanner = VMScaleSetsScanner(credentials, subscription_id)
    vm_scale_sets = scanner.scan()
    
    if vm_scale_sets:
        # Generate Terraform files
        generate_tf_auto(vm_scale_sets, "azure_vmss", output_dir)
        print(f"[Cross-scan] Generated Terraform for {len(vm_scale_sets)} Azure VM Scale Sets")
        
        # Generate import file
        generate_imports_file(
            "azure_linux_virtual_machine_scale_set",
            [vmss for vmss in vm_scale_sets if vmss['type'] == 'azure_linux_virtual_machine_scale_set'],
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
        generate_imports_file(
            "azure_windows_virtual_machine_scale_set",
            [vmss for vmss in vm_scale_sets if vmss['type'] == 'azure_windows_virtual_machine_scale_set'],
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return vm_scale_sets
