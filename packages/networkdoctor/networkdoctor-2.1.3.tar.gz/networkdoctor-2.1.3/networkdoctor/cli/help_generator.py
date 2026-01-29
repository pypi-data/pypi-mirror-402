"""
Help Generator for NetworkDoctor - Creates comprehensive help.md file
"""
from pathlib import Path
from datetime import datetime
from typing import Dict


class HelpGenerator:
    """Generate comprehensive help documentation"""
    
    @staticmethod
    def generate_help(output_file: str = None):
        """Generate help.md file with complete documentation"""
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"outputs/help.md"
        
        output_path = Path(output_file)
        
        # Check if outputs folder exists, create only if needed
        outputs_dir = Path("outputs")
        if not outputs_dir.exists():
            outputs_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure file goes to outputs folder
        if "outputs" not in str(output_path):
            output_path = Path(f"outputs/{output_path.name if output_path.name else 'help.md'}")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        help_content = HelpGenerator._generate_help_content()
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(help_content)
        
        return str(output_path)
    
    @staticmethod
    def _generate_help_content() -> str:
        """Generate complete help documentation"""
        
        content = f"""# 🩺 NetworkDoctor - Complete Help Documentation

**Version:** 2.1.3  
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [All Diagnostic Tools](#all-diagnostic-tools)
5. [Usage Examples](#usage-examples)
6. [Output Formats](#output-formats)
7. [Getting Help](#getting-help)
8. [Contact Information](#contact-information)

---

## 🎯 Introduction

NetworkDoctor is the world's most advanced AI-powered network diagnostic tool. It helps you:

- **Diagnose** network problems automatically
- **Detect** security threats and vulnerabilities
- **Analyze** network performance and quality
- **Fix** common network issues automatically
- **Predict** network failures before they happen
- **Generate** professional reports for ISPs and IT teams

**Why NetworkDoctor?**
- Uses AI to understand problems in plain English
- Provides exact solutions with copy-paste commands
- Features not available in any other tool
- Works for home users, IT engineers, and enterprises

---

## 📦 Installation

### Standard Installation

```bash
pip install networkdoctor
```

### Verify Installation

```bash
networkdoctor --version
# or
ndoc --version
```

### Requirements

- Python 3.8 or higher
- Linux, macOS, or Windows
- Internet connection (optional - has offline mode)

---

## 🚀 Quick Start

### Interactive Mode (Recommended)

Simply run:

```bash
networkdoctor
```

This opens a beautiful interactive menu where you can:
1. Select a tool by number (1-15)
2. Enter your target (domain, IP, or URL)
3. Choose output format
4. Get results automatically

### Direct Command Mode

```bash
# Scan a website
networkdoctor https://google.com

# Quick scan
networkdoctor --quick example.com

# Specific tool
networkdoctor --doctors isp_throttle example.com
```

---

## 🛠️ All Diagnostic Tools

### 1. Full Network Diagnosis
**What it does:** Complete network analysis with all doctors  
**Use when:** You want comprehensive analysis of everything  
**Importance:** Gives you the full picture of your network health

```bash
networkdoctor example.com
# or select option 1 in interactive menu
```

---

### 2. ISP Throttle Detector
**What it does:** Detects when your ISP is throttling your internet speed  
**Use when:** Your internet is slow or inconsistent  
**Importance:** Provides evidence for ISP complaints with complaint letter template

**Features:**
- Performs multiple speed tests
- Analyzes throttling patterns
- Generates ISP complaint letter
- Provides evidence for regulatory bodies

```bash
networkdoctor --doctors isp_throttle example.com
```

---

### 3. Internet Quality Score
**What it does:** Scores your connection for gaming, streaming, Zoom, and cloud work  
**Use when:** You want to know if your internet is good for specific activities  
**Importance:** Helps you understand if your connection meets your needs

**Scoring:**
- **Gaming:** <20ms latency, <10ms jitter = Excellent
- **Streaming:** >25 Mbps = 4K capable
- **Zoom:** <50ms latency = Crystal clear calls
- **Cloud Work:** >50 Mbps, <50ms = Optimal

```bash
networkdoctor --doctors quality_score example.com
```

---

### 4. WiFi Security Scanner
**What it does:** Detects rogue devices, evil twin access points, and ARP spoofing  
**Use when:** You suspect WiFi security issues  
**Importance:** Protects you from network attacks and unauthorized access

**Detects:**
- Rogue/unauthorized devices on your network
- Evil twin access points (fake WiFi)
- ARP spoofing attacks
- Signal strength issues

```bash
networkdoctor --doctors wifi localhost
```

---

### 5. Smart Route Analyzer
**What it does:** Visualizes network routes on a world map, detects submarine cables  
**Use when:** You want to see how data travels to destinations  
**Importance:** Identifies where packets fail and route optimization opportunities

**Features:**
- Visual route mapping
- Submarine cable detection
- Packet failure identification
- Geographic route analysis

```bash
networkdoctor --doctors route_analyzer example.com
```

---

### 6. Auto Network Repair
**What it does:** Automatically fixes DNS, MTU, gateway, proxy, and IPv6 issues  
**Use when:** You have common network connectivity problems  
**Importance:** Fixes issues automatically without manual troubleshooting

**Fixes:**
- DNS resolution problems
- MTU size issues
- Gateway connectivity
- Proxy misconfiguration
- IPv6 conflicts

```bash
networkdoctor --doctors auto_repair example.com
# Note: Requires admin privileges
```

---

### 7. Server Self-Heal System
**What it does:** Monitors CPU, RAM, disk I/O and automatically restarts safe services  
**Use when:** Your server is experiencing performance issues  
**Importance:** Prevents server crashes and maintains uptime

**Monitors:**
- CPU spikes and high usage
- Memory leaks and RAM issues
- Disk I/O bottlenecks
- Hung processes

```bash
networkdoctor --doctors server_heal localhost
```

---

### 8. AI Root Cause Analysis
**What it does:** Understands natural language problems and provides exact solutions  
**Use when:** You have a problem but don't know the technical cause  
**Importance:** Translates problems into actionable solutions

**Example:**
- Input: "Internet is slow"
- Output: Identifies bandwidth/ISP/latency issue with exact fix commands

```bash
networkdoctor --doctors root_cause example.com
```

---

### 9. Predictive Failure Alert
**What it does:** Predicts router, ISP, and cable failures before they happen  
**Use when:** You want to prevent problems proactively  
**Importance:** Warns you before failures occur, saving downtime

**Predicts:**
- Router failure (based on latency/error patterns)
- ISP downtime (based on timeout patterns)
- Cable issues (based on intermittent problems)

```bash
networkdoctor --doctors predictive example.com
```

---

### 10. Offline Diagnosis Mode
**What it does:** Full local network analysis without internet connection  
**Use when:** You don't have internet but need to diagnose local network  
**Importance:** Works even when internet is down

**Checks:**
- Local network configuration
- Network interfaces
- DNS configuration (local)
- Routing table
- ARP table
- System network stats

```bash
networkdoctor --doctors offline localhost
```

---

### 11. DNS Doctor
**What it does:** Checks DNS resolution, DNSSEC, cache poisoning  
**Use when:** Websites won't load or DNS errors occur  
**Importance:** Ensures domain name resolution works correctly

```bash
networkdoctor --doctors dns example.com
```

---

### 12. SSL/TLS Checker
**What it does:** Validates SSL certificates and security  
**Use when:** You need to check certificate validity  
**Importance:** Ensures secure connections and identifies certificate issues

```bash
networkdoctor --doctors ssl example.com
```

---

### 13. Performance Analyst
**What it does:** Measures latency, jitter, packet loss  
**Use when:** You need detailed performance metrics  
**Importance:** Identifies performance bottlenecks

```bash
networkdoctor --doctors performance example.com
```

---

### 14. Security Inspector
**What it does:** Detects security vulnerabilities and threats  
**Use when:** You need security assessment  
**Importance:** Identifies security risks before they become problems

```bash
networkdoctor --doctors security example.com
```

---

### 15. Quick Scan
**What it does:** Fast 30-second basic connectivity check  
**Use when:** You need a quick network check  
**Importance:** Provides instant network status

```bash
networkdoctor --quick example.com
```

---

## 💡 Usage Examples

### Basic Usage

```bash
# Scan a website
networkdoctor https://google.com

# Scan an IP address
networkdoctor 192.168.1.1

# Scan a domain
networkdoctor example.com

# Scan a subnet
networkdoctor 192.168.1.0/24
```

### Scan Modes

```bash
# Quick scan (30 seconds)
networkdoctor --quick example.com

# Full scan (2 minutes) - default
networkdoctor --full example.com

# Deep scan (5+ minutes)
networkdoctor --deep example.com

# Continuous monitoring
networkdoctor --monitor example.com
```

### Selecting Tools

```bash
# Run specific tools
networkdoctor --doctors dns,ssl,performance example.com

# Skip specific tools
networkdoctor --skip security,firewall example.com

# Use unique features
networkdoctor --doctors isp_throttle,quality_score,root_cause example.com
```

### Output Formats

```bash
# Terminal output (default)
networkdoctor example.com

# HTML report
networkdoctor --output html --output-file report.html example.com

# PDF report (auto-generates in outputs/pdf/)
networkdoctor --output pdf example.com

# JSON export (auto-generates in outputs/json/)
networkdoctor --output json example.com
```

**Note:** PDF, HTML, and JSON files are automatically saved in the `outputs/` folder:
- PDF files → `outputs/pdf/`
- JSON files → `outputs/json/`
- HTML files → `outputs/html/`

---

## 📄 Output Formats

### Terminal (Default)
Beautiful colored output with tables and panels - perfect for immediate viewing.

### HTML Report
Interactive reports with charts and formatting - great for sharing with teams.

### PDF Report
Professional reports for ISP complaints and IT reports - saved in `outputs/pdf/`

### JSON Export
Machine-readable format for integration with other tools - saved in `outputs/json/`

### CSV Export
Data format for analysis in spreadsheets - saved in `outputs/csv/`

### Markdown
Documentation-friendly format for wikis and documentation.

---

## ❓ Getting Help

### Command Line Help

```bash
# Show help
networkdoctor --help
# or
networkdoctor -h

# Show version
networkdoctor --version
```

### Interactive Menu Help

When you run `networkdoctor` without arguments, you'll see:
- Numbered list of all tools
- Description of each tool
- Prompt to select tool and enter target
- Output format options

### This Help File

This help.md file is generated automatically and saved in the `outputs/` folder.

To regenerate it:
```bash
networkdoctor --help
```

---

## 📞 Contact Information

### Support & Inquiries

**Project Owner:** frankvena25  
**Email:** frankvenas25@gmail.com  
**WhatsApp:** +255 698 341 653 (Tanzania)

### GitHub Repository

**Repository:** https://github.com/frankvena25/NetworkDoctor  
**Issues:** https://github.com/frankvena25/NetworkDoctor/issues  
**Documentation:** https://github.com/frankvena25/NetworkDoctor/blob/main/README.md

### Reporting Issues

For bugs, feature requests, or questions:
1. **GitHub Issues:** https://github.com/frankvena25/NetworkDoctor/issues
2. **Email:** frankvenas25@gmail.com
3. **WhatsApp:** +255 698 341 653

---

## 🔍 Common Questions

**Q: Do I need admin/root privileges?**  
A: Most features work without privileges. Auto-repair and server-heal features require admin access.

**Q: Does it work offline?**  
A: Yes! Use the "Offline Diagnosis" tool (option 10) for local network analysis.

**Q: Where are reports saved?**  
A: All reports are automatically saved in the `outputs/` folder with organized subfolders.

**Q: Can I use it on Windows/Mac/Linux?**  
A: Yes! NetworkDoctor works on all major operating systems.

**Q: Is it free?**  
A: Yes! NetworkDoctor is open-source and free to use under MIT License.

---

## 📚 Additional Resources

- **Full Documentation:** Check `docs/` folder in the repository
- **API Reference:** See `docs/api_reference.md`
- **Examples:** See `examples/` folder for usage examples
- **Contributing:** See `CONTRIBUTING.md` if you want to contribute

---

## 🙏 Acknowledgments

Created with ❤️ by frankvena25

Thank you for using NetworkDoctor! We hope it helps you solve your network problems quickly and efficiently.

---

**NetworkDoctor** - Your Network Expert, Always Available 🩺🌐

*For the latest updates and support, visit: https://github.com/frankvena25/NetworkDoctor*

        """
        
        return content


