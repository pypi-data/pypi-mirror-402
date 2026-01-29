"""
SecureEnv-Pro - Comprehensive Test Suite
Tests for security, storage, and CLI functionality
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path

from core.security import SecureVault, SecurityError, verify_password_strength, generate_secure_password
from core.storage import VaultStorage, StorageError, TeamVaultManager


class TestSecurity:
    """Test encryption and decryption functionality"""
    
    def test_password_validation(self):
        """Test password strength validation"""
        # Strong password
        is_valid, msg = verify_password_strength("SecurePass123")
        assert is_valid is True
        
        # Weak password - too short
        is_valid, msg = verify_password_strength("Short1")
        assert is_valid is False
        assert "8 characters" in msg
        
        # Weak password - no uppercase
        is_valid, msg = verify_password_strength("password123")
        assert is_valid is False
    
    def test_secure_password_generation(self):
        """Test secure password generation"""
        password = generate_secure_password(16)
        assert len(password) >= 16
        
        # Check password contains required characters
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        assert has_upper and has_lower and has_digit
    
    def test_encryption_decryption(self):
        """Test basic encryption and decryption"""
        password = "TestPassword123"
        test_data = b"SECRET_KEY=mysecretvalue123"
        
        # Encrypt
        vault = SecureVault(password)
        encrypted = vault.encrypt_data(test_data)
        
        # Verify encrypted data is different
        assert encrypted != test_data
        assert len(encrypted) > len(test_data)
        
        # Decrypt with correct password
        vault2 = SecureVault(password, vault.salt)
        decrypted = vault2.fernet.decrypt(encrypted[vault.SALT_SIZE:])
        assert decrypted == test_data
    
    def test_wrong_password_fails(self):
        """Test that wrong password fails decryption"""
        password1 = "CorrectPass123"
        password2 = "WrongPass456"
        test_data = b"SECRET=value"
        
        # Encrypt with password1
        vault1 = SecureVault(password1)
        encrypted = vault1.encrypt_data(test_data)
        
        # Try to decrypt with password2
        vault2 = SecureVault(password2, vault1.salt)
        
        with pytest.raises(Exception):  # InvalidToken
            vault2.fernet.decrypt(encrypted[vault1.SALT_SIZE:])
    
    def test_file_encryption(self):
        """Test file encryption and decryption"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "test.env"
            test_content = b"API_KEY=secret123\nDB_PASSWORD=pass456"
            test_file.write_bytes(test_content)
            
            # Encrypt
            password = "FileTest123"
            vault = SecureVault(password)
            vault_file = vault.encrypt_file(str(test_file))
            
            # Verify vault file exists
            assert os.path.exists(vault_file)
            assert vault_file.endswith('.vlt')
            
            # Decrypt
            decrypted = vault.decrypt_file(vault_file, password)
            assert decrypted == test_content
    
    def test_short_password_rejected(self):
        """Test that short passwords are rejected"""
        with pytest.raises(SecurityError):
            SecureVault("short")


class TestStorage:
    """Test vault storage and configuration management"""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage for testing"""
        tmpdir = tempfile.mkdtemp()
        storage = VaultStorage(tmpdir)
        yield storage
        shutil.rmtree(tmpdir)
    
    def test_config_creation(self, temp_storage):
        """Test configuration file creation"""
        config = temp_storage.load_config()
        assert "version" in config
        assert "vaults" in config
        assert "settings" in config
    
    def test_vault_registration(self, temp_storage):
        """Test registering a new vault"""
        temp_storage.register_vault(
            "test_vault",
            "/path/to/vault.vlt",
            "Test vault"
        )
        
        config = temp_storage.load_config()
        assert "test_vault" in config["vaults"]
        assert config["vaults"]["test_vault"]["file"] == "/path/to/vault.vlt"
    
    def test_duplicate_vault_rejected(self, temp_storage):
        """Test that duplicate vault names are rejected"""
        temp_storage.register_vault("duplicate", "/path1.vlt", "First")
        
        with pytest.raises(StorageError):
            temp_storage.register_vault("duplicate", "/path2.vlt", "Second")
    
    def test_list_vaults(self, temp_storage):
        """Test listing registered vaults"""
        temp_storage.register_vault("vault1", "/path1.vlt", "First vault")
        temp_storage.register_vault("vault2", "/path2.vlt", "Second vault")
        
        vaults = temp_storage.list_vaults()
        assert len(vaults) == 2
        
        vault_names = [v["name"] for v in vaults]
        assert "vault1" in vault_names
        assert "vault2" in vault_names
    
    def test_delete_vault(self, temp_storage):
        """Test deleting a vault"""
        temp_storage.register_vault("to_delete", "/path.vlt", "Delete me")
        temp_storage.delete_vault("to_delete", remove_file=False)
        
        config = temp_storage.load_config()
        assert "to_delete" not in config["vaults"]
    
    def test_audit_logging(self, temp_storage):
        """Test audit log functionality"""
        temp_storage.log_audit("test_action", {"key": "value"})
        
        logs = temp_storage.get_audit_logs()
        assert len(logs) > 0
        assert logs[-1]["action"] == "test_action"
        assert logs[-1]["details"]["key"] == "value"
    
    def test_env_parsing(self, temp_storage):
        """Test .env content parsing"""
        env_content = """
# Comment line
API_KEY=secret123
DB_HOST=localhost
DB_PORT=5432

# Another comment
SECRET_TOKEN=abc123xyz
"""
        env_vars = temp_storage.parse_env_content(env_content)
        
        assert len(env_vars) == 4
        assert env_vars["API_KEY"] == "secret123"
        assert env_vars["DB_HOST"] == "localhost"
        assert env_vars["DB_PORT"] == "5432"
        assert env_vars["SECRET_TOKEN"] == "abc123xyz"
    
    def test_env_formatting(self, temp_storage):
        """Test .env content formatting"""
        env_vars = {
            "API_KEY": "secret123",
            "DB_HOST": "localhost",
            "DB_PORT": "5432"
        }
        
        formatted = temp_storage.format_env_content(env_vars)
        lines = formatted.split("\n")
        
        assert "API_KEY=secret123" in lines
        assert "DB_HOST=localhost" in lines
        assert "DB_PORT=5432" in lines


class TestTeamManagement:
    """Test team collaboration features"""
    
    @pytest.fixture
    def temp_team_manager(self):
        """Create temporary team manager for testing"""
        tmpdir = tempfile.mkdtemp()
        storage = VaultStorage(tmpdir)
        storage.register_vault("team_vault", "/path.vlt", "Team vault")
        manager = TeamVaultManager(storage)
        yield manager
        shutil.rmtree(tmpdir)
    
    def test_add_team_member(self, temp_team_manager):
        """Test adding team member"""
        temp_team_manager.add_team_member(
            "team_vault",
            "dev@company.com",
            "developer"
        )
        
        members = temp_team_manager.get_team_members("team_vault")
        assert "dev@company.com" in members
        assert members["dev@company.com"]["role"] == "developer"
    
    def test_invalid_role_rejected(self, temp_team_manager):
        """Test that invalid roles are rejected"""
        with pytest.raises(StorageError):
            temp_team_manager.add_team_member(
                "team_vault",
                "dev@company.com",
                "invalid_role"
            )
    
    def test_multiple_team_members(self, temp_team_manager):
        """Test adding multiple team members"""
        temp_team_manager.add_team_member("team_vault", "admin@company.com", "admin")
        temp_team_manager.add_team_member("team_vault", "dev@company.com", "developer")
        temp_team_manager.add_team_member("team_vault", "viewer@company.com", "viewer")
        
        members = temp_team_manager.get_team_members("team_vault")
        assert len(members) == 3


class TestEndToEnd:
    """End-to-end integration tests"""
    
    def test_complete_workflow(self):
        """Test complete lock, unlock, run workflow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            storage = VaultStorage(tmpdir)
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("TEST_VAR=test_value\nANOTHER_VAR=another_value")
            
            # Lock (encrypt)
            password = "WorkflowTest123"
            vault = SecureVault(password)
            vault_file = vault.encrypt_file(str(env_file))
            storage.register_vault("test", vault_file, "Test vault")
            
            # Verify vault exists
            assert os.path.exists(vault_file)
            
            # Unlock (decrypt)
            decrypted = vault.decrypt_file(vault_file, password)
            env_vars = storage.parse_env_content(decrypted.decode())
            
            # Verify decrypted content
            assert env_vars["TEST_VAR"] == "test_value"
            assert env_vars["ANOTHER_VAR"] == "another_value"
            
            # Verify storage tracking
            vaults = storage.list_vaults()
            assert len(vaults) == 1
            assert vaults[0]["name"] == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=core", "--cov-report=html"])
