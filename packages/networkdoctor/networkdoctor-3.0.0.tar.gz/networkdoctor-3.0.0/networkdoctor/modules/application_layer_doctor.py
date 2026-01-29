"""
HTTP/API Layer Expert for NetworkDoctor
"""
import asyncio
import aiohttp
from typing import List, Dict, Any
from datetime import datetime


class ApplicationLayerDoctor:
    """Application layer diagnosis expert"""
    
    async def diagnose(self, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Diagnose application layer issues with real HTTP/API testing.
        
        Args:
            scan_results: Results from network scanner
            
        Returns:
            Diagnosis results with real application layer analysis
        """
        issues = []
        findings = []
        
        for result in scan_results:
            target = result.get("target", "")
            
            # Test HTTP/HTTPS connectivity and response
            await self._test_http_connectivity(target, issues, findings)
            
            # Test API endpoints if available
            await self._test_api_endpoints(target, issues, findings)
            
            # Test application performance
            await self._test_application_performance(target, issues, findings)
        
        return {
            "doctor": "application",
            "status": "completed",
            "issues": issues,
            "findings": findings,
            "summary": {
                "total_issues": len(issues),
                "services_tested": len(findings),
            },
        }
    
    async def _test_http_connectivity(self, target: str, issues: List, findings: List):
        """Test HTTP/HTTPS connectivity and response analysis"""
        try:
            # Test both HTTP and HTTPS
            for protocol in ["http", "https"]:
                url = f"{protocol}://{target}"
                
                async with aiohttp.ClientSession() as session:
                    try:
                        start_time = asyncio.get_event_loop().time()
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                            end_time = asyncio.get_event_loop().time()
                            response_time = (end_time - start_time) * 1000
                            
                            findings.append({
                                "target": target,
                                "protocol": protocol,
                                "status_code": response.status,
                                "response_time_ms": round(response_time, 2),
                                "content_type": response.headers.get("Content-Type", ""),
                                "server": response.headers.get("Server", ""),
                                "content_length": response.headers.get("Content-Length", "0"),
                            })
                            
                            # Check for HTTP issues
                            if response.status >= 400:
                                severity = "high" if response.status >= 500 else "medium"
                                issues.append({
                                    "id": f"app_http_error_{target}_{protocol}",
                                    "type": "application",
                                    "severity": severity,
                                    "title": f"HTTP Error {response.status}",
                                    "description": f"{protocol}://{target} returned HTTP {response.status}",
                                    "impact": "Application is not responding correctly",
                                    "solutions": [
                                        {
                                            "action": "Check application logs",
                                            "command": f"Check logs for {target}",
                                        },
                                        {
                                            "action": "Verify service status",
                                            "command": f"systemctl status {target.split('.')[0]}",
                                        },
                                    ],
                                })
                            
                            # Check response time
                            if response_time > 2000:  # > 2 seconds
                                issues.append({
                                    "id": f"app_slow_response_{target}",
                                    "type": "application",
                                    "severity": "medium",
                                    "title": "Slow Application Response",
                                    "description": f"Application response time is {response_time:.1f}ms",
                                    "impact": "Poor user experience",
                                    "solutions": [
                                        {
                                            "action": "Optimize application code",
                                            "command": "Profile application performance",
                                        },
                                        {
                                            "action": "Check server resources",
                                            "command": "top && htop",
                                        },
                                    ],
                                })
                    
                    except asyncio.TimeoutError:
                        issues.append({
                            "id": f"app_timeout_{target}_{protocol}",
                            "type": "application",
                            "severity": "high",
                            "title": "Application Timeout",
                            "description": f"{protocol}://{target} timed out after 10 seconds",
                            "impact": "Application is unreachable or very slow",
                            "solutions": [
                                {
                                    "action": "Check if service is running",
                                    "command": f"netstat -tlnp | grep :{'443' if protocol == 'https' else '80'}",
                                },
                                {
                                    "action": "Check firewall",
                                    "command": f"iptables -L -n | grep :{'443' if protocol == 'https' else '80'}",
                                },
                            ],
                        })
                    except Exception as e:
                        # Connection failed
                        pass
                        
        except Exception:
            pass
    
    async def _test_api_endpoints(self, target: str, issues: List, findings: List):
        """Test common API endpoints"""
        common_endpoints = [
            "/api/health",
            "/health",
            "/status",
            "/ping",
            "/api/v1/status",
        ]
        
        base_url = f"https://{target}"
        
        for endpoint in common_endpoints:
            try:
                url = base_url + endpoint
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            findings.append({
                                "target": target,
                                "api_endpoint": endpoint,
                                "status": "available",
                                "response_time_ms": "fast",
                            })
                            
                            # Check if health endpoint provides useful info
                            if endpoint in ["/health", "/api/health", "/status"]:
                                try:
                                    data = await response.json()
                                    if isinstance(data, dict):
                                        findings[-1]["health_data"] = data
                                except:
                                    pass
                        break  # Stop at first working endpoint
                        
            except Exception:
                continue
    
    async def _test_application_performance(self, target: str, issues: List, findings: List):
        """Test application performance metrics"""
        try:
            url = f"https://{target}"
            
            # Test multiple requests to check consistency
            response_times = []
            for _ in range(3):
                try:
                    start_time = asyncio.get_event_loop().time()
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                            end_time = asyncio.get_event_loop().time()
                            response_times.append((end_time - start_time) * 1000)
                except:
                    pass
                
                await asyncio.sleep(0.5)
            
            if response_times:
                avg_time = sum(response_times) / len(response_times)
                variance = max(response_times) - min(response_times)
                
                findings.append({
                    "target": target,
                    "performance_test": "completed",
                    "avg_response_time_ms": round(avg_time, 2),
                    "min_response_time_ms": round(min(response_times), 2),
                    "max_response_time_ms": round(max(response_times), 2),
                    "variance_ms": round(variance, 2),
                    "consistency": "good" if variance < 100 else "poor",
                })
                
                # Check for inconsistent performance
                if variance > 500:  # > 0.5 seconds variance
                    issues.append({
                        "id": f"app_inconsistent_{target}",
                        "type": "application",
                        "severity": "medium",
                        "title": "Inconsistent Application Performance",
                        "description": f"Response times vary by {variance:.1f}ms",
                        "impact": "Unpredictable user experience",
                        "solutions": [
                            {
                                "action": "Check server load",
                                "command": "uptime && free -m",
                            },
                            {
                                "action": "Monitor application metrics",
                                "command": "Enable application performance monitoring",
                            },
                        ],
                    })
        
        except Exception:
            pass








