"""
Data Parsing Utilities for NetworkDoctor
"""
import re
import json
from typing import Dict, List, Any, Optional
from pathlib import Path


def parse_ip_address(ip_str: str) -> Optional[Dict[str, Any]]:
    """
    Parse IP address and extract information.
    
    Args:
        ip_str: IP address string
        
    Returns:
        Dictionary with IP information
    """
    try:
        import ipaddress
        ip = ipaddress.ip_address(ip_str)
        return {
            "address": str(ip),
            "version": ip.version,
            "is_private": ip.is_private,
            "is_loopback": ip.is_loopback,
            "is_multicast": ip.is_multicast,
            "is_reserved": ip.is_reserved,
        }
    except ValueError:
        return None


def parse_domain(domain: str) -> Dict[str, Any]:
    """
    Parse domain name and extract components.
    
    Args:
        domain: Domain name
        
    Returns:
        Dictionary with domain information
    """
    parts = domain.split(".")
    return {
        "full_domain": domain,
        "tld": parts[-1] if parts else "",
        "domain": parts[-2] if len(parts) >= 2 else "",
        "subdomain": ".".join(parts[:-2]) if len(parts) > 2 else "",
        "parts": parts,
    }


def parse_url(url: str) -> Dict[str, Any]:
    """
    Parse URL and extract components.
    
    Args:
        url: URL string
        
    Returns:
        Dictionary with URL components
    """
    from urllib.parse import urlparse, parse_qs
    
    parsed = urlparse(url)
    return {
        "scheme": parsed.scheme,
        "netloc": parsed.netloc,
        "path": parsed.path,
        "params": parsed.params,
        "query": parse_qs(parsed.query),
        "fragment": parsed.fragment,
        "hostname": parsed.hostname,
        "port": parsed.port,
    }


def parse_http_headers(headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Parse HTTP headers and extract useful information.
    
    Args:
        headers: Dictionary of HTTP headers
        
    Returns:
        Dictionary with parsed header information
    """
    result = {
        "server": headers.get("Server", ""),
        "content_type": headers.get("Content-Type", ""),
        "content_length": headers.get("Content-Length", ""),
        "cache_control": headers.get("Cache-Control", ""),
        "x_powered_by": headers.get("X-Powered-By", ""),
        "strict_transport_security": headers.get("Strict-Transport-Security", ""),
        "x_frame_options": headers.get("X-Frame-Options", ""),
        "content_security_policy": headers.get("Content-Security-Policy", ""),
    }
    
    # Parse Content-Type
    content_type = result["content_type"]
    if content_type:
        parts = content_type.split(";")
        result["mime_type"] = parts[0].strip()
        if len(parts) > 1:
            result["charset"] = parts[1].strip() if "charset" in parts[1] else ""
    
    return result


def parse_ssl_certificate(cert_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse SSL certificate information.
    
    Args:
        cert_info: Certificate information dictionary
        
    Returns:
        Parsed certificate information
    """
    from datetime import datetime
    
    result = cert_info.copy()
    
    # Parse dates
    if "not_before" in result:
        try:
            result["not_before_parsed"] = datetime.strptime(
                result["not_before"], "%b %d %H:%M:%S %Y %Z"
            )
        except Exception:
            pass
    
    if "not_after" in result:
        try:
            result["not_after_parsed"] = datetime.strptime(
                result["not_after"], "%b %d %H:%M:%S %Y %Z"
            )
        except Exception:
            pass
    
    # Calculate days until expiration
    if "not_after_parsed" in result:
        delta = result["not_after_parsed"] - datetime.now()
        result["days_until_expiry"] = delta.days
        result["expires_soon"] = delta.days < 30
    
    return result


def load_json_file(file_path: str) -> Any:
    """
    Load JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON data
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_file(data: Any, file_path: str):
    """
    Save data to JSON file.
    
    Args:
        data: Data to save
        file_path: Path to JSON file
    """
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)







