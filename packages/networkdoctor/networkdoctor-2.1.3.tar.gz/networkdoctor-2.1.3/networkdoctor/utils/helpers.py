"""
Common Helper Functions for NetworkDoctor
"""
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def format_bytes(bytes_count: int) -> str:
    """
    Format bytes in human-readable format.
    
    Args:
        bytes_count: Number of bytes
        
    Returns:
        Formatted bytes string
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_count < 1024.0:
            return f"{bytes_count:.2f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.2f} PB"


def calculate_health_score(issues: List[Dict[str, Any]]) -> int:
    """
    Calculate overall health score from issues.
    
    Args:
        issues: List of issue dictionaries with 'severity' field
        
    Returns:
        Health score (0-100)
    """
    if not issues:
        return 100
    
    severity_weights = {
        "critical": 20,
        "high": 10,
        "medium": 5,
        "low": 2,
        "info": 1,
    }
    
    total_penalty = 0
    for issue in issues:
        severity = issue.get("severity", "info").lower()
        penalty = severity_weights.get(severity, 1)
        total_penalty += penalty
    
    score = max(0, 100 - min(total_penalty, 100))
    return int(score)


def estimate_fix_time(issues: List[Dict[str, Any]]) -> str:
    """
    Estimate time to fix all issues.
    
    Args:
        issues: List of issue dictionaries
        
    Returns:
        Estimated time string
    """
    if not issues:
        return "No issues to fix"
    
    time_per_severity = {
        "critical": 60,  # minutes
        "high": 30,
        "medium": 15,
        "low": 5,
        "info": 1,
    }
    
    total_minutes = 0
    for issue in issues:
        severity = issue.get("severity", "info").lower()
        minutes = time_per_severity.get(severity, 1)
        total_minutes += minutes
    
    if total_minutes < 60:
        return f"~{total_minutes} minutes"
    else:
        hours = total_minutes / 60
        return f"~{hours:.1f} hours"


def get_severity_color(severity: str) -> str:
    """
    Get color code for severity level.
    
    Args:
        severity: Severity level
        
    Returns:
        Color name for Rich
    """
    colors = {
        "critical": "red",
        "high": "bright_red",
        "medium": "yellow",
        "low": "blue",
        "info": "cyan",
    }
    return colors.get(severity.lower(), "white")


def get_severity_icon(severity: str) -> str:
    """
    Get icon for severity level.
    
    Args:
        severity: Severity level
        
    Returns:
        Icon emoji/character
    """
    icons = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🔵",
        "info": "ℹ️",
    }
    return icons.get(severity.lower(), "⚪")


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple dictionaries.
    
    Args:
        *dicts: Dictionaries to merge
        
    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def safe_get(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary value.
    
    Args:
        data: Dictionary to search
        *keys: Keys to traverse
        default: Default value if not found
        
    Returns:
        Value or default
    """
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
            if current is None:
                return default
        else:
            return default
    return current if current is not None else default


def timestamp() -> str:
    """
    Get current timestamp string.
    
    Returns:
        ISO format timestamp
    """
    return datetime.now().isoformat()


def retry_with_backoff(
    func,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
):
    """
    Retry function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
        backoff_factor: Backoff multiplier
        
    Returns:
        Function result
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= backoff_factor
    
    raise last_exception








