"""Data formatters and transformers for Chipi SDK."""

from decimal import Decimal
from typing import Optional


def format_amount(amount: str, decimals: int = 18) -> str:
    """
    Format token amount with decimals.

    Converts human-readable amount to blockchain format.
    Example: "1.5" USDC (6 decimals) → "1500000"

    Args:
        amount: Amount as string (e.g., "1.5")
        decimals: Number of decimals for the token

    Returns:
        Formatted amount as string
    """
    # Convert to Decimal for precision
    amount_decimal = Decimal(amount)
    
    # Multiply by 10^decimals
    multiplier = Decimal(10 ** decimals)
    result = amount_decimal * multiplier
    
    # Convert to integer string (no decimal point)
    return str(int(result))


def format_address(address: str, length: int = 8) -> str:
    """
    Format address for display.

    Args:
        address: Full address string
        length: Number of characters to show on each side

    Returns:
        Formatted address like "0x1234...5678"
    """
    if len(address) <= length * 2:
        return address
    
    return f"{address[:length]}...{address[-length:]}"


def format_transaction_hash(tx_hash: str) -> str:
    """
    Format transaction hash for display.

    Args:
        tx_hash: Full transaction hash

    Returns:
        Formatted hash like "0x1234...5678"
    """
    return format_address(tx_hash, 6)


def format_currency(
    amount: float,
    currency: str = "USD",
    locale: str = "en_US"
) -> str:
    """
    Format amount as currency.

    Args:
        amount: Numeric amount
        currency: Currency code (USD, EUR, etc.)
        locale: Locale for formatting

    Returns:
        Formatted currency string
    """
    # Simple implementation - could use babel for full locale support
    if currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "EUR":
        return f"€{amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"


def format_number(
    value: float,
    decimals: int = 2,
    compact: bool = False
) -> str:
    """
    Format number for display.

    Args:
        value: Number to format
        decimals: Number of decimal places
        compact: Whether to use compact notation (K, M, B)

    Returns:
        Formatted number string
    """
    if compact:
        if value >= 1_000_000_000:
            return f"{value / 1_000_000_000:.{decimals}f}B"
        elif value >= 1_000_000:
            return f"{value / 1_000_000:.{decimals}f}M"
        elif value >= 1_000:
            return f"{value / 1_000:.{decimals}f}K"
    
    return f"{value:,.{decimals}f}"


def camel_to_snake(text: str) -> str:
    """
    Convert camelCase to snake_case.

    Args:
        text: camelCase string

    Returns:
        snake_case string
    """
    import re
    return re.sub(r'(?<!^)(?=[A-Z])', '_', text).lower()


def snake_to_camel(text: str) -> str:
    """
    Convert snake_case to camelCase.

    Args:
        text: snake_case string

    Returns:
        camelCase string
    """
    components = text.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def capitalize_first(text: str) -> str:
    """
    Capitalize first letter of string.

    Args:
        text: Input string

    Returns:
        String with first letter capitalized
    """
    if not text:
        return text
    return text[0].upper() + text[1:]
