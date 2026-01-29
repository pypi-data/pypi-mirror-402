"""
DNS Infrastructure Expert for NetworkDoctor
"""
import asyncio
from typing import List, Dict, Any
from networkdoctor.utils.network_tools import resolve_dns
from networkdoctor.utils.parsers import parse_domain


class DNSDoctor:
    """DNS infrastructure diagnosis expert"""
    
    async def diagnose(self, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Diagnose DNS issues.
        
        Args:
            scan_results: Results from network scanner
            
        Returns:
            Diagnosis results
        """
        issues = []
        findings = []
        
        for result in scan_results:
            target = result.get("target", "")
            
            # Check DNS resolution
            dns_result = result.get("dns")
            if dns_result is None:
                # Try to resolve
                dns_result = await resolve_dns(target)
            
            if not dns_result:
                issues.append({
                    "id": f"dns_no_resolution_{target}",
                    "type": "dns",
                    "severity": "high",
                    "title": "DNS Resolution Failed",
                    "description": f"Unable to resolve DNS for {target}",
                    "impact": "Service is unreachable via domain name",
                    "solutions": [
                        {
                            "action": "Check DNS server configuration",
                            "command": "nslookup " + target,
                        },
                        {
                            "action": "Verify DNS records",
                            "command": "dig " + target,
                        },
                    ],
                })
            else:
                findings.append({
                    "target": target,
                    "resolved": dns_result,
                    "status": "ok",
                })
                
                # Check for multiple IPs (load balancing)
                if len(dns_result) > 1:
                    findings[-1]["load_balanced"] = True
        
        # Check DNSSEC (simplified) - only for domains that actually resolve
        for finding in findings:
            target = finding.get("target", "")
            if not target:
                continue
                
            domain_info = parse_domain(target)
            
            # Try to check DNSSEC - but don't fail if it's not available
            # Many legitimate sites don't have DNSSEC, so make this less strict
            try:
                dnssec_result = await resolve_dns(target, "DNSKEY")
                finding["dnssec"] = bool(dnssec_result)
                # Only report as issue if DNS resolution works but DNSSEC check fails explicitly
                # Don't report if it's just not configured (which is common)
                if not finding.get("dnssec"):
                    # Check if this is a major domain that should have DNSSEC
                    major_domains = ["google.com", "github.com", "cloudflare.com"]
                    if any(major in target.lower() for major in major_domains):
                        issues.append({
                            "id": f"dns_no_dnssec_{target}",
                            "type": "dns",
                            "severity": "low",  # Changed from medium to low
                            "title": "DNSSEC Not Enabled",
                            "description": f"DNSSEC is not enabled for {target} (optional but recommended)",
                            "impact": "DNS responses are not cryptographically signed (low priority)",
                            "solutions": [
                                {
                                    "action": "Enable DNSSEC on DNS provider (optional)",
                                    "command": "Contact DNS provider to enable DNSSEC",
                                },
                            ],
                        })
            except Exception:
                finding["dnssec"] = False
                # Don't create issue if DNSSEC check fails - it's optional
        
        return {
            "doctor": "dns",
            "status": "completed",
            "issues": issues,
            "findings": findings,
            "summary": {
                "total_issues": len(issues),
                "resolved_domains": len([f for f in findings if f.get("status") == "ok"]),
            },
        }

