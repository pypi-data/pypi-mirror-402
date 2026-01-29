"""
Security Vulnerability Expert for NetworkDoctor
"""
from typing import List, Dict, Any
from datetime import datetime


class SecurityInspector:
    """Security vulnerability inspection expert"""
    
    async def diagnose(self, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Diagnose security issues.
        
        Args:
            scan_results: Results from network scanner
            
        Returns:
            Diagnosis results
        """
        issues = []
        findings = []
        
        for result in scan_results:
            target = result.get("target", "")
            http_result = result.get("http", {})
            
            if http_result.get("success"):
                headers = http_result.get("headers", {})
                
                findings.append({
                    "target": target,
                    "status_code": http_result.get("status_code"),
                    "headers_analyzed": len(headers),
                })
                
                # Check security headers
                security_headers = {
                    "Strict-Transport-Security": "HSTS",
                    "X-Frame-Options": "Clickjacking protection",
                    "Content-Security-Policy": "CSP",
                    "X-Content-Type-Options": "MIME sniffing protection",
                }
                
                missing_headers = []
                for header, description in security_headers.items():
                    if header not in headers:
                        missing_headers.append(header)
                
                # Only report missing headers if critical ones are missing
                critical_headers = ["Strict-Transport-Security"]
                missing_critical = [h for h in missing_headers if h in critical_headers]
                
                if missing_critical:
                    issues.append({
                        "id": f"sec_missing_headers_{target}",
                        "type": "security",
                        "severity": "medium",
                        "title": "Missing Critical Security Headers",
                        "description": f"Missing critical security headers: {', '.join(missing_critical)} for {target}",
                        "impact": "Reduced protection against common web vulnerabilities",
                        "solutions": [
                            {
                                "action": "Add security headers",
                                "command": f"Configure web server for {target} to include security headers",
                            },
                        ],
                    })
                elif len(missing_headers) >= 3:  # Only report if many headers are missing
                    issues.append({
                        "id": f"sec_missing_headers_{target}",
                        "type": "security",
                        "severity": "low",
                        "title": "Some Security Headers Missing",
                        "description": f"Missing security headers: {', '.join(missing_headers[:3])} for {target}",
                        "impact": "Could improve protection against web vulnerabilities",
                        "solutions": [
                            {
                                "action": "Add security headers",
                                "command": f"Configure web server for {target} to include security headers",
                            },
                        ],
                    })
                
                # Check for exposed server information
                server_header = headers.get("Server", "")
                x_powered_by = headers.get("X-Powered-By", "")
                
                if server_header or x_powered_by:
                    issues.append({
                        "id": f"sec_exposed_info_{target}",
                        "type": "security",
                        "severity": "low",
                        "title": "Server Information Exposed",
                        "description": f"Server information exposed in headers for {target}: {server_header or x_powered_by}",
                        "impact": "Information disclosure may aid attackers",
                        "solutions": [
                            {
                                "action": "Hide server information",
                                "command": f"Configure server for {target} to hide version information",
                            },
                        ],
                    })
        
        return {
            "doctor": "security",
            "status": "completed",
            "issues": issues,
            "findings": findings,
            "summary": {
                "total_issues": len(issues),
                "targets_checked": len(findings),
            },
        }

