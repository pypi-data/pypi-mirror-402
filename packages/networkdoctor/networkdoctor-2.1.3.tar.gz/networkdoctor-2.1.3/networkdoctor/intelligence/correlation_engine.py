"""
Cross-Issue Correlation Engine for NetworkDoctor
"""
from typing import List, Dict, Any


class CorrelationEngine:
    """Correlates related issues to find root causes"""
    
    def correlate(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Correlate issues to find relationships.
        
        Args:
            issues: List of issues
            
        Returns:
            List of correlations
        """
        correlations = []
        
        # Group issues by type
        issues_by_type = {}
        for issue in issues:
            issue_type = issue.get("type", "unknown")
            if issue_type not in issues_by_type:
                issues_by_type[issue_type] = []
            issues_by_type[issue_type].append(issue)
        
        # Find correlations
        # DNS + SSL = likely firewall
        if "dns" in issues_by_type and "ssl" in issues_by_type:
            correlations.append({
                "type": "firewall_correlation",
                "description": "DNS and SSL issues often indicate firewall blocking",
                "related_issues": [
                    i.get("id") for i in issues_by_type["dns"] + issues_by_type["ssl"]
                ],
                "confidence": 0.8,
            })
        
        # Multiple performance issues = network congestion
        if "performance" in issues_by_type and len(issues_by_type["performance"]) >= 2:
            correlations.append({
                "type": "congestion_correlation",
                "description": "Multiple performance issues suggest network congestion",
                "related_issues": [i.get("id") for i in issues_by_type["performance"]],
                "confidence": 0.7,
            })
        
        return correlations








