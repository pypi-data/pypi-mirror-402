"""Encryption utilities for private key protection."""

import base64
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def encrypt_private_key(private_key: str, password: str) -> str:
    """
    Encrypt private key using AES-256-CBC.
    
    This implementation is compatible with crypto-es library used in TypeScript SDK.
    Uses OpenSSL-compatible format: "Salted__" + salt + ciphertext
    
    Args:
        private_key: Private key to encrypt
        password: Password for encryption
        
    Returns:
        Base64 encoded encrypted string
    """
    # Generate random salt (8 bytes)
    import os
    salt = os.urandom(8)
    
    # Derive key and IV from password using OpenSSL's EVP_BytesToKey equivalent
    # This matches crypto-es behavior
    key_iv = _derive_key_and_iv(password.encode('utf-8'), salt, 32, 16)
    key = key_iv[:32]
    iv = key_iv[32:48]
    
    # Pad the private key (PKCS7 padding)
    padded_key = _pkcs7_pad(private_key.encode('utf-8'), 16)
    
    # Encrypt
    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_key) + encryptor.finalize()
    
    # Format as OpenSSL compatible: "Salted__" + salt + ciphertext
    encrypted_data = b'Salted__' + salt + ciphertext
    
    # Base64 encode
    return base64.b64encode(encrypted_data).decode('utf-8')


def decrypt_private_key(encrypted_private_key: str, password: str) -> str:
    """
    Decrypt private key using AES-256-CBC.
    
    This implementation is compatible with crypto-es library used in TypeScript SDK.
    
    Args:
        encrypted_private_key: Base64 encoded encrypted private key
        password: Password for decryption
        
    Returns:
        Decrypted private key
        
    Raises:
        ValueError: If decryption fails
    """
    try:
        # Decode base64
        encrypted_data = base64.b64decode(encrypted_private_key)
        
        # Check for "Salted__" prefix
        if not encrypted_data.startswith(b'Salted__'):
            raise ValueError("Invalid encrypted data format")
        
        # Extract salt and ciphertext
        salt = encrypted_data[8:16]
        ciphertext = encrypted_data[16:]
        
        # Derive key and IV from password
        key_iv = _derive_key_and_iv(password.encode('utf-8'), salt, 32, 16)
        key = key_iv[:32]
        iv = key_iv[32:48]
        
        # Decrypt
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Remove PKCS7 padding
        plaintext = _pkcs7_unpad(padded_plaintext)
        
        # Convert to string
        decrypted = plaintext.decode('utf-8')
        
        if not decrypted:
            raise ValueError("Decryption resulted in empty string")
        
        return decrypted
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")


def _derive_key_and_iv(password: bytes, salt: bytes, key_len: int, iv_len: int) -> bytes:
    """
    Derive key and IV using OpenSSL's EVP_BytesToKey algorithm.
    
    This matches the behavior of crypto-es to ensure compatibility.
    Uses MD5 hashing in multiple rounds.
    
    Args:
        password: Password bytes
        salt: Salt bytes
        key_len: Desired key length
        iv_len: Desired IV length
        
    Returns:
        Concatenated key + IV bytes
    """
    target_len = key_len + iv_len
    derived = b''
    last_hash = b''
    
    while len(derived) < target_len:
        last_hash = hashlib.md5(last_hash + password + salt).digest()
        derived += last_hash
    
    return derived[:target_len]


def _pkcs7_pad(data: bytes, block_size: int) -> bytes:
    """
    Apply PKCS7 padding to data.
    
    Args:
        data: Data to pad
        block_size: Block size in bytes
        
    Returns:
        Padded data
    """
    padding_len = block_size - (len(data) % block_size)
    padding = bytes([padding_len] * padding_len)
    return data + padding


def _pkcs7_unpad(data: bytes) -> bytes:
    """
    Remove PKCS7 padding from data.
    
    Args:
        data: Padded data
        
    Returns:
        Unpadded data
        
    Raises:
        ValueError: If padding is invalid
    """
    if not data:
        raise ValueError("Cannot unpad empty data")
    
    padding_len = data[-1]
    
    if padding_len > len(data) or padding_len == 0:
        raise ValueError("Invalid padding")
    
    # Verify all padding bytes are correct
    for i in range(padding_len):
        if data[-(i + 1)] != padding_len:
            raise ValueError("Invalid padding")
    
    return data[:-padding_len]
