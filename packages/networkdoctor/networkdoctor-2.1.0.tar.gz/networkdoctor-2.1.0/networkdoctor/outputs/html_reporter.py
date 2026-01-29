"""
HTML Report Generator for NetworkDoctor
"""
from typing import Dict, Any
from pathlib import Path


class HTMLReporter:
    """HTML report generation"""
    
    @staticmethod
    def generate(results: Dict[str, Any], output_file: str):
        """
        Generate HTML report.
        
        Args:
            results: Diagnosis results
            output_file: Output file path
        """
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>NetworkDoctor Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; }}
        .summary {{ background: #ecf0f1; padding: 15px; margin: 20px 0; }}
        .issue {{ border-left: 4px solid #e74c3c; padding: 10px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🩺 NetworkDoctor Report</h1>
    </div>
    <div class="summary">
        <h2>Summary</h2>
        <p>Health Score: {results.get('analysis', {}).get('summary', {}).get('health_score', 0)}/100</p>
    </div>
</body>
</html>
        """
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)







