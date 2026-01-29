"""
Post-scan processor for fixing cross-resource references and optimizing generated files.
This runs after all resources are scanned to apply cross-resource optimizations.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Set, Optional
from terraback.utils.logging import get_logger

logger = get_logger(__name__)

class PostScanProcessor:
    """Processes generated Terraform files to optimize cross-resource references."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.storage_accounts = {}
        self.key_vaults = {}
        self.all_resources = {}
        
    def process_all(self) -> bool:
        """Main entry point - process all generated files."""
        try:
            # Step 1: Discover all resources from .tf files
            self._discover_resources()
            
            # Step 2: Fix cross-resource references
            self._fix_function_app_storage_references()
            
            # Step 3: Remove unnecessary variables
            self._cleanup_unused_variables()
            
            # Step 4: Remove aggressive lifecycle rules
            self._fix_lifecycle_rules()
            
            logger.info("Post-scan processing completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Post-scan processing failed: {e}")
            return False
    
    def _discover_resources(self):
        """Discover all resources from generated .tf files."""
        
        # Find storage accounts
        storage_tf = self.output_dir / "storage_account.tf"
        if storage_tf.exists():
            content = storage_tf.read_text()
            matches = re.findall(r'resource "azurerm_storage_account" "([^"]+)".*?name\s*=\s*"([^"]+)"', content, re.DOTALL)
            for resource_name, account_name in matches:
                self.storage_accounts[account_name] = resource_name
                logger.debug(f"Discovered storage account: {account_name} -> {resource_name}")
        
        # Find key vaults (for future expansion)
        key_vault_tf = self.output_dir / "key_vault.tf"
        if key_vault_tf.exists():
            content = key_vault_tf.read_text()
            matches = re.findall(r'resource "azurerm_key_vault" "([^"]+)".*?name\s*=\s*"([^"]+)"', content, re.DOTALL)
            for resource_name, vault_name in matches:
                self.key_vaults[vault_name] = resource_name
                logger.debug(f"Discovered key vault: {vault_name} -> {resource_name}")
    
    def _fix_function_app_storage_references(self):
        """Fix Function App storage account references."""
        
        function_app_tf = self.output_dir / "linux_function_app.tf"
        if not function_app_tf.exists():
            return
        
        content = function_app_tf.read_text()
        
        # Pattern 1: Replace storage account name variable with actual name
        if self.storage_accounts:
            # Use the first (and likely only) storage account
            storage_name, storage_resource = next(iter(self.storage_accounts.items()))
            
            content = re.sub(
                r'storage_account_name\s*=\s*var\.function_app_storage_account_name',
                f'storage_account_name       = "{storage_name}"',
                content
            )
        
        # Pattern 2: Replace storage account key variable with resource reference  
        if self.storage_accounts:
            storage_name, storage_resource = next(iter(self.storage_accounts.items()))
            
            content = re.sub(
                r'storage_account_access_key\s*=\s*var\.storage_account_key',
                f'storage_account_access_key = azurerm_storage_account.{storage_resource}.primary_access_key',
                content
            )
        
        if content != function_app_tf.read_text():
            function_app_tf.write_text(content)
            logger.info("Fixed Function App storage references")
    
    def _cleanup_unused_variables(self):
        """Remove variables that are no longer needed after cross-resource fixes."""
        
        variables_tf = self.output_dir / "variables.tf"
        if not variables_tf.exists():
            return
        
        content = variables_tf.read_text()
        original_content = content
        
        # Remove storage account variables if we have cross-resource references
        if self.storage_accounts:
            patterns_to_remove = [
                r'variable "storage_account_key" \{[^}]*\}\s*',
                r'variable "function_app_storage_account_name" \{[^}]*\}\s*'
            ]
            
            for pattern in patterns_to_remove:
                content = re.sub(pattern, '', content, flags=re.DOTALL)
        
        # Clean up extra newlines
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content).strip()
        
        if content != original_content:
            if content.strip():
                variables_tf.write_text(content + '\n')
                logger.info("Cleaned up unused variables")
            else:
                variables_tf.unlink()
                logger.info("Removed empty variables.tf")
    
    def _fix_lifecycle_rules(self):
        """Remove or fix aggressive lifecycle rules that cause import issues."""
        
        tf_files = list(self.output_dir.glob("*.tf"))
        fixed_files = []
        
        for tf_file in tf_files:
            if tf_file.name in ["variables.tf", "provider.tf"]:
                continue
            
            content = tf_file.read_text()
            original_content = content
            
            # Remove prevent_destroy = true
            content = re.sub(r'\s*prevent_destroy = true\s*', '', content)
            
            # Clean up empty lifecycle blocks
            content = re.sub(r'lifecycle \{\s*\}', '', content)
            
            if content != original_content:
                tf_file.write_text(content)
                fixed_files.append(tf_file.name)
        
        if fixed_files:
            logger.info(f"Fixed lifecycle rules in: {', '.join(fixed_files)}")

def run_post_scan_processing(output_dir: Path) -> bool:
    """Run post-scan processing on generated files."""
    processor = PostScanProcessor(output_dir)
    return processor.process_all()