"""Markdown Documentation Generator for NetworkDoctor"""
from typing import Dict, Any
from pathlib import Path


class MarkdownGenerator:
    """Markdown report generation"""
    
    @staticmethod
    def generate(results: Dict[str, Any], output_file: str):
        """
        Generate Markdown report.
        
        Args:
            results: Diagnosis results
            output_file: Output file path
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        analysis = results.get("analysis", {})
        summary = analysis.get("summary", {})
        
        md = f"""# NetworkDoctor Report

## Summary

- Health Score: {summary.get('health_score', 0)}/100
- Total Issues: {summary.get('total_issues', 0)}
- Critical Issues: {summary.get('critical_count', 0)}

## Issues

"""
        
        issues = analysis.get("issues", [])
        for issue in issues:
            md += f"### {issue.get('title', '')}\n\n"
            md += f"**Severity:** {issue.get('severity', '')}\n\n"
            md += f"**Description:** {issue.get('description', '')}\n\n"
            md += f"**Impact:** {issue.get('impact', '')}\n\n"
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)







