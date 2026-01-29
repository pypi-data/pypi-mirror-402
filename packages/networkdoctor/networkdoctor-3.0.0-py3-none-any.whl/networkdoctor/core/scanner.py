"""
Network Scanning Engine for NetworkDoctor
"""
import asyncio
from typing import List, Dict, Any, Tuple, Optional
from networkdoctor.utils.network_tools import (
    check_connectivity,
    resolve_dns,
    ping_host,
    check_ssl_certificate,
    http_request,
)
from networkdoctor.utils.async_executor import AsyncExecutor
from networkdoctor.utils.security import RateLimiter
from networkdoctor.cli.validator import validate_target, expand_cidr


class NetworkScanner:
    """Network scanning engine"""
    
    def __init__(self, rate_limit: int = 10, timeout: float = 5.0):
        """
        Initialize network scanner.
        
        Args:
            rate_limit: Requests per second
            timeout: Default timeout in seconds
        """
        self.rate_limiter = RateLimiter(max_requests=rate_limit, time_window=1.0)
        self.executor = AsyncExecutor(max_concurrent=rate_limit)
        self.timeout = timeout
    
    async def scan_target(
        self,
        target: str,
        port: int,
        protocol: str = "tcp"
    ) -> Dict[str, Any]:
        """
        Scan a single target.
        
        Args:
            target: Hostname or IP
            port: Port number
            protocol: Protocol (tcp/udp)
            
        Returns:
            Scan results dictionary
        """
        await self.rate_limiter.wait_if_needed()
        
        from datetime import datetime
        results = {
            "target": target,
            "port": port,
            "protocol": protocol,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Basic connectivity
        results["connectivity"] = await check_connectivity(target, port, self.timeout)
        
        # DNS resolution
        if not target.replace(".", "").replace(":", "").isdigit():
            results["dns"] = await resolve_dns(target)
        
        # Ping (for IPs)
        try:
            import ipaddress
            ipaddress.ip_address(target)
            results["ping"] = await ping_host(target)
        except ValueError:
            pass
        
        # SSL certificate (for HTTPS)
        if port == 443 or protocol == "https":
            results["ssl"] = await check_ssl_certificate(target, port)
        
        # HTTP request (for HTTP/HTTPS)
        if protocol in ("http", "https"):
            url = f"{protocol}://{target}:{port}"
            results["http"] = await http_request(url, timeout=self.timeout)
        
        return results
    
    async def scan_targets(
        self,
        targets: List[Tuple[str, int, str]]
    ) -> List[Dict[str, Any]]:
        """
        Scan multiple targets concurrently.
        
        Args:
            targets: List of (host, port, protocol) tuples
            
        Returns:
            List of scan results
        """
        tasks = [
            self.scan_target(host, port, protocol)
            for host, port, protocol in targets
        ]
        
        results = await self.executor.execute_batch(tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                continue
            valid_results.append(result)
        
        return valid_results
    
    def expand_targets(self, targets: List[str]) -> List[Tuple[str, int, str]]:
        """
        Expand and normalize targets.
        
        Args:
            targets: List of target strings
            
        Returns:
            List of (host, port, protocol) tuples
        """
        expanded = []
        
        for target in targets:
            try:
                validated = validate_target(target)
                
                # Handle CIDR
                if validated[0] == "cidr":
                    ips = expand_cidr(validated[2])
                    for ip in ips:
                        expanded.append((ip, validated[1], "ip"))
                # Handle file
                elif validated[0] == "file":
                    from networkdoctor.cli.validator import read_targets_from_file
                    file_targets = read_targets_from_file(validated[2])
                    file_expanded = self.expand_targets(file_targets)
                    expanded.extend(file_expanded)
                else:
                    expanded.append(validated)
            except Exception:
                continue
        
        return expanded

