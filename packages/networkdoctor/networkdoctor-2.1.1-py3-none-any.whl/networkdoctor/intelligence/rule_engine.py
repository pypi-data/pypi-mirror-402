"""
Expert Rule System for NetworkDoctor
"""
from typing import List, Dict, Any


class RuleEngine:
    """Expert rule-based system for network troubleshooting"""
    
    def __init__(self):
        """Initialize rule engine"""
        self.rules = self._load_rules()
    
    def _load_rules(self) -> List[Dict[str, Any]]:
        """Load expert rules"""
        return [
            {
                "id": "rule_001",
                "name": "DNS + SSL Failure = Firewall",
                "condition": lambda issues, data: (
                    any(i.get("type") == "dns" for i in issues) and
                    any(i.get("type") == "ssl" for i in issues)
                ),
                "action": "firewall_block",
                "confidence": 0.8,
            },
            {
                "id": "rule_002",
                "name": "High Latency + Packet Loss = Congestion",
                "condition": lambda issues, data: (
                    any("latency" in i.get("title", "").lower() for i in issues) and
                    any("packet" in i.get("title", "").lower() for i in issues)
                ),
                "action": "network_congestion",
                "confidence": 0.7,
            },
            # Add more rules as needed
        ]
    
    def apply_rules(
        self,
        issues: List[Dict[str, Any]],
        scan_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply expert rules to issues.
        
        Args:
            issues: List of issues
            scan_data: Scan data
            
        Returns:
            Rule application results
        """
        matched_rules = []
        
        for rule in self.rules:
            try:
                if rule["condition"](issues, scan_data):
                    matched_rules.append({
                        "rule_id": rule["id"],
                        "rule_name": rule["name"],
                        "action": rule["action"],
                        "confidence": rule["confidence"],
                    })
            except Exception:
                continue
        
        return {
            "matched_rules": len(matched_rules),
            "total_rules": len(self.rules),
            "rules": matched_rules,
        }







