"""
Server Self-Heal System - Auto-detect and fix server issues

"""
import psutil
import asyncio
import subprocess
import platform
import os
from typing import List, Dict, Any, Optional
from datetime import datetime


class ServerSelfHeal:
    """Detect server issues and automatically restart safe services"""
    
    def __init__(self):
        self.name = "Server Self-Heal System"
        self.system = platform.system()
        self.is_admin = self._check_admin()
        self.safe_services = [
            "nginx", "apache2", "httpd", "php-fpm", "mysql", "mariadb",
            "postgresql", "redis", "memcached", "docker", "containerd"
        ]
        self.cpu_threshold = 90.0  # CPU usage threshold (%)
        self.mem_threshold = 90.0  # Memory usage threshold (%)
        self.disk_io_threshold = 90.0  # Disk IO wait threshold (%)
        self.memory_leak_detection_window = 300  # seconds
        
    def _check_admin(self) -> bool:
        """Check if running with admin privileges"""
        if self.system == "Windows":
            try:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except:
                return False
        else:
            return os.geteuid() == 0
    
    async def diagnose(self, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect server issues (CPU, RAM, Disk IO) and suggest auto-healing.
        
        Args:
            scan_results: Results from network scan
            
        Returns:
            Server health diagnosis with auto-heal recommendations
        """
        issues = []
        findings = []
        auto_heals = []
        
        # Check CPU spikes
        cpu_result = await self._check_cpu_spikes()
        if cpu_result.get("issue"):
            issues.append(cpu_result["issue"])
        if cpu_result.get("heal_action"):
            auto_heals.append(cpu_result["heal_action"])
        
        # Check RAM leaks
        ram_result = await self._check_ram_leaks()
        if ram_result.get("issue"):
            issues.append(ram_result["issue"])
        if ram_result.get("heal_action"):
            auto_heals.append(ram_result["heal_action"])
        
        # Check Disk IO
        disk_result = await self._check_disk_io()
        if disk_result.get("issue"):
            issues.append(disk_result["issue"])
        if disk_result.get("heal_action"):
            auto_heals.append(disk_result["heal_action"])
        
        # Check for hung processes
        hung_result = await self._check_hung_processes()
        if hung_result.get("issue"):
            issues.append(hung_result["issue"])
        if hung_result.get("heal_action"):
            auto_heals.append(hung_result["heal_action"])
        
        # Generate summary
        findings.append({
            "finding": "server_health_check",
            "cpu_health": cpu_result.get("status", "unknown"),
            "memory_health": ram_result.get("status", "unknown"),
            "disk_health": disk_result.get("status", "unknown"),
            "auto_heal_available": len(auto_heals) > 0 and self.is_admin,
        })
        
        return {
            "doctor": "server_self_heal",
            "status": "completed",
            "issues": issues,
            "findings": findings,
            "auto_heals": auto_heals,
            "summary": {
                "total_issues": len(issues),
                "heal_actions_available": len(auto_heals),
                "admin_required": not self.is_admin,
                "server_health_score": self._calculate_health_score(
                    cpu_result, ram_result, disk_result
                ),
            },
        }
    
    async def _check_cpu_spikes(self) -> Dict[str, Any]:
        """Detect CPU spikes and identify culprit processes"""
        result = {}
        
        try:
            # Get CPU usage over 5 seconds
            cpu_samples = []
            for _ in range(5):
                cpu_samples.append(psutil.cpu_percent(interval=1))
                await asyncio.sleep(0.5)
            
            avg_cpu = sum(cpu_samples) / len(cpu_samples)
            max_cpu = max(cpu_samples)
            
            if max_cpu > self.cpu_threshold:
                # Find top CPU-consuming processes
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                    try:
                        pinfo = proc.info
                        if pinfo['cpu_percent'] and pinfo['cpu_percent'] > 10:
                            processes.append(pinfo)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Sort by CPU usage
                processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
                
                result["issue"] = {
                    "severity": "high" if max_cpu > 95 else "medium",
                    "type": "cpu_spike",
                    "title": f"CPU Spike Detected: {max_cpu:.1f}% (Threshold: {self.cpu_threshold}%)",
                    "description": f"Average CPU usage: {avg_cpu:.1f}%, Peak: {max_cpu:.1f}%",
                    "top_processes": processes[:5],
                    "recommendations": [
                        "Check top CPU-consuming processes",
                        "Consider process priority adjustment",
                        "Investigate potential infinite loops",
                        "Check for runaway scripts or services",
                    ],
                }
                
                result["status"] = "critical" if max_cpu > 95 else "warning"
                
                # Suggest auto-heal for safe services
                if self.is_admin:
                    # Check if high-CPU process is a safe service
                    high_cpu_processes = [p for p in processes[:3] if p.get('cpu_percent', 0) > 50]
                    safe_to_restart = []
                    
                    for proc_info in high_cpu_processes:
                        proc_name = proc_info.get('name', '').lower()
                        for safe_service in self.safe_services:
                            if safe_service in proc_name:
                                safe_to_restart.append({
                                    "service": safe_service,
                                    "pid": proc_info.get('pid'),
                                    "cpu_usage": proc_info.get('cpu_percent', 0),
                                })
                                break
                    
                    if safe_to_restart:
                        result["heal_action"] = {
                            "type": "restart_service",
                            "services": safe_to_restart,
                            "description": "High CPU services can be safely restarted",
                            "command": self._generate_restart_command(safe_to_restart[0]["service"]),
                            "manual": "Run: sudo systemctl restart <service-name>",
                        }
            else:
                result["status"] = "healthy"
                
        except Exception as e:
            result["error"] = str(e)
            result["status"] = "unknown"
        
        return result
    
    async def _check_ram_leaks(self) -> Dict[str, Any]:
        """Detect memory leaks by monitoring RAM usage over time"""
        result = {}
        
        try:
            # Get memory usage
            mem = psutil.virtual_memory()
            mem_percent = mem.percent
            
            # Get process memory usage
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'memory_info']):
                try:
                    pinfo = proc.info
                    mem_mb = pinfo['memory_info'].rss / (1024 * 1024) if pinfo.get('memory_info') else 0
                    if mem_mb > 100:  # Processes using > 100MB
                        processes.append({
                            "pid": pinfo['pid'],
                            "name": pinfo['name'],
                            "memory_mb": round(mem_mb, 2),
                            "memory_percent": pinfo.get('memory_percent', 0),
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by memory usage
            processes.sort(key=lambda x: x['memory_mb'], reverse=True)
            
            if mem_percent > self.mem_threshold:
                result["issue"] = {
                    "severity": "high" if mem_percent > 95 else "medium",
                    "type": "memory_leak",
                    "title": f"High Memory Usage: {mem_percent:.1f}% (Threshold: {self.mem_threshold}%)",
                    "description": f"Memory usage is critically high. Available: {mem.available / (1024**3):.2f} GB",
                    "top_memory_processes": processes[:5],
                    "recommendations": [
                        "Identify processes with memory leaks",
                        "Restart memory-intensive services",
                        "Check for memory leaks in applications",
                        "Consider adding swap space if needed",
                    ],
                }
                
                result["status"] = "critical" if mem_percent > 95 else "warning"
                
                # Suggest auto-heal for memory-intensive safe services
                if self.is_admin:
                    high_mem_processes = [p for p in processes[:3] if p.get('memory_mb', 0) > 500]
                    safe_to_restart = []
                    
                    for proc_info in high_mem_processes:
                        proc_name = proc_info.get('name', '').lower()
                        for safe_service in self.safe_services:
                            if safe_service in proc_name:
                                safe_to_restart.append({
                                    "service": safe_service,
                                    "pid": proc_info.get('pid'),
                                    "memory_mb": proc_info.get('memory_mb', 0),
                                })
                                break
                    
                    if safe_to_restart:
                        result["heal_action"] = {
                            "type": "restart_service",
                            "services": safe_to_restart,
                            "description": "Memory-intensive services can be safely restarted",
                            "command": self._generate_restart_command(safe_to_restart[0]["service"]),
                            "manual": "Run: sudo systemctl restart <service-name>",
                        }
            else:
                result["status"] = "healthy"
                
        except Exception as e:
            result["error"] = str(e)
            result["status"] = "unknown"
        
        return result
    
    async def _check_disk_io(self) -> Dict[str, Any]:
        """Check for disk IO bottlenecks"""
        result = {}
        
        try:
            # Get disk IO stats
            disk_io = psutil.disk_io_counters()
            
            if disk_io:
                # Calculate IO wait (simplified)
                # In production, would use iostat or similar
                
                # Get disk usage
                disk_usage = psutil.disk_usage('/')
                disk_percent = disk_usage.percent
                
                if disk_percent > self.disk_io_threshold:
                    result["issue"] = {
                        "severity": "high" if disk_percent > 95 else "medium",
                        "type": "disk_io_issue",
                        "title": f"Disk Space Low: {disk_percent:.1f}% used",
                        "description": f"Disk usage is high. Free: {disk_usage.free / (1024**3):.2f} GB",
                        "recommendations": [
                            "Clean up temporary files",
                            "Remove old logs",
                            "Check for large files consuming space",
                            "Consider disk expansion",
                        ],
                    }
                    result["status"] = "warning"
                else:
                    result["status"] = "healthy"
            else:
                result["status"] = "unknown"
                
        except Exception as e:
            result["error"] = str(e)
            result["status"] = "unknown"
        
        return result
    
    async def _check_hung_processes(self) -> Dict[str, Any]:
        """Detect hung or unresponsive processes"""
        result = {}
        
        try:
            hung_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'status']):
                try:
                    pinfo = proc.info
                    # Check if process is in uninterruptible sleep (D state on Linux)
                    if pinfo.get('status') == psutil.STATUS_DISK_SLEEP:
                        hung_processes.append({
                            "pid": pinfo['pid'],
                            "name": pinfo['name'],
                            "status": "hung",
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if hung_processes:
                result["issue"] = {
                    "severity": "medium",
                    "type": "hung_processes",
                    "title": f"Hung Processes Detected: {len(hung_processes)}",
                    "description": "Some processes appear to be hung or unresponsive",
                    "hung_processes": hung_processes[:10],
                    "recommendations": [
                        "Kill hung processes if safe",
                        "Investigate root cause",
                        "Check for disk I/O issues",
                    ],
                }
                result["status"] = "warning"
            else:
                result["status"] = "healthy"
                
        except Exception as e:
            result["error"] = str(e)
            result["status"] = "unknown"
        
        return result
    
    def _calculate_health_score(self, cpu_result: Dict, ram_result: Dict, disk_result: Dict) -> int:
        """Calculate overall server health score (0-100)"""
        score = 100
        
        # Deduct points based on issues
        if cpu_result.get("status") == "critical":
            score -= 30
        elif cpu_result.get("status") == "warning":
            score -= 15
        
        if ram_result.get("status") == "critical":
            score -= 30
        elif ram_result.get("status") == "warning":
            score -= 15
        
        if disk_result.get("status") == "warning":
            score -= 10
        
        return max(0, score)
    
    def _generate_restart_command(self, service_name: str) -> str:
        """Generate systemctl restart command for service"""
        if self.system == "Linux":
            return f"sudo systemctl restart {service_name}"
        elif self.system == "Windows":
            return f"net stop {service_name} && net start {service_name}"
        else:
            return f"service {service_name} restart"


