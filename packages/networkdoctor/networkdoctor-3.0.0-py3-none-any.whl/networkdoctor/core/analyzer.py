"""
Data Analysis & Correlation for NetworkDoctor
"""
from typing import List, Dict, Any, Optional
from networkdoctor.utils.helpers import calculate_health_score, estimate_fix_time


class NetworkAnalyzer:
    """Analyzes network scan results and correlates issues"""
    
    def __init__(self):
        """Initialize network analyzer"""
        pass
    
    def analyze_results(
        self,
        scan_results: List[Dict[str, Any]],
        doctor_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze scan and doctor results.
        
        Args:
            scan_results: Results from network scanner
            doctor_results: Results from doctor modules
            
        Returns:
            Analysis summary
        """
        # Collect all issues
        all_issues = []
        for result in doctor_results:
            issues = result.get("issues", [])
            all_issues.extend(issues)
        
        # Categorize issues
        issues_by_severity = self._categorize_by_severity(all_issues)
        issues_by_type = self._categorize_by_type(all_issues)
        
        # Calculate metrics
        health_score = calculate_health_score(all_issues)
        fix_time = estimate_fix_time(all_issues)
        
        # Find root causes
        root_causes = self._find_root_causes(all_issues)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(all_issues)
        
        return {
            "summary": {
                "total_issues": len(all_issues),
                "health_score": health_score,
                "estimated_fix_time": fix_time,
                "critical_count": len(issues_by_severity.get("critical", [])),
                "high_count": len(issues_by_severity.get("high", [])),
                "medium_count": len(issues_by_severity.get("medium", [])),
                "low_count": len(issues_by_severity.get("low", [])),
            },
            "issues": all_issues,
            "issues_by_severity": issues_by_severity,
            "issues_by_type": issues_by_type,
            "root_causes": root_causes,
            "recommendations": recommendations,
            "scan_results": scan_results,
        }
    
    def _categorize_by_severity(
        self,
        issues: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize issues by severity.
        
        Args:
            issues: List of issues
            
        Returns:
            Dictionary of issues grouped by severity
        """
        categorized = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "info": [],
        }
        
        for issue in issues:
            severity = issue.get("severity", "info").lower()
            if severity in categorized:
                categorized[severity].append(issue)
            else:
                categorized["info"].append(issue)
        
        return categorized
    
    def _categorize_by_type(
        self,
        issues: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize issues by type.
        
        Args:
            issues: List of issues
            
        Returns:
            Dictionary of issues grouped by type
        """
        categorized = {}
        
        for issue in issues:
            issue_type = issue.get("type", "unknown")
            if issue_type not in categorized:
                categorized[issue_type] = []
            categorized[issue_type].append(issue)
        
        return categorized
    
    def _find_root_causes(
        self,
        issues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Find root causes by correlating issues.
        
        Args:
            issues: List of issues
            
        Returns:
            List of root causes
        """
        root_causes = []
        
        # Look for common patterns
        # DNS + SSL issues might indicate firewall
        dns_issues = [i for i in issues if i.get("type") == "dns"]
        ssl_issues = [i for i in issues if i.get("type") == "ssl"]
        
        if dns_issues and ssl_issues:
            root_causes.append({
                "type": "firewall",
                "description": "DNS and SSL issues detected, likely firewall blocking",
                "confidence": "high",
                "related_issues": [i.get("id") for i in dns_issues + ssl_issues],
            })
        
        # Performance issues might indicate network congestion
        perf_issues = [i for i in issues if i.get("type") == "performance"]
        if len(perf_issues) >= 3:
            root_causes.append({
                "type": "congestion",
                "description": "Multiple performance issues indicate network congestion",
                "confidence": "medium",
                "related_issues": [i.get("id") for i in perf_issues],
            })
        
        return root_causes
    
    def _generate_recommendations(
        self,
        issues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate actionable recommendations.
        
        Args:
            issues: List of issues
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Prioritize by severity
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        high_issues = [i for i in issues if i.get("severity") == "high"]
        
        for issue in critical_issues + high_issues:
            solutions = issue.get("solutions", [])
            if solutions:
                recommendations.append({
                    "priority": "immediate" if issue.get("severity") == "critical" else "urgent",
                    "issue": issue.get("title", ""),
                    "solutions": solutions,
                })
        
        return recommendations








