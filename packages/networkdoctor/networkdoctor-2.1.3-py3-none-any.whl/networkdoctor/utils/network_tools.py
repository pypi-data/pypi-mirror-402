"""
Raw Network Operations for NetworkDoctor
"""
import asyncio
import socket
import ssl
from typing import Optional, Tuple, Dict, Any
import aiohttp
import dns.resolver
import dns.exception
from ping3 import ping


async def check_connectivity(host: str, port: int, timeout: float = 5.0) -> bool:
    """
    Check if a host:port is reachable.
    
    Args:
        host: Hostname or IP
        port: Port number
        timeout: Connection timeout in seconds
        
    Returns:
        True if reachable
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except (asyncio.TimeoutError, OSError, ConnectionError):
        return False


async def resolve_dns(hostname: str, record_type: str = "A") -> Optional[list]:
    """
    Resolve DNS record.
    
    Args:
        hostname: Domain name
        record_type: DNS record type (A, AAAA, MX, etc.)
        
    Returns:
        List of resolved values or None
    """
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 5
        answers = resolver.resolve(hostname, record_type)
        return [str(rdata) for rdata in answers]
    except (dns.exception.DNSException, Exception):
        return None


async def ping_host(host: str, count: int = 3, timeout: float = 1.0) -> Dict[str, Any]:
    """
    Ping a host and get statistics.
    
    Args:
        host: Hostname or IP
        count: Number of pings
        timeout: Timeout per ping
        
    Returns:
        Dictionary with ping statistics
    """
    results = []
    for _ in range(count):
        try:
            delay = ping(host, timeout=timeout)
            if delay is not None:
                results.append(delay * 1000)  # Convert to ms
        except Exception:
            pass
    
    if not results:
        return {
            "success": False,
            "packet_loss": 100.0,
            "avg_latency": None,
            "min_latency": None,
            "max_latency": None
        }
    
    return {
        "success": True,
        "packet_loss": ((count - len(results)) / count) * 100,
        "avg_latency": sum(results) / len(results),
        "min_latency": min(results),
        "max_latency": max(results)
    }


async def check_ssl_certificate(host: str, port: int = 443) -> Dict[str, Any]:
    """
    Check SSL certificate details.
    
    Args:
        host: Hostname
        port: Port number
        
    Returns:
        Dictionary with certificate information
    """
    try:
        context = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                return {
                    "valid": True,
                    "subject": dict(x[0] for x in cert.get("subject", [])),
                    "issuer": dict(x[0] for x in cert.get("issuer", [])),
                    "version": cert.get("version"),
                    "not_before": cert.get("notBefore"),
                    "not_after": cert.get("notAfter"),
                    "serial_number": cert.get("serialNumber"),
                }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }


async def http_request(
    url: str,
    method: str = "GET",
    timeout: float = 10.0,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Make HTTP request and get response details.
    
    Args:
        url: URL to request
        method: HTTP method
        timeout: Request timeout
        headers: Optional headers
        
    Returns:
        Dictionary with response information
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                url,
                timeout=aiohttp.ClientTimeout(total=timeout),
                headers=headers or {}
            ) as response:
                return {
                    "success": True,
                    "status_code": response.status,
                    "headers": dict(response.headers),
                    "url": str(response.url),
                    "content_type": response.headers.get("Content-Type", ""),
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_local_ip() -> str:
    """
    Get local IP address.
    
    Returns:
        Local IP address
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def is_port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    """
    Check if a port is open (synchronous).
    
    Args:
        host: Hostname or IP
        port: Port number
        timeout: Connection timeout
        
    Returns:
        True if port is open
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False








