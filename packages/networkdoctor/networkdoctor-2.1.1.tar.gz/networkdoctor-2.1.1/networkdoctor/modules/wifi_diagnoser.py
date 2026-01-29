"""
WiFi Diagnoser - Detect Rogue Devices, Evil Twin AP, ARP Spoofing

"""
import subprocess
import platform
import socket
import re
import asyncio
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict


class WiFiDiagnoser:
    """WiFi network diagnosis with security checks"""
    
    def __init__(self):
        self.name = "WiFi Diagnoser"
        self.system = platform.system()
    
    async def diagnose(self, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Diagnose WiFi issues including security threats.
        
        Args:
            scan_results: Results from network scan
            
        Returns:
            WiFi diagnosis with security findings
        """
        issues = []
        findings = []
        
        # Detect rogue devices
        rogue_devices = await self._detect_rogue_devices()
        if rogue_devices:
            issues.append({
                "severity": "high",
                "type": "rogue_devices",
                "title": f"Rogue Devices Detected: {len(rogue_devices)}",
                "description": "Unknown devices found on network",
                "rogue_devices": rogue_devices,
                "recommendations": [
                    "Review authorized device list",
                    "Block unauthorized MAC addresses",
                    "Change WiFi password immediately",
                    "Enable MAC address filtering",
                ],
            })
            findings.append({
                "finding": "rogue_devices",
                "count": len(rogue_devices),
                "devices": rogue_devices,
            })
        
        # Detect evil twin AP
        evil_twin = await self._detect_evil_twin()
        if evil_twin:
            issues.append({
                "severity": "critical",
                "type": "evil_twin_ap",
                "title": "Evil Twin Access Point Detected",
                "description": "Suspicious access point with similar name detected",
                "evil_twin_details": evil_twin,
                "recommendations": [
                    "Disconnect from suspicious network immediately",
                    "Verify legitimate WiFi network name (SSID)",
                    "Check router MAC address",
                    "Change WiFi password",
                    "Enable WPA3 security",
                ],
            })
            findings.append({
                "finding": "evil_twin_ap",
                "threat_level": "critical",
                "details": evil_twin,
            })
        
        # Detect ARP spoofing
        arp_spoofing = await self._detect_arp_spoofing()
        if arp_spoofing:
            issues.append({
                "severity": "critical",
                "type": "arp_spoofing",
                "title": "ARP Spoofing Attack Detected",
                "description": "Multiple MAC addresses claiming same IP address",
                "arp_spoofing_details": arp_spoofing,
                "recommendations": [
                    "Enable ARP inspection on switch/router",
                    "Use static ARP entries for critical devices",
                    "Enable DHCP snooping",
                    "Monitor network for suspicious activity",
                    "Consider using VPN for sensitive traffic",
                ],
            })
            findings.append({
                "finding": "arp_spoofing",
                "threat_level": "critical",
                "details": arp_spoofing,
            })
        
        # Check WiFi signal strength
        signal_info = await self._check_signal_strength()
        if signal_info and signal_info.get("strength") < -80:
            issues.append({
                "severity": "low",
                "type": "weak_signal",
                "title": f"Weak WiFi Signal: {signal_info.get('strength')} dBm",
                "description": "WiFi signal strength is weak, may cause connectivity issues",
                "recommendations": [
                    "Move closer to access point",
                    "Reposition router/access point",
                    "Use WiFi range extenders",
                    "Check for interference",
                ],
            })
        
        return {
            "doctor": "wifi",
            "status": "completed",
            "issues": issues,
            "findings": findings,
            "summary": {
                "total_issues": len(issues),
                "rogue_devices_count": len(rogue_devices) if rogue_devices else 0,
                "evil_twin_detected": bool(evil_twin),
                "arp_spoofing_detected": bool(arp_spoofing),
                "security_threats": sum(1 for issue in issues if issue["severity"] in ["high", "critical"]),
            },
        }
    
    async def _detect_rogue_devices(self) -> Optional[List[Dict[str, Any]]]:
        """Detect rogue (unauthorized) devices on network"""
        try:
            # Get ARP table to see devices on network
            arp_table = await self._get_arp_table()
            
            if not arp_table:
                return None
            
            # Get current device MAC (to exclude from rogue list)
            current_mac = await self._get_current_mac()
            
            # Get authorized devices (from known patterns)
            # In production, would use a whitelist or management system
            authorized_macs = self._get_authorized_devices()
            
            # Identify rogue devices
            rogue_devices = []
            for entry in arp_table:
                mac = entry.get("mac", "").upper()
                ip = entry.get("ip", "")
                
                # Skip current device
                if mac == current_mac:
                    continue
                
                # Check if device is authorized
                if mac not in authorized_macs:
                    # Try to get vendor info from MAC
                    vendor = self._get_vendor_from_mac(mac)
                    
                    rogue_devices.append({
                        "mac": mac,
                        "ip": ip,
                        "vendor": vendor,
                        "first_seen": entry.get("timestamp"),
                    })
            
            return rogue_devices if rogue_devices else None
            
        except Exception as e:
            # If detection fails, return None (don't raise false alarms)
            return None
    
    async def _get_arp_table(self) -> List[Dict[str, Any]]:
        """Get ARP table from system"""
        arp_table = []
        
        try:
            if self.system == "Linux":
                process = await asyncio.create_subprocess_exec(
                    "arp", "-a",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await process.communicate()
                output = stdout.decode()
                
                # Parse ARP output
                # Format: hostname (IP) at MAC [ether] on interface
                pattern = r'\(([\d.]+)\) at ([a-fA-F0-9:]+) \[ether\]'
                matches = re.findall(pattern, output)
                
                for ip, mac in matches:
                    arp_table.append({
                        "ip": ip,
                        "mac": mac,
                        "timestamp": None,
                    })
                    
            elif self.system == "Windows":
                process = await asyncio.create_subprocess_exec(
                    "arp", "-a",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await process.communicate()
                output = stdout.decode()
                
                # Parse Windows ARP output
                pattern = r'([\d.]+)\s+([a-fA-F0-9-]+)'
                matches = re.findall(pattern, output)
                
                for ip, mac in matches:
                    # Convert Windows MAC format (xx-xx-xx-xx-xx-xx) to standard
                    mac_std = mac.replace("-", ":")
                    arp_table.append({
                        "ip": ip,
                        "mac": mac_std,
                        "timestamp": None,
                    })
        
        except Exception:
            pass
        
        return arp_table
    
    async def _get_current_mac(self) -> Optional[str]:
        """Get MAC address of current device"""
        try:
            # Get default interface
            if self.system == "Linux":
                process = await asyncio.create_subprocess_exec(
                    "ip", "link", "show",
                    stdout=asyncio.subprocess.PIPE,
                )
                stdout, _ = await process.communicate()
                output = stdout.decode()
                
                # Find MAC address in output
                pattern = r'link/ether ([a-fA-F0-9:]+)'
                match = re.search(pattern, output)
                if match:
                    return match.group(1).upper()
                    
            elif self.system == "Windows":
                process = await asyncio.create_subprocess_exec(
                    "getmac",
                    stdout=asyncio.subprocess.PIPE,
                )
                stdout, _ = await process.communicate()
                output = stdout.decode()
                
                # Parse MAC from getmac output
                pattern = r'([a-fA-F0-9-]+)'
                matches = re.findall(pattern, output)
                if matches:
                    return matches[0].replace("-", ":").upper()
        
        except Exception:
            pass
        
        return None
    
    def _get_authorized_devices(self) -> Set[str]:
        """Get list of authorized MAC addresses (placeholder)"""
        # In production, would load from config file or management system
        # For now, return empty set (all devices will be flagged)
        # User can whitelist their own devices
        return set()
    
    def _get_vendor_from_mac(self, mac: str) -> Optional[str]:
        """Get vendor name from MAC address OUI (first 3 bytes)"""
        # Simplified vendor lookup (in production, use full OUI database)
        oui = mac[:8].replace(":", "").upper()
        
        # Common OUI prefixes (partial list)
        vendor_db = {
            "00:50:56": "VMware",
            "00:0C:29": "VMware",
            "00:15:5D": "Microsoft",
            "00:1D:72": "Apple",
            "00:23:DF": "Apple",
            "B8:27:EB": "Raspberry Pi",
            "DC:A6:32": "Raspberry Pi",
        }
        
        # Check first 3 bytes
        for oui_prefix, vendor in vendor_db.items():
            if mac.startswith(oui_prefix):
                return vendor
        
        return "Unknown"
    
    async def _detect_evil_twin(self) -> Optional[Dict[str, Any]]:
        """Detect evil twin access points"""
        try:
            # Get available WiFi networks
            networks = await self._scan_wifi_networks()
            
            if not networks:
                return None
            
            # Group networks by similar SSID
            ssid_groups = defaultdict(list)
            for net in networks:
                ssid = net.get("ssid", "")
                # Normalize SSID for comparison
                normalized = ssid.lower().strip()
                ssid_groups[normalized].append(net)
            
            # Check for duplicate SSIDs with different MACs (evil twin indicator)
            evil_twins = []
            for ssid, networks_list in ssid_groups.items():
                if len(networks_list) > 1:
                    # Multiple networks with same SSID - potential evil twin
                    macs = [n.get("bssid", "") for n in networks_list if n.get("bssid")]
                    if len(set(macs)) > 1:  # Different MAC addresses
                        # Get signal strengths
                        signals = [n.get("signal", 0) for n in networks_list]
                        
                        evil_twins.append({
                            "ssid": ssid,
                            "network_count": len(networks_list),
                            "bssids": macs,
                            "signal_strengths": signals,
                            "threat_level": "high" if max(signals) > -60 else "medium",
                        })
            
            if evil_twins:
                return {
                    "detected": True,
                    "evil_twins": evil_twins,
                    "recommendation": "Only connect to known legitimate network",
                }
        
        except Exception:
            pass
        
        return None
    
    async def _scan_wifi_networks(self) -> List[Dict[str, Any]]:
        """Scan for available WiFi networks"""
        networks = []
        
        try:
            if self.system == "Linux":
                # Use iwlist or nmcli
                try:
                    process = await asyncio.create_subprocess_exec(
                        "nmcli", "-t", "-f", "SSID,BSSID,SIGNAL", "device", "wifi", "list",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, _ = await process.communicate()
                    output = stdout.decode()
                    
                    for line in output.strip().split("\n"):
                        if ":" in line:
                            parts = line.split(":")
                            if len(parts) >= 3:
                                networks.append({
                                    "ssid": parts[0] if parts[0] else "Hidden",
                                    "bssid": parts[1] if len(parts) > 1 else "",
                                    "signal": int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0,
                                })
                except Exception:
                    pass
        
        except Exception:
            pass
        
        return networks
    
    async def _detect_arp_spoofing(self) -> Optional[Dict[str, Any]]:
        """Detect ARP spoofing by checking for duplicate IP-MAC mappings"""
        try:
            arp_table = await self._get_arp_table()
            
            if not arp_table:
                return None
            
            # Group by IP address
            ip_to_macs = defaultdict(list)
            for entry in arp_table:
                ip = entry.get("ip", "")
                mac = entry.get("mac", "")
                if ip and mac:
                    ip_to_macs[ip].append(mac.upper())
            
            # Find IPs with multiple MACs (ARP spoofing indicator)
            spoofed_ips = {}
            for ip, macs in ip_to_macs.items():
                unique_macs = set(macs)
                if len(unique_macs) > 1:
                    spoofed_ips[ip] = {
                        "macs": list(unique_macs),
                        "count": len(unique_macs),
                    }
            
            if spoofed_ips:
                return {
                    "detected": True,
                    "spoofed_ips": spoofed_ips,
                    "threat_level": "critical",
                }
        
        except Exception:
            pass
        
        return None
    
    async def _check_signal_strength(self) -> Optional[Dict[str, Any]]:
        """Check WiFi signal strength"""
        try:
            networks = await self._scan_wifi_networks()
            if networks:
                # Get strongest signal
                current_network = max(networks, key=lambda x: x.get("signal", -100), default=None)
                if current_network:
                    return {
                        "ssid": current_network.get("ssid"),
                        "strength": current_network.get("signal", -100),
                        "bssid": current_network.get("bssid"),
                    }
        except Exception:
            pass
        
        return None







