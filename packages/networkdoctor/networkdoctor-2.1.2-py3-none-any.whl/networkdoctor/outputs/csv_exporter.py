"""CSV Export for NetworkDoctor"""
import csv
from typing import Dict, Any, List
from pathlib import Path


class CSVExporter:
    """CSV export functionality"""
    
    @staticmethod
    def export(results: Dict[str, Any], output_file: str):
        """
        Export results to CSV.
        
        Args:
            results: Diagnosis results
            output_file: Output file path
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        issues = results.get("analysis", {}).get("issues", [])
        
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Severity", "Type", "Title", "Description", "Impact"])
            
            for issue in issues:
                writer.writerow([
                    issue.get("severity", ""),
                    issue.get("type", ""),
                    issue.get("title", ""),
                    issue.get("description", ""),
                    issue.get("impact", ""),
                ])







