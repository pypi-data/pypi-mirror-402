"""
JSON Export for NetworkDoctor
"""
import json
from typing import Dict, Any
from pathlib import Path


class JSONExporter:
    """JSON export functionality"""
    
    @staticmethod
    def export(results: Dict[str, Any], output_file: str = None):
        """
        Export results to JSON file.
        Automatically creates outputs/json/ folder if not specified.
        
        Args:
            results: Diagnosis results
            output_file: Output file path (optional, defaults to outputs/json/report_TIMESTAMP.json)
        """
        if output_file is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"outputs/json/report_{timestamp}.json"
        
        output_path = Path(output_file)
        # Always use outputs/json/ structure
        if not output_path.parts[0] == "outputs" or "json" not in str(output_path):
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = output_path.name if output_path.name.endswith('.json') else f"report_{timestamp}.json"
            output_path = Path(f"outputs/json/{filename}")
            output_file = str(output_path)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)







