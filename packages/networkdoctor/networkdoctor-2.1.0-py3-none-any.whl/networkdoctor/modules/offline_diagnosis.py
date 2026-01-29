"""
Offline Diagnosis Mode - Full local analysis without internet
Created by: frankvena25
"""
import socket
import subprocess
import platform
import psutil
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime


class OfflineDiagnosis:
    """Perform full network diagnosis without internet connection"""
    
    def __init__(self):
        self.name = "Offline Diagnosis Mode"
        self.system = platform.system()
    
    async def diagnose(self, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform offline network diagnosis (no internet required).
        
        Args:
            scan_results: Results from network scan
            
        Returns:
            Offline diagnosis results
        """
        issues = []
        findings = []
        
        # Local network configuration check
        local_config = await self._check_local_config()
        if local_config.get("issues"):
            issues.extend(local_config["issues"])
        
        # Network interface analysis
        interface_analysis = await self._analyze_interfaces()
        if interface_analysis.get("issues"):
            issues.extend(interface_analysis["issues"])
        
        # DNS configuration (local)
        dns_config = await self._check_dns_config_local()
        if dns_config.get("issues"):
            issues.extend(dns_config["issues"])
        
        # Routing table analysis
        routing_analysis = await self._analyze_routing_table()
        if routing_analysis.get("issues"):
            issues.extend(routing_analysis["issues"])
        
        # ARP table analysis
        arp_analysis = await self._analyze_arp_table()
        if arp_analysis.get("findings"):
            findings.extend(arp_analysis["findings"])
        
        # System network stats
        system_stats = await self._get_system_network_stats()
        
        # Connection quality (local network only)
        local_connectivity = await self._test_local_connectivity()
        if local_connectivity.get("issues"):
            issues.extend(local_connectivity["issues"])
        
        findings.append({
            "finding": "offline_diagnosis",
            "mode": "offline",
            "local_network_accessible": local_connectivity.get("local_network_ok", False),
            "interfaces_analyzed": len(interface_analysis.get("interfaces", [])),
        })
        
        return {
            "doctor": "offline_diagnosis",
            "status": "completed",
            "issues": issues,
            "findings": findings,
            "local_config": local_config,
            "interface_analysis": interface_analysis,
            "dns_config": dns_config,
            "routing_analysis": routing_analysis,
            "arp_analysis": arp_analysis,
            "system_stats": system_stats,
            "local_connectivity": local_connectivity,
            "summary": {
                "total_issues": len(issues),
                "interfaces_count": len(interface_analysis.get("interfaces", [])),
                "local_network_ok": local_connectivity.get("local_network_ok", False),
                "mode": "offline",
            },
        }
    
    async def _check_local_config(self) -> Dict[str, Any]:
        """Check local network configuration"""
        issues = []
        config = {}
        
        try:
            # Get hostname
            hostname = socket.gethostname()
            config["hostname"] = hostname
            
            # Get local IP
            try:
                # Connect to external IP to get local IP (but we're offline, so use alternate method)
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    # Doesn't actually connect, just prepares socket
                    s.connect(('10.255.255.255', 1))
                    local_ip = s.getsockname()[0]
                except Exception:
                    local_ip = "127.0.0.1"
                finally:
                    s.close()
                
                config["local_ip"] = local_ip
            except Exception as e:
                issues.append({
                    "severity": "low",
                    "type": "ip_detection",
                    "title": "Could not determine local IP",
                    "description": str(e),
                })
            
            # Check if local IP is valid
            if config.get("local_ip") == "127.0.0.1":
                issues.append({
                    "severity": "medium",
                    "type": "loopback_only",
                    "title": "Only loopback interface detected",
                    "description": "No network interface with external IP found",
                    "recommendations": [
                        "Check if network cable is connected",
                        "Verify WiFi is connected",
                        "Check network adapter status",
                    ],
                })
        
        except Exception as e:
            issues.append({
                "severity": "low",
                "type": "config_check_error",
                "title": "Error checking local config",
                "description": str(e),
            })
        
        return {
            "config": config,
            "issues": issues,
        }
    
    async def _analyze_interfaces(self) -> Dict[str, Any]:
        """Analyze network interfaces"""
        issues = []
        interfaces = []
        
        try:
            if self.system == "Linux":
                process = await asyncio.create_subprocess_exec(
                    "ip", "addr", "show",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await process.communicate()
                output = stdout.decode()
                
                # Parse interface info
                current_interface = None
                for line in output.split("\n"):
                    if ":" in line and "state" in line.lower():
                        # Interface line
                        parts = line.split(": ")
                        if len(parts) >= 2:
                            current_interface = parts[1].split()[0]
                            state = parts[1].split()[1] if len(parts[1].split()) > 1 else "unknown"
                            interfaces.append({
                                "name": current_interface,
                                "state": state,
                            })
                    elif current_interface and "inet " in line:
                        # IP address line
                        ip_part = line.strip().split()[1]
                        ip = ip_part.split("/")[0]
                        interfaces[-1]["ip"] = ip
                
            elif self.system == "Windows":
                process = await asyncio.create_subprocess_exec(
                    "ipconfig",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await process.communicate()
                output = stdout.decode()
                
                # Parse Windows ipconfig output (simplified)
                current_interface = None
                for line in output.split("\n"):
                    if "adapter" in line.lower():
                        current_interface = line.split(":")[0].strip()
                    elif current_interface and "IPv4" in line:
                        ip = line.split(":")[-1].strip()
                        interfaces.append({
                            "name": current_interface,
                            "ip": ip,
                            "state": "up",
                        })
        
        except Exception as e:
            issues.append({
                "severity": "low",
                "type": "interface_analysis_error",
                "title": "Error analyzing interfaces",
                "description": str(e),
            })
        
        # Check for issues
        if not interfaces:
            issues.append({
                "severity": "medium",
                "type": "no_interfaces",
                "title": "No network interfaces found",
                "description": "No active network interfaces detected",
            })
        
        # Check for interfaces in down state
        down_interfaces = [i for i in interfaces if i.get("state", "").lower() in ["down", "disabled"]]
        if down_interfaces:
            issues.append({
                "severity": "low",
                "type": "down_interfaces",
                "title": f"Interfaces in down state: {len(down_interfaces)}",
                "description": f"Some interfaces are not active: {', '.join([i['name'] for i in down_interfaces])}",
            })
        
        return {
            "interfaces": interfaces,
            "issues": issues,
        }
    
    async def _check_dns_config_local(self) -> Dict[str, Any]:
        """Check DNS configuration (local settings only)"""
        issues = []
        dns_config = {}
        
        try:
            if self.system == "Linux":
                # Try to read resolv.conf
                try:
                    with open("/etc/resolv.conf", "r") as f:
                        resolv_content = f.read()
                        
                        # Extract nameservers
                        nameservers = []
                        for line in resolv_content.split("\n"):
                            if line.startswith("nameserver"):
                                ns = line.split()[1] if len(line.split()) > 1 else None
                                if ns:
                                    nameservers.append(ns)
                        
                        dns_config["nameservers"] = nameservers
                except FileNotFoundError:
                    # Try systemd-resolved
                    process = await asyncio.create_subprocess_exec(
                        "resolvectl", "status",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, _ = await process.communicate()
                    if stdout:
                        output = stdout.decode()
                        # Extract DNS servers from output (simplified)
                        nameservers = []
                        for line in output.split("\n"):
                            if "DNS Servers:" in line or "Current DNS Server:" in line:
                                parts = line.split(":")
                                if len(parts) > 1:
                                    dns_list = parts[1].strip().split()
                                    nameservers.extend(dns_list)
                        dns_config["nameservers"] = nameservers
            
            elif self.system == "Windows":
                process = await asyncio.create_subprocess_exec(
                    "ipconfig", "/all",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await process.communicate()
                output = stdout.decode()
                
                # Extract DNS servers
                nameservers = []
                for line in output.split("\n"):
                    if "DNS Servers" in line:
                        dns_ip = line.split(":")[-1].strip()
                        if dns_ip:
                            nameservers.append(dns_ip)
                
                dns_config["nameservers"] = nameservers
            
            # Check for missing DNS servers
            if not dns_config.get("nameservers"):
                issues.append({
                    "severity": "medium",
                    "type": "no_dns_servers",
                    "title": "No DNS servers configured",
                    "description": "DNS servers are not configured",
                    "recommendations": [
                        "Configure DNS servers: 8.8.8.8, 8.8.4.4 (Google) or 1.1.1.1, 1.0.0.1 (Cloudflare)",
                    ],
                })
        
        except Exception as e:
            issues.append({
                "severity": "low",
                "type": "dns_config_error",
                "title": "Error checking DNS config",
                "description": str(e),
            })
        
        return {
            "dns_config": dns_config,
            "issues": issues,
        }
    
    async def _analyze_routing_table(self) -> Dict[str, Any]:
        """Analyze routing table"""
        issues = []
        routes = []
        
        try:
            if self.system == "Linux":
                process = await asyncio.create_subprocess_exec(
                    "ip", "route", "show",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await process.communicate()
                output = stdout.decode()
                
                for line in output.split("\n"):
                    if line.strip():
                        routes.append({"route": line.strip()})
                        
                        # Check for default gateway
                        if "default" in line or "0.0.0.0" in line:
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part == "via":
                                    gateway = parts[i+1] if i+1 < len(parts) else None
                                    routes[-1]["gateway"] = gateway
            
            elif self.system == "Windows":
                process = await asyncio.create_subprocess_exec(
                    "route", "print",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await process.communicate()
                output = stdout.decode()
                
                # Parse routes (simplified)
                for line in output.split("\n"):
                    if "0.0.0.0" in line and "On-link" not in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            routes.append({
                                "route": line.strip(),
                                "gateway": parts[2] if len(parts) > 2 else None,
                            })
            
            # Check for missing default gateway
            has_default_gateway = any("default" in str(r.get("route", "")) or "0.0.0.0" in str(r.get("route", "")) for r in routes)
            if not has_default_gateway:
                issues.append({
                    "severity": "high",
                    "type": "no_default_gateway",
                    "title": "No default gateway configured",
                    "description": "Default gateway is missing, cannot reach external networks",
                })
        
        except Exception as e:
            issues.append({
                "severity": "low",
                "type": "routing_analysis_error",
                "title": "Error analyzing routing table",
                "description": str(e),
            })
        
        return {
            "routes": routes,
            "issues": issues,
        }
    
    async def _analyze_arp_table(self) -> Dict[str, Any]:
        """Analyze ARP table for local network discovery"""
        findings = []
        
        try:
            if self.system == "Linux":
                process = await asyncio.create_subprocess_exec(
                    "arp", "-a",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await process.communicate()
                output = stdout.decode()
                
                devices = []
                for line in output.split("\n"):
                    if "(" in line and ")" in line:
                        # Extract IP and MAC
                        parts = line.split()
                        if len(parts) >= 4:
                            ip = parts[1].strip("()")
                            mac = parts[3] if len(parts) > 3 else "unknown"
                            devices.append({"ip": ip, "mac": mac})
                
                if devices:
                    findings.append({
                        "finding": "local_devices",
                        "count": len(devices),
                        "devices": devices[:10],  # Limit to 10 devices
                    })
        
        except Exception:
            pass
        
        return {
            "findings": findings,
        }
    
    async def _get_system_network_stats(self) -> Dict[str, Any]:
        """Get system network statistics"""
        stats = {}
        
        try:
            net_io = psutil.net_io_counters()
            if net_io:
                stats = {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                    "errin": net_io.errin,
                    "errout": net_io.errout,
                    "dropin": net_io.dropin,
                    "dropout": net_io.dropout,
                }
        except Exception:
            pass
        
        return stats
    
    async def _test_local_connectivity(self) -> Dict[str, Any]:
        """Test local network connectivity"""
        issues = []
        local_network_ok = False
        
        try:
            # Try to ping default gateway (if available)
            # Try common local addresses
            local_targets = ["127.0.0.1", "localhost"]
            
            # Try to ping localhost
            if self.system == "Linux":
                process = await asyncio.create_subprocess_exec(
                    "ping", "-c", "1", "127.0.0.1",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            else:  # Windows
                process = await asyncio.create_subprocess_exec(
                    "ping", "-n", "1", "127.0.0.1",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            
            stdout, _ = await process.communicate()
            
            if process.returncode == 0:
                local_network_ok = True
            else:
                issues.append({
                    "severity": "critical",
                    "type": "localhost_unreachable",
                    "title": "Cannot ping localhost",
                    "description": "Local network stack is not functioning",
                })
        
        except Exception as e:
            issues.append({
                "severity": "medium",
                "type": "connectivity_test_error",
                "title": "Error testing local connectivity",
                "description": str(e),
            })
        
        return {
            "local_network_ok": local_network_ok,
            "issues": issues,
        }

