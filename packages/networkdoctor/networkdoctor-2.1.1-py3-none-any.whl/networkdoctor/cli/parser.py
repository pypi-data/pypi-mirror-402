"""
Advanced CLI Argument Parser for NetworkDoctor
"""
import argparse
from typing import List, Optional
from pathlib import Path


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command line arguments for NetworkDoctor.
    
    Args:
        args: Optional list of arguments (for testing)
        
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        prog="networkdoctor",
        description="🩺 NetworkDoctor - Ultimate AI-Powered Network Diagnostic Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  networkdoctor https://example.com
  networkdoctor 192.168.1.1 --quick
  networkdoctor @targets.txt --output html
  networkdoctor example.com --doctors dns,ssl,performance
        """
    )
    
    # Target input
    parser.add_argument(
        "targets",
        nargs="*",
        help="Target(s) to scan: URLs, IPs, domains, CIDR, or @filename (optional - shows interactive menu)"
    )
    
    # Scan modes
    scan_mode = parser.add_mutually_exclusive_group()
    scan_mode.add_argument(
        "--quick",
        action="store_true",
        help="Quick scan (30 seconds) - Basic connectivity check"
    )
    scan_mode.add_argument(
        "--full",
        action="store_true",
        default=True,
        help="Full diagnosis (2 minutes) - Comprehensive check [default]"
    )
    scan_mode.add_argument(
        "--deep",
        action="store_true",
        help="Deep forensic (5+ minutes) - Everything including packet analysis"
    )
    scan_mode.add_argument(
        "--monitor",
        action="store_true",
        help="Continuous monitoring - Run forever, alert on changes"
    )
    
    # Doctor selection
    parser.add_argument(
        "--doctors",
        type=str,
        help="Comma-separated list of doctors to run (e.g., dns,ssl,performance)"
    )
    parser.add_argument(
        "--skip",
        type=str,
        help="Comma-separated list of doctors to skip"
    )
    
    # Output options
    parser.add_argument(
        "--output",
        "-o",
        choices=["terminal", "html", "json", "csv", "pdf", "markdown"],
        default="terminal",
        help="Output format [default: terminal]"
    )
    parser.add_argument(
        "--output-file",
        "-f",
        type=str,
        help="Output file path (required for non-terminal formats)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Quiet mode - minimal output"
    )
    
    # Configuration
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        help="Path to configuration file (YAML/JSON)"
    )
    
    # Limits
    parser.add_argument(
        "--max-targets",
        type=int,
        default=100,
        help="Maximum number of targets to scan [default: 100]"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Scan timeout in seconds [default: 300]"
    )
    parser.add_argument(
        "--rate-limit",
        type=int,
        default=10,
        help="Rate limit (requests per second) [default: 10]"
    )
    
    # Integration options
    parser.add_argument(
        "--notify-slack",
        type=str,
        help="Slack webhook URL for notifications"
    )
    parser.add_argument(
        "--notify-email",
        type=str,
        help="Email address for notifications"
    )
    parser.add_argument(
        "--webhook",
        type=str,
        help="Webhook URL for results"
    )
    
    # API mode
    parser.add_argument(
        "--api",
        action="store_true",
        help="Start API server mode"
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=8080,
        help="API server port [default: 8080]"
    )
    parser.add_argument(
        "--api-host",
        type=str,
        default="127.0.0.1",
        help="API server host [default: 127.0.0.1]"
    )
    
    # Other options
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable result caching"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="NetworkDoctor 2.1.1"
    )
    
    return parser.parse_args(args)







