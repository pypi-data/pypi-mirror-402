"""
JSON Export for NetworkDoctor
"""
import json
from typing import Dict, Any
from pathlib import Path


class JSONExporter:
    """JSON export functionality"""
    
    @staticmethod
    def export(results: Dict[str, Any], output_file: str):
        """
        Export results to JSON file.
        
        Args:
            results: Diagnosis results
            output_file: Output file path
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)







