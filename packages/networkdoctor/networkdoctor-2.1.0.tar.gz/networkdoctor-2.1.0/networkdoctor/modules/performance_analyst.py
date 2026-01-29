"""
Network Performance Expert for NetworkDoctor
"""
from typing import List, Dict, Any


class PerformanceAnalyst:
    """Network performance analysis expert"""
    
    async def diagnose(self, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Diagnose performance issues.
        
        Args:
            scan_results: Results from network scanner
            
        Returns:
            Diagnosis results
        """
        issues = []
        findings = []
        
        for result in scan_results:
            target = result.get("target", "")
            ping_result = result.get("ping", {})
            
            if ping_result.get("success"):
                avg_latency = ping_result.get("avg_latency", 0)
                packet_loss = ping_result.get("packet_loss", 0)
                
                findings.append({
                    "target": target,
                    "avg_latency_ms": avg_latency,
                    "packet_loss_percent": packet_loss,
                    "min_latency_ms": ping_result.get("min_latency"),
                    "max_latency_ms": ping_result.get("max_latency"),
                })
                
                # Check for high latency
                if avg_latency > 100:
                    issues.append({
                        "id": f"perf_high_latency_{target}",
                        "type": "performance",
                        "severity": "medium" if avg_latency < 200 else "high",
                        "title": "High Network Latency",
                        "description": f"Average latency to {target} is {avg_latency:.1f}ms",
                        "impact": "Slow response times, poor user experience",
                        "solutions": [
                            {
                                "action": "Check network path",
                                "command": f"traceroute {target}",
                            },
                            {
                                "action": "Optimize network routing",
                                "command": "Review routing configuration",
                            },
                        ],
                    })
                
                # Check for packet loss
                if packet_loss > 5:
                    issues.append({
                        "id": f"perf_packet_loss_{target}",
                        "type": "performance",
                        "severity": "high" if packet_loss > 10 else "medium",
                        "title": "Packet Loss Detected",
                        "description": f"Packet loss to {target} is {packet_loss:.1f}%",
                        "impact": "Unreliable connections, data retransmission",
                        "solutions": [
                            {
                                "action": "Check network quality",
                                "command": f"ping -c 100 {target}",
                            },
                            {
                                "action": "Investigate network congestion",
                                "command": "Check network utilization",
                            },
                        ],
                    })
            else:
                findings.append({
                    "target": target,
                    "status": "unreachable",
                })
        
        # Calculate performance score
        if findings:
            avg_latency_all = sum(f.get("avg_latency_ms", 0) for f in findings if "avg_latency_ms" in f)
            avg_latency_all = avg_latency_all / len([f for f in findings if "avg_latency_ms" in f]) if findings else 0
            
            performance_score = 100
            if avg_latency_all > 50:
                performance_score -= min(30, (avg_latency_all - 50) / 2)
            if any(f.get("packet_loss_percent", 0) > 5 for f in findings):
                performance_score -= 20
        else:
            performance_score = 0
        
        return {
            "doctor": "performance",
            "status": "completed",
            "issues": issues,
            "findings": findings,
            "summary": {
                "total_issues": len(issues),
                "performance_score": int(performance_score),
                "avg_latency_ms": avg_latency_all if findings else 0,
            },
        }







