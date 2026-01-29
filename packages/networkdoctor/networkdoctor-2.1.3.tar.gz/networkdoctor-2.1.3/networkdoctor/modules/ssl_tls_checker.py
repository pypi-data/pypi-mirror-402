"""
SSL/TLS Certificate Expert for NetworkDoctor
"""
from typing import List, Dict, Any
from datetime import datetime
from networkdoctor.utils.parsers import parse_ssl_certificate


class SSLChecker:
    """SSL/TLS certificate checking expert"""
    
    async def diagnose(self, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Diagnose SSL/TLS certificate issues.
        
        Args:
            scan_results: Results from network scanner
            
        Returns:
            Diagnosis results
        """
        issues = []
        findings = []
        
        for result in scan_results:
            target = result.get("target", "")
            ssl_result = result.get("ssl", {})
            
            if ssl_result:
                if not ssl_result.get("valid"):
                    issues.append({
                        "id": f"ssl_invalid_{target}",
                        "type": "ssl",
                        "severity": "critical",
                        "title": "Invalid SSL Certificate",
                        "description": f"SSL certificate for {target} is invalid",
                        "impact": "Secure connections cannot be established",
                        "solutions": [
                            {
                                "action": "Check certificate validity",
                                "command": f"openssl s_client -connect {target}:443",
                            },
                            {
                                "action": "Renew certificate",
                                "command": "certbot renew --force-renewal",
                            },
                        ],
                    })
                else:
                    # Parse certificate info
                    cert_info = parse_ssl_certificate(ssl_result)
                    findings.append(cert_info)
                    
                    # Check expiration
                    days_until_expiry = cert_info.get("days_until_expiry", 0)
                    
                    if days_until_expiry < 0:
                        issues.append({
                            "id": f"ssl_expired_{target}",
                            "type": "ssl",
                            "severity": "critical",
                            "title": "SSL Certificate Expired",
                            "description": f"SSL certificate for {target} has expired",
                            "impact": "Secure connections will fail",
                            "solutions": [
                                {
                                    "action": "Renew certificate immediately",
                                    "command": "certbot renew --force-renewal",
                                },
                            ],
                        })
                    elif days_until_expiry < 30:
                        issues.append({
                            "id": f"ssl_expiring_soon_{target}",
                            "type": "ssl",
                            "severity": "high",
                            "title": "SSL Certificate Expiring Soon",
                            "description": f"SSL certificate for {target} expires in {days_until_expiry} days",
                            "impact": "Certificate will expire soon, causing service disruption",
                            "solutions": [
                                {
                                    "action": "Renew certificate",
                                    "command": "certbot renew --force-renewal",
                                },
                                {
                                    "action": "Set up auto-renewal",
                                    "command": "certbot renew --dry-run",
                                },
                            ],
                        })
            else:
                # No SSL result - might not be HTTPS
                if result.get("port") == 443:
                    issues.append({
                        "id": f"ssl_no_cert_{target}",
                        "type": "ssl",
                        "severity": "high",
                        "title": "No SSL Certificate Found",
                        "description": f"No SSL certificate found for {target}:443",
                        "impact": "HTTPS connections cannot be established",
                        "solutions": [
                            {
                                "action": "Install SSL certificate",
                                "command": "certbot --nginx -d " + target,
                            },
                        ],
                    })
        
        return {
            "doctor": "ssl",
            "status": "completed",
            "issues": issues,
            "findings": findings,
            "summary": {
                "total_issues": len(issues),
                "certificates_checked": len(findings),
            },
        }








