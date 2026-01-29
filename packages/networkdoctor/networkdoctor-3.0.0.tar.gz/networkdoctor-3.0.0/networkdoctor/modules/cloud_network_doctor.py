"""
Cloud Infrastructure Expert for NetworkDoctor
"""
import asyncio
import aiohttp
import json
from typing import List, Dict, Any
from datetime import datetime


class CloudNetworkDoctor:
    """Cloud network diagnosis expert"""
    
    def __init__(self):
        self.name = "Cloud Network Doctor"
        # Cloud provider detection patterns
        self.cloud_patterns = {
            "aws": {
                "domains": ["amazonaws.com", "aws.amazon.com"],
                "ips": ["3.", "52.", "54.", "18.", "185."],  # AWS IP ranges
                "headers": ["x-amzn-requestid", "x-amz-cf-id"],
            },
            "azure": {
                "domains": ["azure.com", "cloudapp.net", "blob.core.windows.net"],
                "ips": ["20.", "40.", "52.", "104.", "13."],  # Azure IP ranges
                "headers": ["x-ms-request-id", "x-ms-version"],
            },
            "gcp": {
                "domains": ["googleapis.com", "googleusercontent.com", "gcp.gvt2.com"],
                "ips": ["34.", "35.", "64.", "108.", "142."],  # GCP IP ranges
                "headers": ["x-google-backends", "x-guploader-uploadid"],
            },
        }
    
    async def diagnose(self, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Diagnose cloud network issues with real cloud provider detection.
        
        Args:
            scan_results: Results from network scanner
            
        Returns:
            Diagnosis results with real cloud network analysis
        """
        issues = []
        findings = []
        
        for result in scan_results:
            target = result.get("target", "")
            
            # Detect cloud provider
            cloud_info = await self._detect_cloud_provider(target)
            findings.append(cloud_info)
            
            # Test cloud-specific connectivity
            if cloud_info.get("provider"):
                await self._test_cloud_connectivity(target, cloud_info, issues, findings)
                
                # Test cloud service availability
                await self._test_cloud_services(target, cloud_info, issues, findings)
                
                # Test cloud performance metrics
                await self._test_cloud_performance(target, cloud_info, issues, findings)
        
        return {
            "doctor": "cloud",
            "status": "completed",
            "issues": issues,
            "findings": findings,
            "summary": {
                "total_issues": len(issues),
                "cloud_targets_detected": len([f for f in findings if f.get("provider")]),
            },
        }
    
    async def _detect_cloud_provider(self, target: str) -> Dict[str, Any]:
        """Detect which cloud provider hosts the target"""
        cloud_info = {
            "target": target,
            "provider": None,
            "confidence": 0,
            "evidence": [],
        }
        
        try:
            # Check domain patterns
            for provider, patterns in self.cloud_patterns.items():
                confidence = 0
                evidence = []
                
                # Check domain
                for domain in patterns["domains"]:
                    if domain in target.lower():
                        confidence += 40
                        evidence.append(f"Domain matches {provider.upper()}: {domain}")
                
                # Check via HTTP headers
                try:
                    url = f"https://{target}"
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                            headers = dict(response.headers)
                            
                            for header in patterns["headers"]:
                                if header.lower() in [h.lower() for h in headers.keys()]:
                                    confidence += 30
                                    evidence.append(f"Header indicates {provider.upper()}: {header}")
                            
                            # Check server header for cloud signatures
                            server = headers.get("Server", "").lower()
                            if any(cloud_sig in server for cloud_sig in ["gws", "gse", "google"]):
                                if provider == "gcp":
                                    confidence += 20
                                    evidence.append("Server header indicates Google Cloud")
                            elif any(cloud_sig in server for cloud_sig in ["aws", "amazon"]):
                                if provider == "aws":
                                    confidence += 20
                                    evidence.append("Server header indicates AWS")
                            elif any(cloud_sig in server for cloud_sig in ["azure", "microsoft"]):
                                if provider == "azure":
                                    confidence += 20
                                    evidence.append("Server header indicates Azure")
                
                except:
                    pass
                
                if confidence > cloud_info["confidence"]:
                    cloud_info = {
                        "target": target,
                        "provider": provider,
                        "confidence": confidence,
                        "evidence": evidence,
                    }
        
        except:
            pass
        
        return cloud_info
    
    async def _test_cloud_connectivity(self, target: str, cloud_info: Dict, issues: List, findings: List):
        """Test cloud-specific connectivity"""
        provider = cloud_info.get("provider")
        
        try:
            url = f"https://{target}"
            
            # Test connectivity with cloud-specific considerations
            async with aiohttp.ClientSession() as session:
                start_time = asyncio.get_event_loop().time()
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    end_time = asyncio.get_event_loop().time()
                    response_time = (end_time - start_time) * 1000
                    
                    findings.append({
                        "target": target,
                        "provider": provider,
                        "connectivity_test": "completed",
                        "response_time_ms": round(response_time, 2),
                        "status_code": response.status,
                        "cloud_optimized": response_time < 1000,  # Cloud should be fast
                    })
                    
                    # Cloud-specific performance expectations
                    if provider == "aws" and response_time > 2000:
                        issues.append({
                            "id": f"cloud_slow_aws_{target}",
                            "type": "cloud",
                            "severity": "medium",
                            "title": "AWS Service Slow Response",
                            "description": f"AWS service responding in {response_time:.1f}ms",
                            "impact": "Poor cloud performance",
                            "solutions": [
                                {
                                    "action": "Check AWS service health",
                                    "command": "https://status.aws.amazon.com/",
                                },
                                {
                                    "action": "Check AWS CloudWatch metrics",
                                    "command": "aws cloudwatch get-metric-statistics",
                                },
                            ],
                        })
                    elif provider == "azure" and response_time > 3000:
                        issues.append({
                            "id": f"cloud_slow_azure_{target}",
                            "type": "cloud",
                            "severity": "medium",
                            "title": "Azure Service Slow Response",
                            "description": f"Azure service responding in {response_time:.1f}ms",
                            "impact": "Poor cloud performance",
                            "solutions": [
                                {
                                    "action": "Check Azure status",
                                    "command": "https://status.azure.com/",
                                },
                                {
                                    "action": "Check Azure Monitor",
                                    "command": "az monitor metrics list",
                                },
                            ],
                        })
                    elif provider == "gcp" and response_time > 1500:
                        issues.append({
                            "id": f"cloud_slow_gcp_{target}",
                            "type": "cloud",
                            "severity": "medium",
                            "title": "GCP Service Slow Response",
                            "description": f"GCP service responding in {response_time:.1f}ms",
                            "impact": "Poor cloud performance",
                            "solutions": [
                                {
                                    "action": "Check GCP status",
                                    "command": "https://status.cloud.google.com/",
                                },
                                {
                                    "action": "Check Cloud Monitoring",
                                    "command": "gcloud monitoring metrics list",
                                },
                            ],
                        })
        
        except Exception:
            issues.append({
                "id": f"cloud_no_connectivity_{target}",
                "type": "cloud",
                "severity": "high",
                "title": "Cloud Service Unreachable",
                "description": f"Cannot connect to cloud service {target}",
                "impact": "Cloud service is down or blocked",
                "solutions": [
                    {
                        "action": "Check cloud provider status",
                        "command": f"Check {provider.upper()} status dashboard",
                    },
                    {
                        "action": "Verify network connectivity",
                        "command": "traceroute " + target,
                    },
                ],
            })
    
    async def _test_cloud_services(self, target: str, cloud_info: Dict, issues: List, findings: List):
        """Test cloud-specific services"""
        provider = cloud_info.get("provider")
        
        # Test provider-specific health endpoints
        health_endpoints = {
            "aws": ["https://status.aws.amazon.com/health.json"],
            "azure": ["https://status.azure.com/api/health"],
            "gcp": ["https://status.cloud.google.com/api/v1/instances"],
        }
        
        if provider in health_endpoints:
            for endpoint in health_endpoints[provider]:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=5)) as response:
                            if response.status == 200:
                                try:
                                    health_data = await response.json()
                                    findings.append({
                                        "target": target,
                                        "provider": provider,
                                        "health_check": "passed",
                                        "health_endpoint": endpoint,
                                        "health_data": health_data,
                                    })
                                except:
                                    findings.append({
                                        "target": target,
                                        "provider": provider,
                                        "health_check": "passed",
                                        "health_endpoint": endpoint,
                                    })
                except:
                    issues.append({
                        "id": f"cloud_health_fail_{provider}",
                        "type": "cloud",
                        "severity": "medium",
                        "title": f"{provider.upper()} Health Check Failed",
                        "description": f"Cannot reach {provider.upper()} health endpoint",
                        "impact": "Unable to verify cloud provider status",
                        "solutions": [
                            {
                                "action": "Check internet connectivity",
                                "command": "ping 8.8.8.8",
                            },
                        ],
                    })
    
    async def _test_cloud_performance(self, target: str, cloud_info: Dict, issues: List, findings: List):
        """Test cloud performance metrics"""
        provider = cloud_info.get("provider")
        
        try:
            url = f"https://{target}"
            
            # Test multiple requests for performance consistency
            response_times = []
            for _ in range(5):
                try:
                    start_time = asyncio.get_event_loop().time()
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                            end_time = asyncio.get_event_loop().time()
                            response_times.append((end_time - start_time) * 1000)
                except:
                    pass
                
                await asyncio.sleep(0.2)
            
            if response_times:
                avg_time = sum(response_times) / len(response_times)
                min_time = min(response_times)
                max_time = max(response_times)
                variance = max_time - min_time
                
                findings.append({
                    "target": target,
                    "provider": provider,
                    "performance_test": "completed",
                    "avg_response_time_ms": round(avg_time, 2),
                    "min_response_time_ms": round(min_time, 2),
                    "max_response_time_ms": round(max_time, 2),
                    "variance_ms": round(variance, 2),
                    "reliability": "high" if variance < 100 else "medium" if variance < 500 else "low",
                })
                
                # Check for performance issues
                if avg_time > 5000:  # > 5 seconds
                    issues.append({
                        "id": f"cloud_poor_performance_{target}",
                        "type": "cloud",
                        "severity": "high",
                        "title": "Poor Cloud Performance",
                        "description": f"Cloud service average response: {avg_time:.1f}ms",
                        "impact": "Severely degraded cloud service",
                        "solutions": [
                            {
                                "action": "Check cloud resource limits",
                                "command": f"Check {provider.upper()} quotas and limits",
                            },
                            {
                                "action": "Scale cloud resources",
                                "command": f"Upgrade {provider.upper()} service tier",
                            },
                        ],
                    })
        
        except:
            pass








