"""
Input Validation for NetworkDoctor
"""
import re
import ipaddress
from typing import List, Tuple, Optional
from pathlib import Path
from urllib.parse import urlparse


class ValidationError(Exception):
    """Raised when validation fails"""
    pass


def validate_target(target: str) -> Tuple[str, int, str]:
    """
    Validate and normalize a target input.
    
    Supports:
    - URLs: https://example.com, http://example.com:8080
    - IPs: 192.168.1.1, 192.168.1.1:443
    - Domains: example.com, example.com:8080
    - CIDR: 192.168.1.0/24
    - Files: @targets.txt
    
    Args:
        target: Target string to validate
        
    Returns:
        Tuple of (host, port, protocol)
        
    Raises:
        ValidationError: If target is invalid
    """
    # File reference
    if target.startswith("@"):
        file_path = target[1:]
        if not Path(file_path).exists():
            raise ValidationError(f"File not found: {file_path}")
        return ("file", 0, file_path)
    
    # URL parsing
    if target.startswith(("http://", "https://")):
        parsed = urlparse(target)
        host = parsed.hostname or ""
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        protocol = parsed.scheme
        if not host:
            raise ValidationError(f"Invalid URL: {target}")
        return (host, port, protocol)
    
    # CIDR notation
    if "/" in target:
        try:
            ipaddress.ip_network(target, strict=False)
            return ("cidr", 0, target)
        except ValueError:
            raise ValidationError(f"Invalid CIDR: {target}")
    
    # IP:port or domain:port
    if ":" in target:
        parts = target.rsplit(":", 1)
        host = parts[0]
        try:
            port = int(parts[1])
            if not (1 <= port <= 65535):
                raise ValidationError(f"Invalid port: {port}")
        except ValueError:
            raise ValidationError(f"Invalid port: {parts[1]}")
    else:
        host = target
        port = 80  # Default port
    
    # Validate IP address
    try:
        ipaddress.ip_address(host)
        return (host, port, "ip")
    except ValueError:
        pass
    
    # Validate domain name
    if is_valid_domain(host):
        return (host, port, "domain")
    
    raise ValidationError(f"Invalid target format: {target}")


def is_valid_domain(domain: str) -> bool:
    """
    Validate domain name format.
    
    Args:
        domain: Domain name to validate
        
    Returns:
        True if valid domain format
    """
    if not domain or len(domain) > 253:
        return False
    
    # Basic domain regex
    pattern = r"^([a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$"
    return bool(re.match(pattern, domain.lower()))


def validate_targets(targets: List[str]) -> List[Tuple[str, int, str]]:
    """
    Validate multiple targets.
    
    Args:
        targets: List of target strings
        
    Returns:
        List of validated (host, port, protocol) tuples
        
    Raises:
        ValidationError: If any target is invalid
    """
    validated = []
    for target in targets:
        try:
            validated.append(validate_target(target))
        except ValidationError as e:
            raise ValidationError(f"Invalid target '{target}': {e}")
    return validated


def expand_cidr(cidr: str) -> List[str]:
    """
    Expand CIDR notation to list of IP addresses.
    
    Args:
        cidr: CIDR notation (e.g., 192.168.1.0/24)
        
    Returns:
        List of IP addresses
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        return [str(ip) for ip in network.hosts()]
    except ValueError:
        raise ValidationError(f"Invalid CIDR: {cidr}")


def read_targets_from_file(file_path: str) -> List[str]:
    """
    Read targets from a file.
    
    Args:
        file_path: Path to file containing targets (one per line)
        
    Returns:
        List of target strings
    """
    path = Path(file_path)
    if not path.exists():
        raise ValidationError(f"File not found: {file_path}")
    
    targets = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                targets.append(line)
    
    return targets








