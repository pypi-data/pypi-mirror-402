"""
Internet Quality Score - Score for Gaming, Streaming, Zoom, Cloud Work

"""
import asyncio
import time
import statistics
from typing import List, Dict, Any
import aiohttp
from datetime import datetime


class InternetQualityScore:
    """Calculate quality scores for different internet usage scenarios"""
    
    def __init__(self):
        self.name = "Internet Quality Score"
        self.test_urls = {
            "download": "http://ipv4.download.thinkbroadband.com/10MB.zip",
            "latency": ["8.8.8.8", "1.1.1.1", "208.67.222.222"],
        }
    
    async def diagnose(self, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate quality scores for gaming, streaming, Zoom, cloud work.
        
        Args:
            scan_results: Results from network scan
            
        Returns:
            Quality scores for different use cases
        """
        issues = []
        findings = []
        
        # Perform network quality tests
        download_speed = await self._test_download_speed()
        latency_results = await self._test_latency()
        jitter_results = await self._calculate_jitter(latency_results)
        packet_loss = await self._test_packet_loss()
        
        # Calculate scores for each use case
        gaming_score = self._calculate_gaming_score(latency_results, jitter_results, packet_loss)
        streaming_score = self._calculate_streaming_score(download_speed, latency_results)
        zoom_score = self._calculate_zoom_score(latency_results, jitter_results, download_speed)
        cloud_score = self._calculate_cloud_score(download_speed, latency_results, packet_loss)
        
        # Overall score
        overall_score = (gaming_score + streaming_score + zoom_score + cloud_score) / 4
        
        # Generate findings
        findings.append({
            "finding": "internet_quality_assessment",
            "overall_score": round(overall_score, 1),
            "gaming_score": round(gaming_score, 1),
            "streaming_score": round(streaming_score, 1),
            "zoom_score": round(zoom_score, 1),
            "cloud_score": round(cloud_score, 1),
        })
        
        # Add issues if scores are low
        if overall_score < 50:
            issues.append({
                "severity": "high",
                "type": "poor_internet_quality",
                "title": f"Poor Internet Quality: {overall_score:.1f}/100",
                "description": "Overall internet quality is below acceptable standards",
                "recommendations": [
                    "Check with ISP for service issues",
                    "Upgrade internet plan if possible",
                    "Use wired connection instead of WiFi",
                    "Check for network congestion",
                ],
            })
        
        # Detailed metrics
        metrics = {
            "download_speed_mbps": download_speed,
            "average_latency_ms": statistics.mean(latency_results) if latency_results else 0,
            "jitter_ms": jitter_results,
            "packet_loss_percent": packet_loss,
        }
        
        return {
            "doctor": "internet_quality",
            "status": "completed",
            "issues": issues,
            "findings": findings,
            "scores": {
                "overall": round(overall_score, 1),
                "gaming": round(gaming_score, 1),
                "streaming": round(streaming_score, 1),
                "zoom": round(zoom_score, 1),
                "cloud_work": round(cloud_score, 1),
            },
            "metrics": metrics,
            "recommendations": self._generate_recommendations(
                gaming_score, streaming_score, zoom_score, cloud_score
            ),
            "summary": {
                "overall_quality": self._get_quality_label(overall_score),
                "best_for": self._get_best_use_case(gaming_score, streaming_score, zoom_score, cloud_score),
                "needs_improvement": self._get_improvement_areas(gaming_score, streaming_score, zoom_score, cloud_score),
            },
        }
    
    async def _test_download_speed(self) -> float:
        """Test download speed in Mbps"""
        try:
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.test_urls["download"],
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    data = await response.read()
                    end_time = time.time()
                    
                    duration = end_time - start_time
                    size_mb = len(data) / (1024 * 1024)
                    speed_mbps = (size_mb * 8) / duration if duration > 0 else 0
                    
                    return round(speed_mbps, 2)
        except Exception:
            return 0.0
    
    async def _test_latency(self) -> List[float]:
        """Test latency to multiple servers"""
        latencies = []
        
        for host in self.test_urls["latency"]:
            try:
                start_time = time.time()
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"http://{host}",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        await response.read()
                        end_time = time.time()
                        latency_ms = (end_time - start_time) * 1000
                        latencies.append(round(latency_ms, 2))
            except Exception:
                pass
            await asyncio.sleep(0.5)
        
        return latencies
    
    def _calculate_jitter(self, latencies: List[float]) -> float:
        """Calculate jitter (variation in latency)"""
        if len(latencies) < 2:
            return 0.0
        
        differences = []
        for i in range(1, len(latencies)):
            differences.append(abs(latencies[i] - latencies[i-1]))
        
        return round(statistics.mean(differences) if differences else 0.0, 2)
    
    async def _test_packet_loss(self) -> float:
        """Estimate packet loss (simplified test)"""
        # In production, would use actual packet loss test
        # This is a simplified version
        successful = 0
        total = 10
        
        for _ in range(total):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        "http://8.8.8.8",
                        timeout=aiohttp.ClientTimeout(total=2)
                    ) as response:
                        await response.read()
                        successful += 1
            except Exception:
                pass
            await asyncio.sleep(0.2)
        
        packet_loss = ((total - successful) / total) * 100
        return round(packet_loss, 2)
    
    def _calculate_gaming_score(self, latency: List[float], jitter: float, packet_loss: float) -> float:
        """Calculate gaming quality score (0-100)"""
        if not latency:
            return 0.0
        
        avg_latency = statistics.mean(latency)
        score = 100.0
        
        # Latency scoring (lower is better)
        # < 20ms = excellent (100)
        # 20-50ms = good (90-80)
        # 50-100ms = fair (70-60)
        # > 100ms = poor (< 60)
        if avg_latency < 20:
            latency_score = 100
        elif avg_latency < 50:
            latency_score = 90 - ((avg_latency - 20) / 30) * 10
        elif avg_latency < 100:
            latency_score = 70 - ((avg_latency - 50) / 50) * 10
        else:
            latency_score = max(0, 60 - ((avg_latency - 100) / 100) * 30)
        
        # Jitter scoring (lower is better)
        # < 10ms = excellent (100)
        # 10-30ms = good (90-70)
        # > 30ms = poor (< 70)
        if jitter < 10:
            jitter_score = 100
        elif jitter < 30:
            jitter_score = 90 - ((jitter - 10) / 20) * 20
        else:
            jitter_score = max(0, 70 - ((jitter - 30) / 30) * 40)
        
        # Packet loss scoring (lower is better)
        # < 1% = excellent (100)
        # 1-3% = good (90-70)
        # > 3% = poor (< 70)
        if packet_loss < 1:
            loss_score = 100
        elif packet_loss < 3:
            loss_score = 90 - ((packet_loss - 1) / 2) * 20
        else:
            loss_score = max(0, 70 - ((packet_loss - 3) / 3) * 50)
        
        # Weighted average
        final_score = (latency_score * 0.5) + (jitter_score * 0.3) + (loss_score * 0.2)
        return round(final_score, 1)
    
    def _calculate_streaming_score(self, download_speed: float, latency: List[float]) -> float:
        """Calculate streaming quality score (0-100)"""
        score = 100.0
        
        # Download speed scoring
        # > 25 Mbps = excellent (100) - 4K streaming
        # 10-25 Mbps = good (90-80) - HD streaming
        # 5-10 Mbps = fair (70-60) - SD streaming
        # < 5 Mbps = poor (< 60)
        if download_speed > 25:
            speed_score = 100
        elif download_speed > 10:
            speed_score = 80 + ((download_speed - 10) / 15) * 20
        elif download_speed > 5:
            speed_score = 60 + ((download_speed - 5) / 5) * 10
        else:
            speed_score = max(0, 60 - ((5 - download_speed) / 5) * 40)
        
        # Latency matters less for streaming but still considered
        if latency:
            avg_latency = statistics.mean(latency)
            latency_score = 100 if avg_latency < 100 else max(70, 100 - ((avg_latency - 100) / 100) * 30)
        else:
            latency_score = 70
        
        # Weighted: speed 80%, latency 20%
        final_score = (speed_score * 0.8) + (latency_score * 0.2)
        return round(final_score, 1)
    
    def _calculate_zoom_score(self, latency: List[float], jitter: float, download_speed: float) -> float:
        """Calculate video conferencing (Zoom) quality score (0-100)"""
        score = 100.0
        
        # Latency is critical for video calls
        if latency:
            avg_latency = statistics.mean(latency)
            if avg_latency < 50:
                latency_score = 100
            elif avg_latency < 150:
                latency_score = 90 - ((avg_latency - 50) / 100) * 20
            else:
                latency_score = max(0, 70 - ((avg_latency - 150) / 100) * 50)
        else:
            latency_score = 50
        
        # Jitter is very important for video calls
        if jitter < 20:
            jitter_score = 100
        elif jitter < 50:
            jitter_score = 90 - ((jitter - 20) / 30) * 20
        else:
            jitter_score = max(0, 70 - ((jitter - 50) / 50) * 50)
        
        # Download speed (needs less but still important)
        if download_speed > 3:
            speed_score = 100
        else:
            speed_score = max(0, (download_speed / 3) * 100)
        
        # Weighted: latency 40%, jitter 40%, speed 20%
        final_score = (latency_score * 0.4) + (jitter_score * 0.4) + (speed_score * 0.2)
        return round(final_score, 1)
    
    def _calculate_cloud_score(self, download_speed: float, latency: List[float], packet_loss: float) -> float:
        """Calculate cloud work quality score (0-100)"""
        score = 100.0
        
        # Download/upload speed is critical for cloud work
        if download_speed > 50:
            speed_score = 100
        elif download_speed > 25:
            speed_score = 80 + ((download_speed - 25) / 25) * 20
        elif download_speed > 10:
            speed_score = 60 + ((download_speed - 10) / 15) * 20
        else:
            speed_score = max(0, (download_speed / 10) * 60)
        
        # Latency matters for interactive cloud work
        if latency:
            avg_latency = statistics.mean(latency)
            latency_score = 100 if avg_latency < 50 else max(70, 100 - ((avg_latency - 50) / 50) * 30)
        else:
            latency_score = 70
        
        # Packet loss is bad for cloud work
        if packet_loss < 1:
            loss_score = 100
        elif packet_loss < 3:
            loss_score = 90 - ((packet_loss - 1) / 2) * 20
        else:
            loss_score = max(0, 70 - ((packet_loss - 3) / 3) * 50)
        
        # Weighted: speed 50%, latency 30%, loss 20%
        final_score = (speed_score * 0.5) + (latency_score * 0.3) + (loss_score * 0.2)
        return round(final_score, 1)
    
    def _generate_recommendations(
        self, gaming: float, streaming: float, zoom: float, cloud: float
    ) -> Dict[str, List[str]]:
        """Generate recommendations for improving scores"""
        recommendations = {
            "gaming": [],
            "streaming": [],
            "zoom": [],
            "cloud_work": [],
        }
        
        if gaming < 70:
            recommendations["gaming"] = [
                "Use wired connection instead of WiFi",
                "Close bandwidth-heavy applications",
                "Use QoS settings on router to prioritize gaming",
                "Upgrade internet plan for lower latency",
            ]
        
        if streaming < 70:
            recommendations["streaming"] = [
                "Upgrade internet plan for faster speeds",
                "Use wired connection for stable streaming",
                "Reduce video quality if on limited connection",
                "Close other bandwidth-consuming apps",
            ]
        
        if zoom < 70:
            recommendations["zoom"] = [
                "Use wired connection for stable video calls",
                "Close other applications using bandwidth",
                "Reduce video quality in Zoom settings",
                "Use phone audio if video quality is poor",
            ]
        
        if cloud < 70:
            recommendations["cloud_work"] = [
                "Upgrade internet plan for faster speeds",
                "Use wired connection for reliability",
                "Optimize cloud sync settings",
                "Consider using local caching when possible",
            ]
        
        return recommendations
    
    def _get_quality_label(self, score: float) -> str:
        """Get quality label from score"""
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Fair"
        elif score >= 40:
            return "Poor"
        else:
            return "Very Poor"
    
    def _get_best_use_case(self, gaming: float, streaming: float, zoom: float, cloud: float) -> str:
        """Determine best use case based on scores"""
        scores = {
            "Gaming": gaming,
            "Streaming": streaming,
            "Video Calls (Zoom)": zoom,
            "Cloud Work": cloud,
        }
        
        best = max(scores.items(), key=lambda x: x[1])
        return best[0]
    
    def _get_improvement_areas(self, gaming: float, streaming: float, zoom: float, cloud: float) -> List[str]:
        """Get areas that need improvement"""
        areas = []
        
        if gaming < 70:
            areas.append("Gaming - Low latency/jitter needed")
        if streaming < 70:
            areas.append("Streaming - Higher speeds needed")
        if zoom < 70:
            areas.append("Video Calls - Better stability needed")
        if cloud < 70:
            areas.append("Cloud Work - Faster speeds needed")
        
        return areas if areas else ["All areas performing well"]


