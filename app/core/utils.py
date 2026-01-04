# app/core/utils.py

"""
Common utility functions used across the application.
Provides reusable helpers for data transformation, validation, and common operations.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import re


# ==================== Data Transformation Utilities ====================

def to_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float with default fallback.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        float: Converted value or default
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def to_bool(value: Any) -> bool:
    """
    Convert various value types to boolean.
    
    Handles string "true"/"false", numbers, and other types.
    
    Args:
        value: Value to convert
        
    Returns:
        bool: Converted boolean value
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    if isinstance(value, (int, float)):
        return value != 0
    return bool(value)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers with default fallback for division by zero.
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if denominator is zero
        
    Returns:
        float: Division result or default
    """
    return numerator / denominator if denominator != 0 else default


def normalize_score(score: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """
    Normalize a score to be within min and max bounds.
    
    Args:
        score: Score to normalize
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        float: Normalized score
    """
    return max(min_val, min(max_val, score))


# ==================== Validation Utilities ====================

def is_valid_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_username(username: str, min_length: int = 3, max_length: int = 50) -> bool:
    """
    Validate username format and length.
    
    Args:
        username: Username to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not username:
        return False
    if len(username) < min_length or len(username) > max_length:
        return False
    # Only allow alphanumeric and underscores
    return bool(re.match(r'^[a-zA-Z0-9_]+$', username))


def is_valid_password(password: str, min_length: int = 8) -> bool:
    """
    Validate password meets minimum requirements.
    
    Args:
        password: Password to validate
        min_length: Minimum required length
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not password:
        return False
    return len(password) >= min_length


# ==================== Dictionary/Object Utilities ====================

def get_nested(data: Dict, *keys, default: Any = None) -> Any:
    """
    Safely get nested dictionary value.
    
    Args:
        data: Dictionary to search
        *keys: Sequence of keys to traverse
        default: Default value if key not found
        
    Returns:
        Value at nested location or default
        
    Example:
        get_nested({"a": {"b": {"c": 1}}}, "a", "b", "c") -> 1
    """
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
            if current is None:
                return default
        else:
            return default
    return current


def merge_dicts(*dicts: Dict) -> Dict:
    """
    Merge multiple dictionaries, with later dicts overriding earlier ones.
    
    Args:
        *dicts: Dictionaries to merge
        
    Returns:
        dict: Merged dictionary
    """
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def filter_none_values(data: Dict) -> Dict:
    """
    Remove keys with None values from dictionary.
    
    Args:
        data: Dictionary to filter
        
    Returns:
        dict: Filtered dictionary
    """
    return {k: v for k, v in data.items() if v is not None}


# ==================== String Utilities ====================

def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate string to maximum length with suffix.
    
    Args:
        text: String to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncating
        
    Returns:
        str: Truncated string
    """
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def clean_whitespace(text: str) -> str:
    """
    Clean excessive whitespace from string.
    
    Args:
        text: String to clean
        
    Returns:
        str: Cleaned string with normalized whitespace
    """
    if not text:
        return ""
    return " ".join(text.split())


# ==================== List Utilities ====================

def chunk_list(items: List, chunk_size: int) -> List[List]:
    """
    Split list into chunks of specified size.
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def deduplicate_list(items: List, key: Optional[callable] = None) -> List:
    """
    Remove duplicates from list while preserving order.
    
    Args:
        items: List to deduplicate
        key: Optional function to extract comparison key from item
        
    Returns:
        List with duplicates removed
    """
    if key is None:
        # Simple deduplication
        seen = set()
        result = []
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result
    else:
        # Deduplication with key function
        seen = set()
        result = []
        for item in items:
            k = key(item)
            if k not in seen:
                seen.add(k)
                result.append(item)
        return result


# ==================== Time/Date Utilities ====================

def format_datetime(dt: Optional[datetime], format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[str]:
    """
    Format datetime to string.
    
    Args:
        dt: Datetime to format
        format_str: Format string
        
    Returns:
        str: Formatted datetime or None
    """
    if dt is None:
        return None
    return dt.strftime(format_str)


def time_ago(dt: datetime) -> str:
    """
    Get human-readable time difference.
    
    Args:
        dt: Datetime to compare against now
        
    Returns:
        str: Human-readable time difference (e.g., "2 hours ago")
    """
    now = datetime.utcnow()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
