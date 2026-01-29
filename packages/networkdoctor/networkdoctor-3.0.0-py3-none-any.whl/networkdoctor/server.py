#!/usr/bin/env python3
"""
NetworkDoctor Server Module
Run NetworkDoctor as a server monitoring service
"""
import asyncio
import json
import logging
import time
import socket
import subprocess
import platform
import os
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

import yaml
from networkdoctor.core.doctor import NetworkDoctor
from networkdoctor.utils.network_tools import get_local_ip, check_connectivity


class NetworkDoctorServer:
    """NetworkDoctor server for autonomous monitoring"""
    
    def __init__(self, config_path="/etc/networkdoctor/server_config.yaml"):
        self.config = self._load_config(config_path)
        self.setup_logging()
        self.local_ip = get_local_ip()
        self.hostname = socket.gethostname()
        
    def _load_config(self, config_path):
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self):
        """Get default configuration"""
        return {
            "server": {
                "mode": "autonomous",
                "auto_discovery": True,
                "continuous_monitoring": True
            },
            "monitoring": {
                "auto_detect_services": True,
                "auto_detect_interfaces": True,
                "default_checks": ["dns", "ssl", "performance", "security", "firewall", "application", "cloud", "routing"]
            },
            "output": {
                "format": "json",
                "log_file": "/var/log/networkdoctor/networkdoctor.log",
                "report_interval": 3600,
                "auto_cleanup": True
            }
        }
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_file = self.config.get("output", {}).get("log_file", "/var/log/networkdoctor/networkdoctor.log")
        log_dir = Path(log_file).parent
        
        # Try to create log directory, fallback to temp if permission denied
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Fallback to user's temp directory
            import tempfile
            temp_dir = tempfile.gettempdir()
            fallback_log_file = os.path.join(temp_dir, "networkdoctor.log")
            self.config["output"]["log_file"] = fallback_log_file
            log_file = fallback_log_file
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("NetworkDoctorServer")
    
    async def auto_discover_targets(self):
        """Auto-discover monitoring targets"""
        targets = []
        
        # Add localhost
        targets.append("localhost")
        targets.append("127.0.0.1")
        targets.append(self.local_ip)
        
        # Discover services on common ports
        common_ports = [80, 443, 22, 21, 25, 53, 110, 143, 993, 995]
        for port in common_ports:
            if await check_connectivity("localhost", port, timeout=2):
                targets.append(f"localhost:{port}")
        
        # Discover cloud environment
        cloud_info = await self.detect_cloud_environment()
        if cloud_info.get("provider"):
            targets.extend(cloud_info.get("endpoints", []))
        
        # Discover network interfaces
        interfaces = await self.discover_interfaces()
        for interface in interfaces:
            if interface.get("ip"):
                targets.append(interface["ip"])
        
        return list(set(targets))  # Remove duplicates
    
    async def detect_cloud_environment(self):
        """Detect if running in cloud environment"""
        cloud_info = {"provider": None, "endpoints": []}
        
        try:
            # AWS detection
            aws_metadata = await self.check_aws_metadata()
            if aws_metadata:
                cloud_info["provider"] = "aws"
                cloud_info["endpoints"] = ["amazonaws.com", "aws.amazon.com"]
                return cloud_info
            
            # Azure detection
            azure_metadata = await self.check_azure_metadata()
            if azure_metadata:
                cloud_info["provider"] = "azure"
                cloud_info["endpoints"] = ["azure.com", "cloudapp.net"]
                return cloud_info
            
            # GCP detection
            gcp_metadata = await self.check_gcp_metadata()
            if gcp_metadata:
                cloud_info["provider"] = "gcp"
                cloud_info["endpoints"] = ["googleapis.com", "googleusercontent.com"]
                return cloud_info
                
        except Exception as e:
            self.logger.error(f"Cloud detection failed: {e}")
        
        return cloud_info
    
    async def check_aws_metadata(self):
        """Check AWS metadata service"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://169.254.169.254/latest/meta-data/",
                    timeout=aiohttp.ClientTimeout(total=2)
                ) as response:
                    if response.status == 200:
                        return {"aws": True}
        except:
            pass
        return None
    
    async def check_azure_metadata(self):
        """Check Azure metadata service"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://169.254.169.254/metadata/instance?api-version=2021-02-01",
                    timeout=aiohttp.ClientTimeout(total=2)
                ) as response:
                    if response.status == 200:
                        return {"azure": True}
        except:
            pass
        return None
    
    async def check_gcp_metadata(self):
        """Check GCP metadata service"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://metadata.google.internal/computeMetadata/v1/",
                    timeout=aiohttp.ClientTimeout(total=2),
                    headers={"Metadata-Flavor": "Google"}
                ) as response:
                    if response.status == 200:
                        return {"gcp": True}
        except:
            pass
        return None
    
    async def discover_interfaces(self):
        """Discover network interfaces"""
        interfaces = []
        
        try:
            # Linux
            if platform.system() == "Linux":
                result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'inet ' in line and '127.0.0.1' not in line:
                        ip_match = subprocess.run(['grep', '-oP', r'inet \K[\d.]+'], input=line, capture_output=True, text=True)
                        if ip_match.stdout.strip():
                            interfaces.append({
                                "ip": ip_match.stdout.strip(),
                                "interface": "auto-discovered"
                            })
        except Exception as e:
            self.logger.error(f"Interface discovery failed: {e}")
        
        return interfaces
    
    async def run_continuous_monitoring(self):
        """Run continuous monitoring loop"""
        self.logger.info("Starting NetworkDoctor server monitoring...")
        self.logger.info(f"Local IP: {self.local_ip}")
        self.logger.info(f"Hostname: {self.hostname}")
        
        report_interval = self.config.get("output", {}).get("report_interval", 3600)
        last_report = time.time()
        
        while True:
            try:
                # Auto-discover targets
                targets = await self.auto_discover_targets()
                self.logger.info(f"Auto-discovered {len(targets)} targets: {targets}")
                
                # Run NetworkDoctor diagnosis
                doctor = NetworkDoctor(use_cache=True)
                
                # Create mock scan results for server mode
                scan_results = []
                for target in targets:
                    scan_results.append({"target": target})
                
                # Run diagnosis with default doctors
                default_doctors = self.config.get("monitoring", {}).get("default_checks", [])
                results = await doctor.diagnose(
                    targets=targets,
                    doctors=default_doctors,
                    verbose=False
                )
                
                # Save results
                await self.save_results(results)
                
                # Check if it's time for a detailed report
                current_time = time.time()
                if current_time - last_report >= report_interval:
                    await self.generate_report(results)
                    last_report = current_time
                
                # Cleanup old files if configured
                if self.config.get("output", {}).get("auto_cleanup", True):
                    await self.cleanup_old_files()
                
                # Wait for next cycle (configurable interval)
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                self.logger.error(f"Monitoring cycle failed: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def save_results(self, results):
        """Save monitoring results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"/var/lib/networkdoctor/results_{timestamp}.json"
        
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            self.logger.info(f"Results saved to {output_file}")
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
    
    async def generate_report(self, results):
        """Generate detailed report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"/var/lib/networkdoctor/report_{timestamp}.pdf"
        
        try:
            from networkdoctor.outputs.pdf_reporter import PDFReporter
            PDFReporter.generate(results, report_file)
            self.logger.info(f"Report generated: {report_file}")
        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")
    
    async def cleanup_old_files(self):
        """Clean up old result files"""
        try:
            import glob
            result_files = glob.glob("/var/lib/networkdoctor/results_*.json")
            report_files = glob.glob("/var/lib/networkdoctor/report_*.pdf")
            
            # Keep only the latest 10 files
            all_files = result_files + report_files
            all_files.sort(key=lambda x: os.path.getctime(x), reverse=True)
            
            for old_file in all_files[10:]:
                os.remove(old_file)
                self.logger.info(f"Cleaned up old file: {old_file}")
                
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
    
    async def start(self):
        """Start the NetworkDoctor server"""
        self.logger.info("NetworkDoctor Server starting...")
        await self.run_continuous_monitoring()


async def main():
    """Main entry point for server mode"""
    server = NetworkDoctorServer()
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
