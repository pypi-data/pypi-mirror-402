"""
Firewall & Security Expert for NetworkDoctor
"""
from typing import List, Dict, Any
from networkdoctor.utils.network_tools import check_connectivity


class FirewallDetector:
    """Firewall and security policy detection expert"""
    
    async def diagnose(self, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Diagnose firewall and security issues.
        
        Args:
            scan_results: Results from network scanner
            
        Returns:
            Diagnosis results
        """
        issues = []
        findings = []
        
        for result in scan_results:
            target = result.get("target", "")
            port = result.get("port", 80)
            connectivity = result.get("connectivity", False)
            
            if not connectivity:
                # Check if it's likely a firewall block
                http_result = result.get("http", {})
                if not http_result.get("success"):
                    issues.append({
                        "id": f"firewall_blocked_{target}_{port}",
                        "type": "firewall",
                        "severity": "high",
                        "title": "Port Blocked by Firewall",
                        "description": f"Port {port} on {target} appears to be blocked",
                        "impact": "Service is unreachable, may be blocked by firewall or security policy",
                        "solutions": [
                            {
                                "action": "Check firewall rules",
                                "command": f"Check firewall configuration for {target}:{port}",
                            },
                            {
                                "action": "Verify service is running",
                                "command": f"Check if service is listening on port {port}",
                            },
                            {
                                "action": "Configure proxy if corporate firewall",
                                "command": "export https_proxy=http://proxy.company.com:8080",
                            },
                        ],
                    })
            
            findings.append({
                "target": target,
                "port": port,
                "accessible": connectivity,
                "likely_firewall": not connectivity,
            })
        
        return {
            "doctor": "firewall",
            "status": "completed",
            "issues": issues,
            "findings": findings,
            "summary": {
                "total_issues": len(issues),
                "blocked_ports": len([f for f in findings if not f.get("accessible")]),
            },
        }








