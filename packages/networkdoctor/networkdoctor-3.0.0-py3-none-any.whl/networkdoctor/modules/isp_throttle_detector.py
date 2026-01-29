"""
ISP Problem Detector - Detect ISP Throttling and Provide Evidence

"""
import asyncio
import time
import statistics
from typing import List, Dict, Any, Optional
import aiohttp
from datetime import datetime


class ISPThrottleDetector:
    """Detect ISP throttling and provide evidence for complaints"""
    
    def __init__(self):
        self.name = "ISP Throttle Detector"
        self.test_servers = [
            "http://speedtest.tele2.net/10MB.zip",
            "http://ipv4.download.thinkbroadband.com/10MB.zip",
            "https://proof.ovh.net/files/10Mb.dat",
        ]
    
    async def diagnose(self, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect ISP throttling issues.
        
        Args:
            scan_results: Results from network scan
            
        Returns:
            Diagnosis results with throttling evidence
        """
        issues = []
        findings = []
        evidence = []
        
        # Test connection speed at different times
        speed_tests = await self._perform_speed_tests()
        
        # Analyze patterns
        throttling_detected = self._analyze_throttling_patterns(speed_tests)
        
        if throttling_detected:
            issues.append({
                "severity": "high",
                "type": "isp_throttling",
                "title": "ISP Speed Throttling Detected",
                "description": "Your ISP appears to be throttling your connection speed",
                "evidence": speed_tests,
            })
            
            # Generate complaint template
            complaint_template = self._generate_complaint_template(speed_tests)
            evidence.append({
                "type": "complaint_template",
                "content": complaint_template,
            })
            
            findings.append({
                "finding": "isp_throttling",
                "confidence": self._calculate_confidence(speed_tests),
                "recommendations": [
                    "Document all speed test results",
                    "Contact ISP with evidence",
                    "File complaint with regulatory body if needed",
                    "Consider switching ISPs if problem persists",
                ],
            })
        
        # Detect packet shaping
        packet_shaping = await self._detect_packet_shaping()
        if packet_shaping:
            issues.append({
                "severity": "medium",
                "type": "packet_shaping",
                "title": "ISP Packet Shaping Detected",
                "description": "Your ISP may be prioritizing certain types of traffic",
                "evidence": packet_shaping,
            })
        
        return {
            "doctor": "isp_throttle",
            "status": "completed",
            "issues": issues,
            "findings": findings,
            "evidence": evidence,
            "summary": {
                "throttling_detected": throttling_detected,
                "packet_shaping_detected": bool(packet_shaping),
                "total_issues": len(issues),
                "confidence_score": self._calculate_confidence(speed_tests) if speed_tests else 0,
            },
        }
    
    async def _perform_speed_tests(self) -> List[Dict[str, Any]]:
        """Perform multiple speed tests to detect throttling patterns"""
        results = []
        
        # Test with different file sizes to detect throttling patterns
        test_configs = [
            {"url": "http://speedtest.tele2.net/1MB.zip", "size_mb": 1, "name": "1MB Test"},
            {"url": "http://speedtest.tele2.net/10MB.zip", "size_mb": 10, "name": "10MB Test"},
            {"url": "http://ipv4.download.thinkbroadband.com/5MB.zip", "size_mb": 5, "name": "5MB Alternative"},
        ]
        
        for config in test_configs[:3]:  # Test 3 different sizes
            try:
                # Test multiple times to check consistency
                speeds = []
                for attempt in range(2):
                    start_time = time.time()
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            config["url"], 
                            timeout=aiohttp.ClientTimeout(total=30)
                        ) as response:
                            data = await response.read()
                            end_time = time.time()
                            
                            duration = end_time - start_time
                            actual_size_mb = len(data) / (1024 * 1024)
                            speed_mbps = (actual_size_mb * 8) / duration if duration > 0 else 0
                            speeds.append(speed_mbps)
                    
                    await asyncio.sleep(1)  # Wait between attempts
                
                avg_speed = statistics.mean(speeds) if speeds else 0
                speed_variance = statistics.stdev(speeds) if len(speeds) > 1 else 0
                
                results.append({
                    "server": config["url"],
                    "test_name": config["name"],
                    "expected_size_mb": config["size_mb"],
                    "actual_size_mb": round(actual_size_mb, 2),
                    "timestamp": datetime.now().isoformat(),
                    "duration_sec": round(duration, 2),
                    "speed_mbps": round(avg_speed, 2),
                    "speed_variance": round(speed_variance, 3),
                    "attempts": len(speeds),
                    "status": "success",
                })
                
            except Exception as e:
                results.append({
                    "server": config["url"],
                    "test_name": config["name"],
                    "timestamp": datetime.now().isoformat(),
                    "status": "failed",
                    "error": str(e),
                })
            
            await asyncio.sleep(2)  # Wait between different test servers
        
        return results
    
    def _analyze_throttling_patterns(self, speed_tests: List[Dict[str, Any]]) -> bool:
        """Analyze speed test results for throttling patterns"""
        if not speed_tests or len(speed_tests) < 2:
            return False
        
        successful_tests = [t for t in speed_tests if t.get("status") == "success"]
        if len(successful_tests) < 2:
            return False
        
        speeds = [t["speed_mbps"] for t in successful_tests]
        avg_speed = statistics.mean(speeds)
        std_dev = statistics.stdev(speeds) if len(speeds) > 1 else 0
        
        # Enhanced throttling indicators:
        # 1. Large variance in speeds (unstable connection)
        # 2. Very low speeds compared to typical broadband
        # 3. Speeds decreasing with larger file sizes (throttling pattern)
        # 4. High variance within individual tests
        
        # Check for large variance (coefficient of variation > 0.4)
        cv = (std_dev / avg_speed) if avg_speed > 0 else 0
        if cv > 0.4:
            return True
        
        # Check for suspiciously low speeds (< 2 Mbps on typical broadband)
        if avg_speed < 2.0:
            return True
        
        # Check for size-based throttling (larger files significantly slower)
        if len(successful_tests) >= 2:
            # Sort by expected size
            sorted_tests = sorted(successful_tests, key=lambda x: x.get("expected_size_mb", 0))
            small_file_speed = sorted_tests[0]["speed_mbps"]
            large_file_speed = sorted_tests[-1]["speed_mbps"]
            
            # If large file is significantly slower (>30% difference), possible throttling
            if large_file_speed > 0 and (small_file_speed / large_file_speed) > 1.3:
                return True
        
        # Check for high variance in individual test attempts
        high_variance_tests = [t for t in successful_tests if t.get("speed_variance", 0) > 1.0]
        if len(high_variance_tests) >= 2:
            return True
        
        return False
    
    def _calculate_confidence(self, speed_tests: List[Dict[str, Any]]) -> int:
        """Calculate confidence score for throttling detection (0-100)"""
        if not speed_tests:
            return 0
        
        successful_tests = [t for t in speed_tests if t.get("status") == "success"]
        if len(successful_tests) < 2:
            return 30
        
        speeds = [t["speed_mbps"] for t in successful_tests]
        avg_speed = statistics.mean(speeds)
        std_dev = statistics.stdev(speeds) if len(speeds) > 1 else 0
        cv = (std_dev / avg_speed) if avg_speed > 0 else 0
        
        confidence = 50  # Base confidence
        
        # Increase confidence based on indicators
        if cv > 0.5:
            confidence += 20
        if avg_speed < 1.0:
            confidence += 20
        if len(successful_tests) >= 3:
            confidence += 10
        
        return min(confidence, 95)
    
    async def _detect_packet_shaping(self) -> Optional[Dict[str, Any]]:
        """Detect packet shaping by analyzing latency patterns"""
        # This would require more advanced testing
        # For now, return None (placeholder for future implementation)
        return None
    
    def _generate_complaint_template(self, speed_tests: List[Dict[str, Any]]) -> str:
        """Generate ISP complaint template with evidence"""
        successful_tests = [t for t in speed_tests if t.get("status") == "success"]
        
        template = f"""
ISP COMPLAINT TEMPLATE
Generated by NetworkDoctor (created by frankvena25)
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUBJECT: Internet Speed Throttling Complaint

Dear [ISP Name],

I am writing to file a formal complaint regarding inconsistent internet speeds on my connection.

EVIDENCE OF THROTTLING:
"""
        
        for i, test in enumerate(successful_tests, 1):
            template += f"""
Test {i} ({test.get('timestamp', 'N/A')}):
- Server: {test.get('server', 'N/A')}
- Download Speed: {test.get('speed_mbps', 0):.2f} Mbps
- File Size: {test.get('size_mb', 0):.2f} MB
- Duration: {test.get('duration_sec', 0):.2f} seconds
"""
        
        template += """
CONCERNS:
- My connection speed is inconsistent
- Speed tests show significant variation
- This suggests traffic shaping or throttling may be occurring

REQUESTED ACTIONS:
1. Investigation into why speeds are inconsistent
2. Explanation of any traffic management policies affecting my connection
3. Resolution plan to provide consistent speeds as advertised

I have documented all tests and can provide additional evidence if needed.

Sincerely,
[Your Name]
[Account Number: XXX-XXX-XXX]
"""
        
        return template

