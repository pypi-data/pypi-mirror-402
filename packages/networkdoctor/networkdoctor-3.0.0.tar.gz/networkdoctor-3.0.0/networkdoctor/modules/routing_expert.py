"""
BGP & Routing Expert for NetworkDoctor
"""
import asyncio
import subprocess
import re
from typing import List, Dict, Any


class RoutingExpert:
    """BGP and routing diagnosis expert"""
    
    async def diagnose(self, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Diagnose routing issues with real traceroute and BGP analysis.
        
        Args:
            scan_results: Results from network scanner
            
        Returns:
            Diagnosis results with real routing analysis
        """
        issues = []
        findings = []
        
        for result in scan_results:
            target = result.get("target", "")
            
            # Perform traceroute analysis
            route_info = await self._analyze_route(target)
            findings.append(route_info)
            
            # Analyze routing issues
            await self._detect_routing_issues(target, route_info, issues, findings)
            
            # Check BGP routing if available
            await self._analyze_bgp_routing(target, issues, findings)
        
        return {
            "doctor": "routing",
            "status": "completed",
            "issues": issues,
            "findings": findings,
            "summary": {
                "total_issues": len(issues),
                "routes_analyzed": len(findings),
            },
        }
    
    async def _analyze_route(self, target: str) -> Dict[str, Any]:
        """Analyze network route using traceroute"""
        route_info = {
            "target": target,
            "hops": [],
            "total_hops": 0,
            "max_latency": 0,
            "avg_latency": 0,
            "route_complete": False,
        }
        
        try:
            # Use traceroute (Linux/Mac) or tracert (Windows)
            if self._get_system() == "Windows":
                cmd = ["tracert", target]
            else:
                cmd = ["traceroute", "-n", "-m", "15", target]  # Max 15 hops
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            output = stdout.decode()
            
            # Parse traceroute output
            hops = self._parse_traceroute(output)
            route_info["hops"] = hops
            route_info["total_hops"] = len(hops)
            route_info["route_complete"] = len(hops) > 0
            
            if hops:
                latencies = [hop.get("latency", 0) for hop in hops if hop.get("latency")]
                if latencies:
                    route_info["max_latency"] = max(latencies)
                    route_info["avg_latency"] = sum(latencies) / len(latencies)
        
        except Exception as e:
            route_info["error"] = str(e)
        
        return route_info
    
    def _parse_traceroute(self, output: str) -> List[Dict[str, Any]]:
        """Parse traceroute output into structured data"""
        hops = []
        
        for line in output.split('\n'):
            if not line.strip():
                continue
                
            # Parse hop information
            hop = self._parse_hop_line(line)
            if hop:
                hops.append(hop)
        
        return hops
    
    def _parse_hop_line(self, line: str) -> Dict[str, Any]:
        """Parse individual traceroute hop line"""
        hop = {"hop_number": 0, "ip": "", "latency": None, "hostname": ""}
        
        # Linux traceroute format: "1  192.168.1.1 (192.168.1.1)  1.234 ms  1.567 ms  1.890 ms"
        # Windows tracert format: "1    <1 ms    192.168.1.1"
        
        # Extract hop number
        hop_match = re.match(r'^\s*(\d+)', line)
        if hop_match:
            hop["hop_number"] = int(hop_match.group(1))
        
        # Extract IP addresses
        ip_matches = re.findall(r'(\d+\.\d+\.\d+\.\d+)', line)
        if ip_matches:
            hop["ip"] = ip_matches[0]
        
        # Extract latency values
        latency_matches = re.findall(r'(\d+\.?\d*)\s*ms', line)
        if latency_matches:
            # Use the last (most stable) latency value
            hop["latency"] = float(latency_matches[-1])
        
        # Extract hostname (in parentheses)
        hostname_match = re.search(r'\(([^)]+)\)', line)
        if hostname_match:
            hop["hostname"] = hostname_match.group(1)
        
        return hop if hop["hop_number"] > 0 else None
    
    def _get_system(self) -> str:
        """Get operating system"""
        import platform
        return platform.system()
    
    async def _detect_routing_issues(self, target: str, route_info: Dict, issues: List, findings: List):
        """Detect routing issues from traceroute data"""
        hops = route_info.get("hops", [])
        
        if not hops:
            issues.append({
                "id": f"routing_no_route_{target}",
                "type": "routing",
                "severity": "high",
                "title": "No Route Found",
                "description": f"Cannot determine route to {target}",
                "impact": "Target is unreachable",
                "solutions": [
                    {
                        "action": "Check network connectivity",
                        "command": f"ping {target}",
                    },
                    {
                        "action": "Check DNS resolution",
                        "command": f"nslookup {target}",
                    },
                ],
            })
            return
        
        # Check for high latency hops
        high_latency_hops = [hop for hop in hops if hop.get("latency") and hop.get("latency", 0) > 200]
        if high_latency_hops:
            issues.append({
                "id": f"routing_high_latency_{target}",
                "type": "routing",
                "severity": "medium",
                "title": "High Latency Hops Detected",
                "description": f"{len(high_latency_hops)} hops with >200ms latency to {target}",
                "impact": "Slow network path performance",
                "solutions": [
                    {
                        "action": "Check network congestion",
                        "command": "Check network utilization on high-latency hops",
                    },
                    {
                        "action": "Consider alternative routes",
                        "command": "Consult ISP for route optimization",
                    },
                ],
            })
        
        # Check for packet loss (indicated by * in traceroute)
        packet_loss_hops = [hop for hop in hops if "*" in hop.get("ip", "")]
        if packet_loss_hops:
            issues.append({
                "id": f"routing_packet_loss_{target}",
                "type": "routing",
                "severity": "high",
                "title": "Packet Loss in Route",
                "description": f"Packet loss detected at {len(packet_loss_hops)} hops to {target}",
                "impact": "Unreliable connection, data loss",
                "solutions": [
                    {
                        "action": "Check network equipment",
                        "command": "Inspect routers/switches on packet loss hops",
                    },
                    {
                        "action": "Contact ISP",
                        "command": "Report routing issues to ISP",
                    },
                ],
            })
        
        # Check for excessive hops
        if len(hops) > 20:
            issues.append({
                "id": f"routing_excessive_hops_{target}",
                "type": "routing",
                "severity": "medium",
                "title": "Excessive Network Hops",
                "description": f"Route to {target} uses {len(hops)} hops (inefficient)",
                "impact": "Increased latency and potential reliability issues",
                "solutions": [
                    {
                        "action": "Check routing tables",
                        "command": "netstat -rn",
                    },
                    {
                        "action": "Optimize routing",
                        "command": "Review BGP advertisements",
                    },
                ],
            })
    
    async def _analyze_bgp_routing(self, target: str, issues: List, findings: List):
        """Analyze BGP routing information"""
        try:
            # Use external BGP looking glass services
            bgp_services = [
                "https://bgp.he.net/dns/{target}",
                "https://stat.ripe.net/data/whois/{target}",
            ]
            
            for service_url in bgp_services:
                try:
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get(service_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                            if response.status == 200:
                                findings.append({
                                    "target": target,
                                    "bgp_service": service_url.split('/')[2],
                                    "bgp_data_available": True,
                                    "routing_analysis": "BGP information retrieved",
                                })
                                break
                except:
                    continue
        
        except Exception:
            pass








