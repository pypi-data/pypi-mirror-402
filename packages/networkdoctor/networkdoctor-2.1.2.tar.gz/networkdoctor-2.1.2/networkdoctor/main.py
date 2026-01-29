#!/usr/bin/env python3
"""
NetworkDoctor - Main Entry Point
"""
import sys
from networkdoctor.cli.parser import parse_args
from networkdoctor.core.doctor import NetworkDoctor
from networkdoctor.cli.interactive_menu import InteractiveMenu


def main():
    """Main entry point"""
    try:
        args = parse_args()
        
        # Handle help command
        if hasattr(args, 'help') and args.help or ('--help' in sys.argv or '-h' in sys.argv):
            from networkdoctor.cli.help_generator import HelpGenerator
            from rich.console import Console
            console = Console()
            
            console.print("\n[bold cyan]🩺 NetworkDoctor - Help Documentation[/bold cyan]\n")
            console.print("Generating comprehensive help.md file...")
            
            help_file = HelpGenerator.generate_help()
            
            console.print(f"\n[bold green]✅ Help documentation generated![/bold green]")
            console.print(f"[cyan]📄 File saved at: {help_file}[/cyan]")
            console.print(f"\n[dim]Read the help.md file in the outputs folder for complete documentation.[/dim]")
            console.print(f"[dim]Open it with: cat {help_file} or open it in a text editor[/dim]\n")
            
            # Show brief help
            console.print("[bold]Quick Help:[/bold]")
            console.print("  networkdoctor                    - Interactive menu")
            console.print("  networkdoctor example.com        - Scan a website")
            console.print("  networkdoctor --help             - Generate help.md")
            console.print("  networkdoctor --version          - Show version")
            console.print("  networkdoctor --doctors dns,ssl  - Use specific tools\n")
            
            return 0
        
        # If no targets provided, show interactive menu
        if not args.targets:
            menu = InteractiveMenu()
            menu_args = menu.show_main_menu()
            
            # Check if help was requested
            if menu_args.get("action") == "help":
                from networkdoctor.cli.help_generator import HelpGenerator
                from rich.console import Console
                console = Console()
                
                console.print("\n[bold cyan]Generating help documentation...[/bold cyan]\n")
                help_file = HelpGenerator.generate_help()
                console.print(f"[bold green]✅ Help documentation generated![/bold green]")
                console.print(f"[cyan]📄 File saved at: {help_file}[/cyan]")
                console.print(f"\n[dim]Read help.md in the outputs folder for complete documentation.[/dim]\n")
                return 0
            
            # Mark as interactive
            args._was_interactive = True
            
            # Merge menu selections with command line args
            if menu_args.get("doctors"):
                args.doctors = menu_args["doctors"]
            if menu_args.get("mode"):
                if menu_args["mode"] == "quick":
                    args.quick = True
                    args.full = False
            if menu_args.get("output"):
                args.output = menu_args["output"]
            if menu_args.get("output_file"):
                args.output_file = menu_args["output_file"]
            
            args.targets = menu_args["targets"]
            
            # Show progress
            tool_name = next((t["name"] for t in menu.tools.values() if t.get("doctors") == menu_args.get("doctors")), "Full Diagnosis")
            menu.show_scan_progress(args.targets[0], tool_name)
        
        doctor = NetworkDoctor(use_cache=not args.no_cache)
        result = doctor.run(args)
        
        # Show completion if interactive
        was_interactive = not hasattr(args, '_was_interactive') or args._was_interactive
        if was_interactive:
            menu = InteractiveMenu()
            menu.show_completion()
        
        return result
    except KeyboardInterrupt:
        print("\n\n[bold red]Interrupted by user[/bold red]")
        return 130
    except Exception as e:
        print(f"[bold red]Fatal error: {e}[/bold red]", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())







