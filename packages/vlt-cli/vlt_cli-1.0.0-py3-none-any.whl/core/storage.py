"""
SecureEnv-Pro - Storage Management Module
Handles vault files, configuration, and audit logging
"""

import os
import json
import yaml
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class StorageError(Exception):
    """Custom exception for storage-related errors"""
    pass


class VaultStorage:
    """
    Manages vault storage and configuration
    
    Features:
    - Multiple vault support
    - Configuration management
    - Audit logging
    - Team sharing metadata
    """
    
    def __init__(self, base_dir: str = "./vault"):
        """
        Initialize storage manager
        
        Args:
            base_dir: Base directory for vault storage
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        self.config_file = self.base_dir / "config.yml"
        self.audit_file = self.base_dir / "audit.log"
        
        self._ensure_config()
    
    def _ensure_config(self):
        """Create default config if it doesn't exist"""
        if not self.config_file.exists():
            default_config = {
                "version": "1.0.0",
                "vaults": {},
                "settings": {
                    "auto_lock_timeout": 300,  # 5 minutes
                    "max_password_attempts": 3,
                    "audit_enabled": True
                }
            }
            self.save_config(default_config)
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise StorageError(f"Failed to load config: {e}")
    
    def save_config(self, config: Dict[str, Any]):
        """Save configuration to YAML file"""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
        except Exception as e:
            raise StorageError(f"Failed to save config: {e}")
    
    def register_vault(self, name: str, file_path: str, description: str = ""):
        """
        Register a new vault in configuration
        
        Args:
            name: Vault identifier
            file_path: Path to .vlt file
            description: Optional description
        """
        config = self.load_config()
        
        if name in config["vaults"]:
            raise StorageError(f"Vault '{name}' already exists")
        
        config["vaults"][name] = {
            "file": file_path,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "last_accessed": None
        }
        
        self.save_config(config)
        self.log_audit("vault_created", {"vault": name})
    
    def get_vault_path(self, name: str) -> str:
        """
        Get file path for a registered vault
        
        Args:
            name: Vault identifier
            
        Returns:
            Path to vault file
        """
        config = self.load_config()
        
        if name not in config["vaults"]:
            raise StorageError(f"Vault '{name}' not found")
        
        return config["vaults"][name]["file"]
    
    def list_vaults(self) -> List[Dict[str, Any]]:
        """
        List all registered vaults
        
        Returns:
            List of vault metadata
        """
        config = self.load_config()
        return [
            {"name": name, **details}
            for name, details in config["vaults"].items()
        ]
    
    def delete_vault(self, name: str, remove_file: bool = False):
        """
        Delete a vault registration
        
        Args:
            name: Vault identifier
            remove_file: If True, also delete the .vlt file
        """
        config = self.load_config()
        
        if name not in config["vaults"]:
            raise StorageError(f"Vault '{name}' not found")
        
        vault_file = config["vaults"][name]["file"]
        del config["vaults"][name]
        
        self.save_config(config)
        self.log_audit("vault_deleted", {"vault": name})
        
        if remove_file and os.path.exists(vault_file):
            os.remove(vault_file)
    
    def update_access_time(self, name: str):
        """Update last accessed timestamp for a vault"""
        config = self.load_config()
        
        if name in config["vaults"]:
            config["vaults"][name]["last_accessed"] = datetime.now().isoformat()
            self.save_config(config)
    
    def log_audit(self, action: str, details: Dict[str, Any]):
        """
        Log audit event
        
        Args:
            action: Action type (e.g., 'vault_created', 'decryption_success')
            details: Additional event details
        """
        config = self.load_config()
        
        if not config["settings"].get("audit_enabled", True):
            return
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        }
        
        with open(self.audit_file, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def get_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve recent audit logs
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of audit log entries
        """
        if not self.audit_file.exists():
            return []
        
        logs = []
        with open(self.audit_file, 'r') as f:
            for line in f:
                try:
                    logs.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
        
        return logs[-limit:]
    
    def parse_env_content(self, content: str) -> Dict[str, str]:
        """
        Parse .env file content into key-value pairs
        
        Args:
            content: Raw .env file content
            
        Returns:
            Dictionary of environment variables
        """
        env_vars = {}
        
        for line in content.splitlines():
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip().strip('"').strip("'")
        
        return env_vars
    
    def format_env_content(self, env_vars: Dict[str, str]) -> str:
        """
        Format environment variables as .env content
        
        Args:
            env_vars: Dictionary of environment variables
            
        Returns:
            Formatted .env file content
        """
        lines = [f"{key}={value}" for key, value in sorted(env_vars.items())]
        return "\n".join(lines)


class TeamVaultManager:
    """
    Manages team-shared vaults with role-based access
    
    Features:
    - Team member management
    - Role-based permissions (admin, developer, viewer)
    - Shared vault metadata
    """
    
    ROLES = ["admin", "developer", "viewer"]
    
    def __init__(self, storage: VaultStorage):
        self.storage = storage
    
    def add_team_member(self, vault_name: str, member_email: str, role: str):
        """
        Add team member to a vault
        
        Args:
            vault_name: Vault identifier
            member_email: Team member email
            role: Member role (admin/developer/viewer)
        """
        if role not in self.ROLES:
            raise StorageError(f"Invalid role. Must be one of: {self.ROLES}")
        
        config = self.storage.load_config()
        
        if vault_name not in config["vaults"]:
            raise StorageError(f"Vault '{vault_name}' not found")
        
        if "team" not in config["vaults"][vault_name]:
            config["vaults"][vault_name]["team"] = {}
        
        config["vaults"][vault_name]["team"][member_email] = {
            "role": role,
            "added_at": datetime.now().isoformat()
        }
        
        self.storage.save_config(config)
        self.storage.log_audit("team_member_added", {
            "vault": vault_name,
            "member": member_email,
            "role": role
        })
    
    def get_team_members(self, vault_name: str) -> Dict[str, Dict[str, str]]:
        """Get all team members for a vault"""
        config = self.storage.load_config()
        
        if vault_name not in config["vaults"]:
            raise StorageError(f"Vault '{vault_name}' not found")
        
        return config["vaults"][vault_name].get("team", {})
