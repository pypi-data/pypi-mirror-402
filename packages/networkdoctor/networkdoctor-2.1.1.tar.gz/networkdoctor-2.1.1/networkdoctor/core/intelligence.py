"""
AI-Powered Problem Detection for NetworkDoctor
"""
from typing import List, Dict, Any, Optional
from networkdoctor.intelligence.rule_engine import RuleEngine
from networkdoctor.intelligence.correlation_engine import CorrelationEngine
from networkdoctor.intelligence.knowledge_base import KnowledgeBase


class IntelligenceEngine:
    """AI-powered intelligence engine for problem detection"""
    
    def __init__(self):
        """Initialize intelligence engine"""
        self.rule_engine = RuleEngine()
        self.correlation_engine = CorrelationEngine()
        self.knowledge_base = KnowledgeBase()
    
    def analyze_issues(
        self,
        issues: List[Dict[str, Any]],
        scan_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze issues using AI and expert rules.
        
        Args:
            issues: List of detected issues
            scan_data: Raw scan data
            
        Returns:
            Enhanced analysis with AI insights
        """
        # Apply expert rules
        rule_results = self.rule_engine.apply_rules(issues, scan_data)
        
        # Correlate issues
        correlations = self.correlation_engine.correlate(issues)
        
        # Get knowledge base insights
        insights = self.knowledge_base.get_insights(issues, scan_data)
        
        # Predict future issues
        predictions = self._predict_issues(issues, scan_data)
        
        return {
            "rule_results": rule_results,
            "correlations": correlations,
            "insights": insights,
            "predictions": predictions,
            "confidence": self._calculate_confidence(issues, rule_results),
        }
    
    def _predict_issues(
        self,
        current_issues: List[Dict[str, Any]],
        scan_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Predict potential future issues.
        
        Args:
            current_issues: Current detected issues
            scan_data: Scan data
            
        Returns:
            List of predicted issues
        """
        predictions = []
        
        # Simple pattern-based prediction
        # If SSL cert expires soon, predict certificate renewal issue
        for issue in current_issues:
            if issue.get("type") == "ssl" and "expires" in issue.get("title", "").lower():
                predictions.append({
                    "type": "ssl_certificate_expiry",
                    "description": "SSL certificate will expire soon, renewal needed",
                    "estimated_time": "15 days",
                    "confidence": "high",
                })
        
        # If high latency detected, predict performance degradation
        perf_issues = [i for i in current_issues if i.get("type") == "performance"]
        if perf_issues:
            predictions.append({
                "type": "performance_degradation",
                "description": "Performance issues may worsen without intervention",
                "estimated_time": "7 days",
                "confidence": "medium",
            })
        
        return predictions
    
    def _calculate_confidence(
        self,
        issues: List[Dict[str, Any]],
        rule_results: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence score for analysis.
        
        Args:
            issues: Detected issues
            rule_results: Results from rule engine
            
        Returns:
            Confidence score (0-1)
        """
        if not issues:
            return 1.0
        
        # Base confidence on number of matching rules
        matched_rules = rule_results.get("matched_rules", 0)
        total_rules = rule_results.get("total_rules", 1)
        
        rule_confidence = matched_rules / total_rules if total_rules > 0 else 0.5
        
        # Adjust based on issue count (more issues = lower confidence)
        issue_factor = min(1.0, 10.0 / max(len(issues), 1))
        
        return (rule_confidence + issue_factor) / 2







