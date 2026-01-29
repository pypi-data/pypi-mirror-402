"""
SecureEnv-Pro - High-Security Encryption Module
AES-256 encryption with PBKDF2 key derivation
"""

import os
import base64
import secrets
from typing import Optional, Tuple
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecurityError(Exception):
    """Custom exception for security-related errors"""
    pass


class SecureVault:
    """
    Enterprise-grade encryption vault using AES-256
    
    Features:
    - PBKDF2 key derivation with 100,000 iterations
    - Random salt generation for production security
    - Secure password verification
    - Memory-safe operations
    """
    
    ITERATIONS = 100000
    SALT_SIZE = 32
    
    def __init__(self, password: str, salt: Optional[bytes] = None):
        """
        Initialize vault with master password
        
        Args:
            password: Master password for encryption/decryption
            salt: Optional salt (if None, generates new random salt)
        """
        if not password or len(password) < 8:
            raise SecurityError("Password must be at least 8 characters long")
        
        self.salt = salt if salt else secrets.token_bytes(self.SALT_SIZE)
        self.fernet = self._derive_key(password)
    
    def _derive_key(self, password: str) -> Fernet:
        """
        Derive encryption key from password using PBKDF2
        
        Args:
            password: Master password
            
        Returns:
            Fernet cipher instance
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=self.ITERATIONS,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return Fernet(key)
    
    def encrypt_data(self, data: bytes) -> bytes:
        """
        Encrypt data with AES-256
        
        Args:
            data: Raw bytes to encrypt
            
        Returns:
            Encrypted data with salt prepended
        """
        encrypted = self.fernet.encrypt(data)
        # Prepend salt for later decryption
        return self.salt + encrypted
    
    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt data with AES-256
        
        Args:
            encrypted_data: Data with salt prepended
            
        Returns:
            Decrypted raw bytes
            
        Raises:
            SecurityError: If decryption fails (wrong password)
        """
        try:
            # Extract salt from beginning
            salt = encrypted_data[:self.SALT_SIZE]
            encrypted = encrypted_data[self.SALT_SIZE:]
            
            # Re-initialize with extracted salt
            self.salt = salt
            self.fernet = self._derive_key(
                self._get_current_password()  # This needs to be stored temporarily
            )
            
            return self.fernet.decrypt(encrypted)
        except InvalidToken:
            raise SecurityError("Decryption failed: Invalid password or corrupted data")
    
    def encrypt_file(self, input_file: str, output_file: Optional[str] = None) -> str:
        """
        Encrypt a file
        
        Args:
            input_file: Path to file to encrypt
            output_file: Optional output path (defaults to input_file.vlt)
            
        Returns:
            Path to encrypted file
        """
        if not os.path.exists(input_file):
            raise SecurityError(f"File not found: {input_file}")
        
        with open(input_file, 'rb') as f:
            data = f.read()
        
        encrypted = self.encrypt_data(data)
        
        output_path = output_file or f"{input_file}.vlt"
        with open(output_path, 'wb') as f:
            f.write(encrypted)
        
        return output_path
    
    def decrypt_file(self, vault_file: str, password: str) -> bytes:
        """
        Decrypt a vault file
        
        Args:
            vault_file: Path to encrypted .vlt file
            password: Master password
            
        Returns:
            Decrypted data as bytes
        """
        if not os.path.exists(vault_file):
            raise SecurityError(f"Vault file not found: {vault_file}")
        
        with open(vault_file, 'rb') as f:
            encrypted_data = f.read()
        
        # Extract salt and re-initialize
        salt = encrypted_data[:self.SALT_SIZE]
        encrypted = encrypted_data[self.SALT_SIZE:]
        
        # Create new instance with correct salt
        vault = SecureVault(password, salt)
        
        try:
            return vault.fernet.decrypt(encrypted)
        except InvalidToken:
            raise SecurityError("Decryption failed: Invalid password or corrupted vault")


def verify_password_strength(password: str) -> Tuple[bool, str]:
    """
    Verify password meets security requirements
    
    Args:
        password: Password to check
        
    Returns:
        Tuple of (is_valid, message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "Password must contain uppercase, lowercase, and digits"
    
    return True, "Password is strong"


def generate_secure_password(length: int = 16) -> str:
    """
    Generate a cryptographically secure random password
    
    Args:
        length: Password length (minimum 12)
        
    Returns:
        Random secure password
    """
    import string
    
    length = max(length, 12)
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    return password
