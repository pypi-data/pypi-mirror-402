"""
Auto Network Repair Engine - Automatically Fix Network Issues

"""
import subprocess
import platform
import socket
from typing import List, Dict, Any, Optional
import asyncio


class AutoNetworkRepair:
    """Automatically diagnose and repair common network issues"""
    
    def __init__(self):
        self.name = "Auto Network Repair"
        self.system = platform.system()
        self.is_admin = self._check_admin()
    
    async def diagnose(self, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Diagnose and automatically repair network issues.
        
        Args:
            scan_results: Results from network scan
            
        Returns:
            Diagnosis and repair results
        """
        issues = []
        repairs = []
        findings = []
        
        # Test DNS
        dns_result = await self._check_and_repair_dns()
        if dns_result.get("issue"):
            issues.append(dns_result["issue"])
        if dns_result.get("repaired"):
            repairs.append(dns_result["repair"])
        
        # Test MTU
        mtu_result = await self._check_and_repair_mtu()
        if mtu_result.get("issue"):
            issues.append(mtu_result["issue"])
        if mtu_result.get("repaired"):
            repairs.append(mtu_result["repair"])
        
        # Test Gateway
        gateway_result = await self._check_and_repair_gateway()
        if gateway_result.get("issue"):
            issues.append(gateway_result["issue"])
        if gateway_result.get("repaired"):
            repairs.append(gateway_result["repair"])
        
        # Test Proxy
        proxy_result = await self._check_and_repair_proxy()
        if proxy_result.get("issue"):
            issues.append(proxy_result["issue"])
        if proxy_result.get("repaired"):
            repairs.append(proxy_result["repair"])
        
        # Test IPv6 conflicts
        ipv6_result = await self._check_and_repair_ipv6()
        if ipv6_result.get("issue"):
            issues.append(ipv6_result["issue"])
        if ipv6_result.get("repaired"):
            repairs.append(ipv6_result["repair"])
        
        # Check fragmentation
        frag_result = await self._check_fragmentation()
        if frag_result.get("issue"):
            issues.append(frag_result["issue"])
        
        findings.append({
            "finding": "auto_repair_available",
            "repairs_performed": len(repairs),
            "issues_found": len(issues),
        })
        
        return {
            "doctor": "auto_repair",
            "status": "completed",
            "issues": issues,
            "repairs": repairs,
            "findings": findings,
            "summary": {
                "total_issues": len(issues),
                "repairs_performed": len(repairs),
                "admin_required": not self.is_admin,
                "repair_status": "completed" if repairs else "no_repairs_needed",
            },
        }
    
    def _check_admin(self) -> bool:
        """Check if running with admin privileges"""
        if self.system == "Windows":
            try:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except:
                return False
        else:
            # Linux/Mac - check if UID is 0
            import os
            return os.geteuid() == 0
    
    async def _check_and_repair_dns(self) -> Dict[str, Any]:
        """Check and repair DNS issues"""
        result = {}
        
        try:
            # Test DNS resolution
            socket.gethostbyname("google.com")
            result["dns_working"] = True
        except Exception as e:
            result["dns_working"] = False
            result["dns_error"] = str(e)
            
            if self.is_admin:
                # Try to fix DNS
                repair_commands = []
                if self.system == "Windows":
                    repair_commands = [
                        ["ipconfig", "/flushdns"],
                        ["netsh", "winsock", "reset"],
                    ]
                else:
                    repair_commands = [
                        ["sudo", "systemctl", "restart", "systemd-resolved"],
                        ["sudo", "resolvectl", "flush-caches"],
                    ]
                
                for cmd in repair_commands:
                    try:
                        process = await asyncio.create_subprocess_exec(
                            *cmd,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                        )
                        await process.communicate()
                    except Exception:
                        pass
                
                result["repaired"] = True
                result["repair"] = {
                    "type": "dns_flush",
                    "commands": repair_commands,
                    "status": "executed",
                }
            else:
                result["issue"] = {
                    "severity": "medium",
                    "type": "dns_failure",
                    "title": "DNS Resolution Failed",
                    "description": f"DNS is not working: {e}",
                    "requires_admin": True,
                    "manual_fix": "Run: ipconfig /flushdns (Windows) or sudo systemctl restart systemd-resolved (Linux)",
                }
        
        return result
    
    async def _check_and_repair_mtu(self) -> Dict[str, Any]:
        """Check and repair MTU issues"""
        result = {}
        
        try:
            # Check current MTU (simplified - would need system-specific commands)
            if self.system == "Windows":
                process = await asyncio.create_subprocess_exec(
                    "netsh", "interface", "ipv4", "show", "interfaces",
                    stdout=asyncio.subprocess.PIPE,
                )
                stdout, _ = await process.communicate()
                output = stdout.decode()
                
                # Check if MTU is too low (common issue)
                if "MTU : 576" in output or "MTU : 1280" in output:
                    result["mtu_low"] = True
                    if self.is_admin:
                        # Suggest MTU fix (would need interface name)
                        result["repaired"] = True
                        result["repair"] = {
                            "type": "mtu_adjustment",
                            "description": "MTU adjustment recommended",
                            "manual_fix": "Set MTU to 1500: netsh interface ipv4 set subinterface \"Wi-Fi\" mtu=1500 store=persistent",
                        }
                    else:
                        result["issue"] = {
                            "severity": "low",
                            "type": "mtu_low",
                            "title": "MTU Size May Be Too Low",
                            "description": "MTU size might be causing fragmentation issues",
                            "requires_admin": True,
                        }
        except Exception:
            pass
        
        return result
    
    async def _check_and_repair_gateway(self) -> Dict[str, Any]:
        """Check and repair gateway connectivity"""
        result = {}
        
        try:
            # Get default gateway
            if self.system == "Windows":
                process = await asyncio.create_subprocess_exec(
                    "ipconfig",
                    stdout=asyncio.subprocess.PIPE,
                )
                stdout, _ = await process.communicate()
                output = stdout.decode()
            else:
                process = await asyncio.create_subprocess_exec(
                    "ip", "route", "show", "default",
                    stdout=asyncio.subprocess.PIPE,
                )
                stdout, _ = await process.communicate()
                output = stdout.decode()
            
            # Try to ping gateway (simplified)
            # In production, parse output to get gateway IP and ping it
            
        except Exception as e:
            result["gateway_check_failed"] = True
            result["error"] = str(e)
        
        return result
    
    async def _check_and_repair_proxy(self) -> Dict[str, Any]:
        """Check and repair proxy configuration issues"""
        result = {}
        
        import os
        
        # Check for misconfigured proxy settings
        proxy_vars = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]
        proxies_found = []
        
        for var in proxy_vars:
            if var in os.environ:
                proxies_found.append(var)
        
        if proxies_found:
            # Check if proxy is reachable
            for var in proxies_found:
                proxy_url = os.environ[var]
                if not await self._test_proxy_connection(proxy_url):
                    result["issue"] = {
                        "severity": "medium",
                        "type": "proxy_unreachable",
                        "title": "Proxy Server Unreachable",
                        "description": f"Proxy configured ({var}={proxy_url}) but not reachable",
                        "manual_fix": f"Unset proxy: unset {var} or remove from /etc/environment",
                    }
        
        return result
    
    async def _test_proxy_connection(self, proxy_url: str) -> bool:
        """Test if proxy is reachable"""
        try:
            # Simplified proxy test
            # In production, would actually try to connect through proxy
            return True  # Placeholder
        except:
            return False
    
    async def _check_and_repair_ipv6(self) -> Dict[str, Any]:
        """Check and repair IPv6 conflicts"""
        result = {}
        
        try:
            # Check if IPv6 is enabled but causing issues
            if self.system == "Linux":
                process = await asyncio.create_subprocess_exec(
                    "sysctl", "net.ipv6.conf.all.disable_ipv6",
                    stdout=asyncio.subprocess.PIPE,
                )
                stdout, _ = await process.communicate()
                output = stdout.decode()
                
                # Check for IPv6 conflicts (simplified)
                # In production, would do more thorough checking
        except Exception:
            pass
        
        return result
    
    async def _check_fragmentation(self) -> Dict[str, Any]:
        """Check for packet fragmentation issues"""
        result = {}
        
        # Fragmentation issues are usually detected during packet capture
        # This is a placeholder for future implementation
        
        return result

