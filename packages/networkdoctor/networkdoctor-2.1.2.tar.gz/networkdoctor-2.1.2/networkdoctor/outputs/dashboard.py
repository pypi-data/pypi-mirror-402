"""Real-time Dashboard for NetworkDoctor"""
from typing import Dict, Any


class Dashboard:
    """Real-time monitoring dashboard"""
    
    def __init__(self):
        """Initialize dashboard"""
        pass
    
    def show(self, results: Dict[str, Any]):
        """
        Display dashboard.
        
        Args:
            results: Diagnosis results
        """
        # Simplified dashboard
        print("NetworkDoctor Dashboard")
        print("=" * 50)
        print(f"Health Score: {results.get('analysis', {}).get('summary', {}).get('health_score', 0)}/100")







