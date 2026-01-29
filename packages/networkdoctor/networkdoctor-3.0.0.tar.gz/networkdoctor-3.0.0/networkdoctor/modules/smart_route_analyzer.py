"""
Smart Route Analyzer - Visual World Map Hops and Submarine Cable Detection

"""
import subprocess
import json
import socket
import ipaddress
from typing import List, Dict, Any, Optional
import asyncio


class SmartRouteAnalyzer:
    """Analyze network routes with visual map and submarine cable detection"""
    
    def __init__(self):
        self.name = "Smart Route Analyzer"
        # Known submarine cable endpoints and regions
        self.submarine_cable_regions = {
            "trans-atlantic": ["US", "UK", "FR", "DE"],
            "trans-pacific": ["US", "JP", "CN", "AU"],
            "mediterranean": ["IT", "GR", "EG", "TR"],
            "asia-pacific": ["SG", "HK", "IN", "TH"],
        }
        # GeoIP data (simplified - in production, use a real GeoIP service)
        self.ip_ranges = {}
    
    async def diagnose(self, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze network routes with geographic visualization.
        
        Args:
            scan_results: Results from network scan
            
        Returns:
            Route analysis with map data
        """
        issues = []
        findings = []
        route_data = []
        
        # Extract target IPs from scan results
        targets = self._extract_targets(scan_results)
        
        for target in targets[:5]:  # Limit to 5 targets
            route_info = await self._trace_route(target)
            if route_info:
                route_data.append(route_info)
                
                # Detect submarine cable crossings
                submarine_detected = self._detect_submarine_cables(route_info)
                
                # Detect packet failures
                failures = self._detect_failures(route_info)
                
                if failures:
                    issues.append({
                        "severity": "medium",
                        "type": "route_failure",
                        "title": f"Packet Failures Detected to {target}",
                        "description": f"Packets failing at hop(s): {', '.join(failures)}",
                        "route_info": route_info,
                    })
                
                if submarine_detected:
                    findings.append({
                        "finding": "submarine_cable_crossing",
                        "target": target,
                        "cables": submarine_detected,
                        "description": "Route crosses submarine cable infrastructure",
                    })
        
        # Generate map visualization data
        map_data = self._generate_map_data(route_data)
        
        return {
            "doctor": "smart_route",
            "status": "completed",
            "issues": issues,
            "findings": findings,
            "route_data": route_data,
            "map_visualization": map_data,
            "summary": {
                "total_routes_analyzed": len(route_data),
                "submarine_cables_detected": len(findings),
                "packet_failures": sum(1 for r in route_data if r.get("failures")),
                "total_issues": len(issues),
            },
        }
    
    def _extract_targets(self, scan_results: List[Dict[str, Any]]) -> List[str]:
        """Extract target IPs from scan results"""
        targets = []
        for result in scan_results:
            if "ip" in result:
                targets.append(result["ip"])
            elif "target" in result:
                target = result["target"]
                # Try to resolve if it's a hostname
                try:
                    ip = socket.gethostbyname(target)
                    targets.append(ip)
                except:
                    pass
        return list(set(targets))  # Remove duplicates
    
    async def _trace_route(self, target: str) -> Optional[Dict[str, Any]]:
        """Perform traceroute to target"""
        try:
            # Use system traceroute command
            process = await asyncio.create_subprocess_exec(
                "traceroute",
                "-n",  # Don't resolve hostnames (faster)
                "-m", "30",  # Max hops
                target,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                # Fallback: try tracert on Windows or use Python implementation
                return await self._trace_route_python(target)
            
            hops = self._parse_traceroute_output(stdout.decode())
            
            return {
                "target": target,
                "hops": hops,
                "total_hops": len(hops),
                "failures": [h["hop"] for h in hops if h.get("status") == "failed"],
            }
        except Exception as e:
            # Fallback to Python implementation
            return await self._trace_route_python(target)
    
    async def _trace_route_python(self, target: str) -> Optional[Dict[str, Any]]:
        """Python-based traceroute fallback"""
        hops = []
        max_hops = 30
        
        try:
            target_ip = socket.gethostbyname(target)
        except:
            target_ip = target
        
        for ttl in range(1, max_hops + 1):
            try:
                # Create UDP socket (simplified traceroute)
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(3)
                
                # Send packet
                sock.connect((target_ip, 33434 + ttl))
                
                # Try to receive ICMP reply (simplified - real traceroute is more complex)
                hop_info = {
                    "hop": ttl,
                    "ip": target_ip if ttl == max_hops else "unknown",
                    "status": "success",
                }
                
                # Try to get geo location (simplified)
                geo = self._get_ip_geo(hop_info["ip"])
                if geo:
                    hop_info.update(geo)
                
                hops.append(hop_info)
                
                if hop_info["ip"] == target_ip:
                    break
                
                sock.close()
            except Exception:
                hops.append({
                    "hop": ttl,
                    "ip": "*",
                    "status": "failed",
                })
        
        return {
            "target": target,
            "hops": hops,
            "total_hops": len(hops),
            "failures": [h["hop"] for h in hops if h.get("status") == "failed"],
        }
    
    def _parse_traceroute_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse traceroute command output"""
        hops = []
        lines = output.strip().split("\n")[1:]  # Skip first line
        
        for line in lines:
            parts = line.split()
            if len(parts) < 2:
                continue
            
            try:
                hop_num = int(parts[0])
                ip = parts[1] if parts[1] != "*" else None
                
                if ip and ip != "*":
                    geo = self._get_ip_geo(ip)
                    hop_info = {
                        "hop": hop_num,
                        "ip": ip,
                        "status": "success",
                    }
                    if geo:
                        hop_info.update(geo)
                    hops.append(hop_info)
                else:
                    hops.append({
                        "hop": hop_num,
                        "ip": "*",
                        "status": "failed",
                    })
            except (ValueError, IndexError):
                continue
        
        return hops
    
    def _get_ip_geo(self, ip: str) -> Optional[Dict[str, Any]]:
        """Get geographic location for IP (simplified - use real GeoIP service in production)"""
        # This is a placeholder - in production, use MaxMind GeoIP2 or similar
        try:
            # Simple heuristic based on IP ranges (not accurate, just for demo)
            ip_obj = ipaddress.ip_address(ip)
            
            # Example: Classify by IP ranges (very simplified)
            if ipaddress.IPv4Address("1.0.0.0") <= ip_obj <= ipaddress.IPv4Address("126.255.255.255"):
                return {"country": "US", "region": "North America"}
            elif ipaddress.IPv4Address("128.0.0.0") <= ip_obj <= ipaddress.IPv4Address("191.255.255.255"):
                return {"country": "EU", "region": "Europe"}
            elif ipaddress.IPv4Address("192.0.0.0") <= ip_obj <= ipaddress.IPv4Address("223.255.255.255"):
                return {"country": "ASIA", "region": "Asia"}
        except:
            pass
        
        return None
    
    def _detect_submarine_cables(self, route_info: Dict[str, Any]) -> List[str]:
        """Detect if route crosses submarine cables"""
        detected_cables = []
        hops = route_info.get("hops", [])
        
        # Get countries from hops
        countries = []
        for hop in hops:
            if "country" in hop:
                countries.append(hop["country"])
        
        # Check if route crosses known submarine cable regions
        for cable_type, cable_countries in self.submarine_cable_regions.items():
            if any(c in countries for c in cable_countries):
                # Check if route spans continents (indicates submarine cable)
                regions = set()
                for hop in hops:
                    if "region" in hop:
                        regions.add(hop["region"])
                
                if len(regions) > 1:  # Multiple regions = likely submarine cable
                    detected_cables.append(cable_type)
        
        return detected_cables
    
    def _detect_failures(self, route_info: Dict[str, Any]) -> List[int]:
        """Detect packet failures in route"""
        failures = []
        for hop in route_info.get("hops", []):
            if hop.get("status") == "failed" or hop.get("ip") == "*":
                failures.append(hop["hop"])
        return failures
    
    def _generate_map_data(self, route_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate data for map visualization"""
        coordinates = []
        
        for route in route_data:
            route_coords = []
            for hop in route.get("hops", []):
                if "country" in hop and hop.get("ip") != "*":
                    # In production, get actual lat/long from GeoIP
                    route_coords.append({
                        "hop": hop["hop"],
                        "ip": hop["ip"],
                        "country": hop.get("country", "Unknown"),
                        "region": hop.get("region", "Unknown"),
                    })
            if route_coords:
                coordinates.append({
                    "target": route["target"],
                    "path": route_coords,
                })
        
        return {
            "type": "world_map",
            "routes": coordinates,
            "total_routes": len(coordinates),
        }

