"""
Beautiful terminal output display for NetworkDoctor.
This makes the CLI look professional and easy to read.
"""
from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich import box


class TerminalDisplay:
    """Display diagnosis results in a beautiful terminal format."""
    
    def __init__(self):
        self.console = Console()
    
    def show_results(self, results: Dict[str, Any], verbose: bool = False):
        """Show the diagnosis results in an attractive format."""
        # Print a nice header
        self._print_header(results)
        
        # Show the executive summary
        self._print_summary(results)
        
        # Show detected issues
        self._print_issues(results, verbose)
        
        # Show action plan
        self._print_action_plan(results)
        
        # Show doctor results if verbose
        if verbose:
            self._print_detailed_results(results)
    
    def _print_header(self, results: Dict[str, Any]):
        """Print the main header banner."""
        targets = results.get("targets", ["Unknown"])
        target_str = ", ".join(targets[:3])
        if len(targets) > 3:
            target_str += f" (+{len(targets) - 3} more)"
        
        header_text = f"""🩺 NetworkDoctor - AI-Powered Network Diagnostic Tool
Created by: frankvena25
Scanning: {target_str}"""
        
        self.console.print()
        self.console.print(Panel.fit(
            header_text,
            style="bold cyan",
            border_style="cyan"
        ))
        self.console.print()
    
    def _print_summary(self, results: Dict[str, Any]):
        """Print the executive summary with health score."""
        analysis = results.get("analysis", {})
        summary = analysis.get("summary", {})
        
        health_score = summary.get("health_score", 0)
        
        # Determine color based on score
        if health_score >= 80:
            score_style = "bold green"
            status = "Excellent"
        elif health_score >= 60:
            score_style = "bold yellow"
            status = "Good"
        elif health_score >= 40:
            score_style = "bold orange1"
            status = "Fair"
        else:
            score_style = "bold red"
            status = "Poor"
        
        # Build summary text
        summary_table = Table.grid(padding=(0, 2))
        summary_table.add_column(style="bold")
        summary_table.add_column()
        
        summary_table.add_row("📊 Health Score:", f"[{score_style}]{health_score}/100[/{score_style}] ({status})")
        summary_table.add_row("🔴 Critical Issues:", str(summary.get("critical_count", 0)))
        summary_table.add_row("⚠️  Total Issues:", str(summary.get("total_issues", 0)))
        summary_table.add_row("⏱️  Estimated Fix Time:", summary.get("estimated_fix_time", "N/A"))
        summary_table.add_row("👨‍⚕️  Doctors Run:", str(summary.get("doctors_run", 0)))
        
        self.console.print(Panel(
            summary_table,
            title="Executive Summary",
            border_style="blue"
        ))
        self.console.print()
    
    def _print_issues(self, results: Dict[str, Any], verbose: bool):
        """Print all detected issues in a table."""
        analysis = results.get("analysis", {})
        all_issues = analysis.get("issues", [])
        
        # Collect issues from all doctors
        for doctor_result in results.get("doctor_results", []):
            issues = doctor_result.get("issues", [])
            for issue in issues:
                if issue not in all_issues:
                    all_issues.append(issue)
        
        if not all_issues:
            self.console.print("[bold green]✅ No issues detected! Network is healthy.[/bold green]")
            self.console.print()
            return
        
        # Group issues by severity
        issues_by_severity = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
        }
        
        for issue in all_issues:
            severity = issue.get("severity", "medium").lower()
            if severity in issues_by_severity:
                issues_by_severity[severity].append(issue)
        
        # Print critical and high issues first
        for severity in ["critical", "high"]:
            severity_issues = issues_by_severity[severity]
            if severity_issues:
                self._print_issues_table(severity_issues, severity.upper())
        
        # Print medium and low if verbose
        if verbose:
            for severity in ["medium", "low"]:
                severity_issues = issues_by_severity[severity]
                if severity_issues:
                    self._print_issues_table(severity_issues, severity.upper())
    
    def _print_issues_table(self, issues: List[Dict[str, Any]], severity_label: str):
        """Print a table of issues for a specific severity level."""
        severity_colors = {
            "CRITICAL": "bold red",
            "HIGH": "bold orange1",
            "MEDIUM": "bold yellow",
            "LOW": "bold blue",
        }
        
        color = severity_colors.get(severity_label, "white")
        
        table = Table(
            title=f"[{color}]{severity_label} Issues[/{color}]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold white"
        )
        
        table.add_column("Type", style="cyan", width=20)
        table.add_column("Title", style="white", width=40)
        table.add_column("Description", style="dim", width=50)
        
        for issue in issues[:20]:  # Limit to 20 issues per severity
            issue_type = issue.get("type", "unknown")
            title = issue.get("title", "No title")
            description = issue.get("description", "")[:47] + "..." if len(issue.get("description", "")) > 50 else issue.get("description", "")
            
            table.add_row(issue_type, title, description)
        
        self.console.print(table)
        self.console.print()
    
    def _print_action_plan(self, results: Dict[str, Any]):
        """Print the action plan with recommendations."""
        analysis = results.get("analysis", {})
        recommendations = analysis.get("recommendations", [])
        
        # Collect recommendations from issues
        if not recommendations:
            all_issues = analysis.get("issues", [])
            for doctor_result in results.get("doctor_results", []):
                for issue in doctor_result.get("issues", []):
                    if issue not in all_issues:
                        all_issues.append(issue)
            
            recommendations = []
            for issue in all_issues:
                recs = issue.get("recommendations", [])
                if recs:
                    recommendations.append({
                        "priority": issue.get("severity", "medium"),
                        "issue": issue.get("title", ""),
                        "solutions": recs,
                    })
        
        if not recommendations:
            return
        
        # Sort by priority
        priority_order = {"critical": 1, "high": 2, "medium": 3, "low": 4}
        recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "medium").lower(), 99))
        
        self.console.print("[bold cyan]🛠️  Action Plan[/bold cyan]")
        self.console.print()
        
        priority_labels = {
            "critical": "[bold red]IMMEDIATE:[/bold red]",
            "high": "[bold orange1]URGENT:[/bold orange1]",
            "medium": "[bold yellow]RECOMMENDED:[/bold yellow]",
            "low": "[bold blue]OPTIONAL:[/bold blue]",
        }
        
        for rec in recommendations[:10]:  # Show top 10
            priority = rec.get("priority", "medium").lower()
            label = priority_labels.get(priority, "[dim]ACTION:[/dim]")
            
            self.console.print(f"{label} {rec.get('issue', 'No title')}")
            
            solutions = rec.get("solutions", [])
            if solutions and isinstance(solutions[0], dict):
                cmd = solutions[0].get("command", "")
                if cmd:
                    self.console.print(f"  [dim]Command:[/dim] [cyan]{cmd}[/cyan]")
            elif solutions and isinstance(solutions[0], str):
                self.console.print(f"  [cyan]{solutions[0]}[/cyan]")
            
            self.console.print()
    
    def _print_detailed_results(self, results: Dict[str, Any]):
        """Print detailed results from each doctor if verbose mode."""
        doctor_results = results.get("doctor_results", [])
        
        if not doctor_results:
            return
        
        self.console.print("[bold cyan]📋 Detailed Results[/bold cyan]")
        self.console.print()
        
        for doctor_result in doctor_results:
            doctor_name = doctor_result.get("doctor", "unknown")
            summary = doctor_result.get("summary", {})
            
            # Create a simple table for each doctor's summary
            if summary:
                table = Table(title=f"Doctor: {doctor_name}", box=box.SIMPLE)
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="white")
                
                for key, value in summary.items():
                    table.add_row(key.replace("_", " ").title(), str(value))
                
                self.console.print(table)
                self.console.print()







