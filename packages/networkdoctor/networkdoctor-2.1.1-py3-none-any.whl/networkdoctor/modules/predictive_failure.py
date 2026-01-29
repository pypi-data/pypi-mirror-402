"""
Predictive Failure Alert - Predict Router, ISP, Cable Issues

"""
import asyncio
import time
import statistics
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import deque


class PredictiveFailureAlert:
    """Predict network failures before they occur"""
    
    def __init__(self):
        self.name = "Predictive Failure Alert"
        self.history_window = 100  # Number of data points to keep
        self.latency_history = deque(maxlen=self.history_window)
        self.packet_loss_history = deque(maxlen=self.history_window)
        self.timeout_history = deque(maxlen=self.history_window)
        
        # Thresholds for prediction
        self.latency_increase_threshold = 1.5  # 50% increase
        self.packet_loss_threshold = 5.0  # 5% packet loss
        self.timeout_threshold = 10.0  # 10% timeout rate
    
    async def diagnose(self, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Predict potential network failures.
        
        Args:
            scan_results: Results from network scan
            
        Returns:
            Predictive failure analysis
        """
        issues = []
        predictions = []
        findings = []
        
        # Collect current metrics
        current_metrics = self._extract_metrics(scan_results)
        
        # Update history
        if current_metrics.get("latency"):
            self.latency_history.append(current_metrics["latency"])
        if current_metrics.get("packet_loss"):
            self.packet_loss_history.append(current_metrics["packet_loss"])
        if current_metrics.get("timeout_rate"):
            self.timeout_history.append(current_metrics["timeout_rate"])
        
        # Predict router failure
        router_prediction = self._predict_router_failure()
        if router_prediction:
            predictions.append(router_prediction)
            issues.append({
                "severity": router_prediction.get("severity", "medium"),
                "type": "predicted_router_failure",
                "title": "Router Failure Predicted",
                "description": router_prediction.get("description"),
                "confidence": router_prediction.get("confidence", 0),
                "timeframe": router_prediction.get("timeframe"),
                "recommendations": [
                    "Backup router configuration",
                    "Check router logs for errors",
                    "Monitor router CPU and memory",
                    "Have backup router ready",
                    "Contact ISP if router is leased",
                ],
            })
        
        # Predict ISP downtime
        isp_prediction = self._predict_isp_downtime()
        if isp_prediction:
            predictions.append(isp_prediction)
            issues.append({
                "severity": isp_prediction.get("severity", "medium"),
                "type": "predicted_isp_downtime",
                "title": "ISP Downtime Predicted",
                "description": isp_prediction.get("description"),
                "confidence": isp_prediction.get("confidence", 0),
                "timeframe": isp_prediction.get("timeframe"),
                "recommendations": [
                    "Contact ISP proactively",
                    "Plan for alternative connectivity",
                    "Schedule important work during stable periods",
                    "Monitor ISP status page",
                ],
            })
        
        # Predict cable issues
        cable_prediction = self._predict_cable_issues()
        if cable_prediction:
            predictions.append(cable_prediction)
            issues.append({
                "severity": cable_prediction.get("severity", "medium"),
                "type": "predicted_cable_issue",
                "title": "Cable/Fiber Issue Predicted",
                "description": cable_prediction.get("description"),
                "confidence": cable_prediction.get("confidence", 0),
                "timeframe": cable_prediction.get("timeframe"),
                "recommendations": [
                    "Inspect physical cables for damage",
                    "Check connectors and terminations",
                    "Test with replacement cables if possible",
                    "Contact ISP for line testing",
                ],
            })
        
        findings.append({
            "finding": "predictive_analysis",
            "predictions_count": len(predictions),
            "history_data_points": len(self.latency_history),
        })
        
        return {
            "doctor": "predictive_failure",
            "status": "completed",
            "issues": issues,
            "findings": findings,
            "predictions": predictions,
            "current_metrics": current_metrics,
            "summary": {
                "predictions_count": len(predictions),
                "high_confidence_predictions": sum(1 for p in predictions if p.get("confidence", 0) > 70),
                "imminent_threats": sum(1 for p in predictions if p.get("timeframe") == "imminent"),
            },
        }
    
    def _extract_metrics(self, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract metrics from scan results"""
        metrics = {}
        
        latencies = []
        packet_loss = None
        timeouts = 0
        total_requests = 0
        
        for result in scan_results:
            if isinstance(result, dict):
                # Extract latency
                if "latency" in result:
                    latencies.append(result["latency"])
                elif "ping" in result:
                    latencies.append(result["ping"])
                
                # Extract packet loss
                if "packet_loss" in result:
                    packet_loss = result["packet_loss"]
                
                # Count timeouts
                if result.get("status") == "timeout" or "timeout" in str(result.get("error", "")).lower():
                    timeouts += 1
                
                if "status" in result:
                    total_requests += 1
        
        if latencies:
            metrics["latency"] = statistics.mean(latencies)
        
        if packet_loss is not None:
            metrics["packet_loss"] = packet_loss
        elif total_requests > 0:
            metrics["packet_loss"] = (timeouts / total_requests) * 100
        
        if total_requests > 0:
            metrics["timeout_rate"] = (timeouts / total_requests) * 100
        
        return metrics
    
    def _predict_router_failure(self) -> Optional[Dict[str, Any]]:
        """Predict router failure based on patterns"""
        if len(self.latency_history) < 10:
            return None
        
        # Calculate trends
        recent_latency = list(self.latency_history)[-10:]
        older_latency = list(self.latency_history)[-20:-10] if len(self.latency_history) >= 20 else recent_latency[:5]
        
        if not older_latency:
            return None
        
        avg_recent = statistics.mean(recent_latency)
        avg_older = statistics.mean(older_latency)
        
        # Check for increasing latency trend (router overload/failure indicator)
        latency_increase = (avg_recent / avg_older) if avg_older > 0 else 1.0
        
        # Check packet loss trend
        packet_loss_increase = False
        if len(self.packet_loss_history) >= 10:
            recent_loss = list(self.packet_loss_history)[-10:]
            older_loss = list(self.packet_loss_history)[-20:-10] if len(self.packet_loss_history) >= 20 else recent_loss[:5]
            
            if older_loss:
                avg_recent_loss = statistics.mean(recent_loss)
                avg_older_loss = statistics.mean(older_loss)
                if avg_recent_loss > avg_older_loss * 1.5:
                    packet_loss_increase = True
        
        confidence = 0
        timeframe = "unknown"
        severity = "medium"
        
        # Predict based on patterns
        if latency_increase > self.latency_increase_threshold:
            confidence += 40
            if latency_increase > 2.0:  # Doubled latency
                confidence += 20
                severity = "high"
        
        if packet_loss_increase:
            confidence += 30
            avg_loss = statistics.mean(list(self.packet_loss_history)[-10:])
            if avg_loss > self.packet_loss_threshold:
                confidence += 20
                severity = "high"
        
        # Determine timeframe
        if confidence > 70:
            timeframe = "imminent"  # Within hours/days
        elif confidence > 50:
            timeframe = "near_term"  # Within weeks
        elif confidence > 30:
            timeframe = "medium_term"  # Within months
        
        if confidence < 40:
            return None
        
        return {
            "type": "router_failure",
            "confidence": min(confidence, 90),
            "severity": severity,
            "timeframe": timeframe,
            "description": f"Router showing signs of failure: latency increased {latency_increase:.1f}x, packet loss patterns detected",
            "indicators": {
                "latency_increase": latency_increase,
                "packet_loss_increase": packet_loss_increase,
            },
        }
    
    def _predict_isp_downtime(self) -> Optional[Dict[str, Any]]:
        """Predict ISP downtime based on patterns"""
        if len(self.timeout_history) < 10:
            return None
        
        # Analyze timeout patterns
        recent_timeouts = list(self.timeout_history)[-10:]
        avg_timeout_rate = statistics.mean(recent_timeouts)
        
        # Check for increasing timeout trend
        timeout_increase = False
        if len(self.timeout_history) >= 20:
            older_timeouts = list(self.timeout_history)[-20:-10]
            avg_older = statistics.mean(older_timeouts)
            if avg_timeout_rate > avg_older * 1.5:
                timeout_increase = True
        
        confidence = 0
        timeframe = "unknown"
        severity = "medium"
        
        # Predict based on timeout patterns
        if avg_timeout_rate > self.timeout_threshold:
            confidence += 40
            if avg_timeout_rate > 20:
                confidence += 20
                severity = "high"
        
        if timeout_increase:
            confidence += 30
        
        # Check for cyclic patterns (scheduled maintenance)
        if len(self.timeout_history) >= 30:
            # Simple pattern detection (could be enhanced)
            recent_pattern = recent_timeouts[-5:]
            older_pattern = list(self.timeout_history)[-15:-10]
            
            # Check if similar patterns (indicating scheduled issues)
            if abs(statistics.mean(recent_pattern) - statistics.mean(older_pattern)) < 5:
                confidence += 20
        
        if confidence < 40:
            return None
        
        # Determine timeframe
        if confidence > 70:
            timeframe = "imminent"
        elif confidence > 50:
            timeframe = "near_term"
        else:
            timeframe = "medium_term"
        
        return {
            "type": "isp_downtime",
            "confidence": min(confidence, 90),
            "severity": severity,
            "timeframe": timeframe,
            "description": f"ISP downtime predicted: timeout rate at {avg_timeout_rate:.1f}%, showing upward trend",
            "indicators": {
                "timeout_rate": avg_timeout_rate,
                "increasing_trend": timeout_increase,
            },
        }
    
    def _predict_cable_issues(self) -> Optional[Dict[str, Any]]:
        """Predict cable/fiber issues based on patterns"""
        if len(self.latency_history) < 10:
            return None
        
        # Cable issues often show intermittent high latency and packet loss
        recent_latency = list(self.latency_history)[-10:]
        latency_variance = statistics.stdev(recent_latency) if len(recent_latency) > 1 else 0
        avg_latency = statistics.mean(recent_latency)
        
        # High variance indicates intermittent issues (cable problem)
        cv = (latency_variance / avg_latency) if avg_latency > 0 else 0
        
        confidence = 0
        timeframe = "unknown"
        severity = "medium"
        
        # High coefficient of variation = intermittent issues = cable problem
        if cv > 0.5:
            confidence += 40
            if cv > 1.0:
                confidence += 20
                severity = "high"
        
        # Check packet loss patterns
        if len(self.packet_loss_history) >= 10:
            recent_loss = list(self.packet_loss_history)[-10:]
            avg_loss = statistics.mean(recent_loss)
            
            if avg_loss > 2.0:  # 2% packet loss
                confidence += 30
                if avg_loss > self.packet_loss_threshold:
                    confidence += 20
                    severity = "high"
            
            # Intermittent packet loss = cable issue
            loss_variance = statistics.stdev(recent_loss) if len(recent_loss) > 1 else 0
            if loss_variance > 3.0:  # High variance in packet loss
                confidence += 20
        
        if confidence < 40:
            return None
        
        # Determine timeframe
        if confidence > 70:
            timeframe = "imminent"
        elif confidence > 50:
            timeframe = "near_term"
        else:
            timeframe = "medium_term"
        
        return {
            "type": "cable_issue",
            "confidence": min(confidence, 90),
            "severity": severity,
            "timeframe": timeframe,
            "description": f"Cable/fiber issue predicted: high latency variance (CV={cv:.2f}), intermittent packet loss",
            "indicators": {
                "latency_variance": latency_variance,
                "coefficient_of_variation": cv,
            },
        }

