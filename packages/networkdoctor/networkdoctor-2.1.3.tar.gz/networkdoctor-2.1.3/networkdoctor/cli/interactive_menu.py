"""
Beautiful Interactive Terminal Menu for NetworkDoctor
"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt
from rich import box
from typing import Optional, Dict, List


class InteractiveMenu:
    """Interactive menu system for NetworkDoctor"""
    
    def __init__(self):
        self.console = Console()
        self.tools = {
            1: {"name": "Full Network Diagnosis", "description": "Complete network analysis with all doctors", "doctors": None},
            2: {"name": "ISP Throttle Detector", "description": "Detect ISP speed throttling with evidence", "doctors": "isp_throttle"},
            3: {"name": "Internet Quality Score", "description": "Score your connection for gaming, streaming, Zoom", "doctors": "quality_score"},
            4: {"name": "WiFi Security Scanner", "description": "Detect rogue devices, evil twin AP, ARP spoofing", "doctors": "wifi"},
            5: {"name": "Smart Route Analyzer", "description": "Visual route map with submarine cable detection", "doctors": "route_analyzer"},
            6: {"name": "Auto Network Repair", "description": "Automatically fix DNS, MTU, gateway, proxy issues", "doctors": "auto_repair"},
            7: {"name": "Server Self-Heal", "description": "Monitor CPU, RAM, disk and auto-restart services", "doctors": "server_heal"},
            8: {"name": "AI Root Cause Analysis", "description": "Natural language problem analysis", "doctors": "root_cause"},
            9: {"name": "Predictive Failure Alert", "description": "Predict router, ISP, and cable failures", "doctors": "predictive"},
            10: {"name": "Offline Diagnosis", "description": "Full local analysis without internet", "doctors": "offline"},
            11: {"name": "DNS Doctor", "description": "DNS resolution, DNSSEC, cache poisoning detection", "doctors": "dns"},
            12: {"name": "SSL/TLS Checker", "description": "Certificate validation and security analysis", "doctors": "ssl"},
            13: {"name": "Performance Analyst", "description": "Latency, jitter, packet loss analysis", "doctors": "performance"},
            14: {"name": "Security Inspector", "description": "Security vulnerabilities and threat detection", "doctors": "security"},
            15: {"name": "Quick Scan", "description": "Fast 30-second basic connectivity check", "mode": "quick"},
            16: {"name": "📚 Show Help & Generate help.md", "description": "Generate comprehensive help documentation", "action": "help"},
        }
        
        self.output_formats = {
            1: {"name": "Terminal (Default)", "format": "terminal"},
            2: {"name": "HTML Report", "format": "html"},
            3: {"name": "JSON Export", "format": "json"},
            4: {"name": "PDF Report", "format": "pdf"},
            5: {"name": "CSV Export", "format": "csv"},
            6: {"name": "Markdown", "format": "markdown"},
        }
    
    def show_welcome(self):
        """Display welcome banner"""
        banner = """
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   🩺  N E T W O R K  D O C T O R  -  AI  D I A G N O S T I C         ║
║                                                                       ║
║   Ultimate Network Diagnostic Tool for Everyone                      ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
"""
        self.console.print(banner, style="bold cyan")
        self.console.print()
    
    def show_main_menu(self) -> Dict:
        """Display main menu and get user selection"""
        self.show_welcome()
        
        # Create tools table
        table = Table(
            title="[bold cyan]Available Diagnostic Tools[/bold cyan]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold white",
            border_style="cyan"
        )
        
        table.add_column("No.", style="cyan", width=5, justify="center")
        table.add_column("Tool Name", style="white", width=35)
        table.add_column("Description", style="dim", width=45)
        
        for num, tool in self.tools.items():
            table.add_row(
                str(num),
                f"[bold]{tool['name']}[/bold]",
                tool['description']
            )
        
        self.console.print(table)
        self.console.print()
        
        # Get tool selection
        selected = IntPrompt.ask(
            "\n[bold cyan]Select a tool (enter number)[/bold cyan]",
            choices=[str(i) for i in range(1, len(self.tools) + 1)],
            default="1"
        )
        
        tool_info = self.tools[selected]
        
        # If help was selected, return immediately
        if tool_info.get("action") == "help":
            return {"action": "help"}
        
        # Get target input
        self.console.print()
        self.console.print("[bold yellow]📋 Enter target information:[/bold yellow]")
        self.console.print("   Examples: google.com, 192.168.1.1, https://example.com, 192.168.1.0/24")
        
        target = Prompt.ask(
            "[bold cyan]Target[/bold cyan]",
            default="google.com"
        )
        
        # Get output format
        self.console.print()
        output_table = Table(
            title="[bold cyan]Output Format Options[/bold cyan]",
            box=box.SIMPLE,
            show_header=False,
            border_style="blue"
        )
        
        for num, fmt in self.output_formats.items():
            output_table.add_row(f"[cyan]{num}.[/cyan]", fmt['name'])
        
        self.console.print(output_table)
        
        output_choice = IntPrompt.ask(
            "\n[bold cyan]Select output format (enter number)[/bold cyan]",
            choices=[str(i) for i in range(1, len(self.output_formats) + 1)],
            default="1"
        )
        
        output_info = self.output_formats[output_choice]
        
        # Build arguments
        args_dict = {
            "targets": [target],
            "doctors": tool_info.get("doctors"),
            "mode": tool_info.get("mode"),
            "output": output_info["format"],
            "verbose": False,
            "no_cache": False,
        }
        
        # If PDF/HTML/JSON, ask for filename
        if output_info["format"] in ["pdf", "html", "json", "csv", "markdown"]:
            filename = Prompt.ask(
                f"[bold cyan]Output filename[/bold cyan] (press Enter for auto-generated)",
                default=""
            )
            if filename:
                args_dict["output_file"] = filename
        
        return args_dict
    
    def show_scan_progress(self, target: str, tool_name: str):
        """Show scanning progress"""
        self.console.print()
        self.console.print(Panel.fit(
            f"[bold cyan]🔍 Scanning: {target}[/bold cyan]\n"
            f"[dim]Tool: {tool_name}[/dim]",
            border_style="cyan"
        ))
        self.console.print()
    
    def show_completion(self):
        """Show completion message"""
        self.console.print()
        self.console.print("[bold green]✅ Scan completed successfully![/bold green]")
        self.console.print("[dim]Check the output file or terminal results above.[/dim]")
        self.console.print()

