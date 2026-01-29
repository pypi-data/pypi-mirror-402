"""Validation utilities for Chipi SDK."""

import re
from typing import Any


def is_valid_api_key(api_key: str) -> bool:
    """
    Validate API key format.

    Args:
        api_key: API key string to validate

    Returns:
        True if valid, False otherwise
    """
    if not api_key or not isinstance(api_key, str):
        return False
    
    # API keys should be non-empty strings with reasonable length
    return len(api_key) > 0 and len(api_key) < 500


def validate_address(address: str) -> bool:
    """
    Validate Starknet address format.

    Args:
        address: Starknet address to validate

    Returns:
        True if valid, False otherwise
    """
    if not address or not isinstance(address, str):
        return False
    
    # Starknet addresses should start with 0x and be hex
    if not address.startswith("0x"):
        return False
    
    # Remove 0x prefix and validate hex
    hex_part = address[2:]
    if not hex_part:
        return False
    
    # Check if it's valid hex (0-9, a-f, A-F)
    return bool(re.match(r"^[0-9a-fA-F]+$", hex_part))


def validate_error_response(response: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and normalize error response.

    Args:
        response: Error response dictionary

    Returns:
        Normalized error response with message and code
    """
    if not isinstance(response, dict):
        return {
            "message": "Unknown error occurred",
            "code": "UNKNOWN_ERROR",
        }
    
    message = response.get("message")
    if not message:
        message = response.get("error", "Unknown error occurred")
    
    code = response.get("code", "UNKNOWN_ERROR")
    
    return {
        "message": str(message),
        "code": str(code),
    }
