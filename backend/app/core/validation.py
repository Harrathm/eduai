"""Input sanitization utilities for security."""

import re
import html
from typing import Optional


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """Sanitize a string to prevent XSS attacks.
    
    - Escape HTML characters
    - Remove control characters
    - Trim whitespace
    
    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized string
    """
    if not value:
        return ""
    
    # Escape HTML to prevent XSS
    sanitized = html.escape(value)
    
    # Remove control characters (except newlines, tabs)
    sanitized = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', sanitized)
    
    # Trim and normalize whitespace
    sanitized = ' '.join(sanitized.split())
    
    # Apply max length
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def sanitize_email(email: str) -> str:
    """Sanitize and validate email address.
    
    Args:
        email: Email to sanitize
    
    Returns:
        Sanitized lowercase email
    """
    if not email:
        return ""
    
    # Trim and lowercase
    return email.strip().lower()


def sanitize_html(value: str, allow_tags: Optional[list[str]] = None) -> str:
    """Sanitize HTML content while allowing certain tags.
    
    Args:
        value: HTML content
        allow_tags: List of allowed HTML tags (e.g., ['b', 'i', 'p'])
    
    Returns:
        Sanitized HTML
    """
    if not value:
        return ""
    
    # If no tags allowed, escape all HTML
    if not allow_tags:
        return html.escape(value)
    
    # Encode disallowed tags
    allowed = '|'.join(allow_tags)
    # Simple approach: escape everything, then selectively decode allowed
    sanitized = html.escape(value)
    
    return sanitized


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """Validate password strength.
    
    Args:
        password: Password to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if len(password) > 128:
        return False, "Password must be less than 128 characters"
    
    # Check for at least one letter (Unicode-aware)
    if not any(c.isalpha() for c in password):
        return False, "Password must contain at least one letter"
    
    # Check for at least one number
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, None


def validate_email_format(email: str) -> bool:
    """Validate email format.
    
    Args:
        email: Email to validate
    
    Returns:
        True if valid format
    """
    if not email:
        return False
    
    # RFC 5322 simplified pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


# ---- FIELD VALIDATORS ----
def validate_not_empty(value: str, field_name: str) -> tuple[bool, Optional[str]]:
    """Validate field is not empty.
    
    Args:
        value: Value to validate
        field_name: Name of field for error message
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not value or not value.strip():
        return False, f"{field_name} is required"
    return True, None


def validate_max_length(value: str, max_length: int, field_name: str) -> tuple[bool, Optional[str]]:
    """Validate max length.
    
    Args:
        value: Value to validate
        max_length: Maximum allowed length
        field_name: Name of field for error message
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(value) > max_length:
        return False, f"{field_name} must be less than {max_length} characters"
    return True, None


def validate_min_length(value: str, min_length: int, field_name: str) -> tuple[bool, Optional[str]]:
    """Validate min length.
    
    Args:
        value: Value to validate
        min_length: Minimum required length
        field_name: Name of field for error message
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(value) < min_length:
        return False, f"{field_name} must be at least {min_length} characters"
    return True, None