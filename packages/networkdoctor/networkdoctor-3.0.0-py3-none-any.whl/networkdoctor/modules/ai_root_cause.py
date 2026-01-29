"""
AI Root Cause Engine - Natural Language Problem Analysis

"""
import re
from typing import List, Dict, Any, Optional
from collections import Counter


class AIRootCauseEngine:
    """Analyze natural language descriptions and identify root causes"""
    
    def __init__(self):
        self.name = "AI Root Cause Engine"
        
        # Keywords for different problem types
        self.problem_patterns = {
            "slow": {
                "keywords": ["slow", "sluggish", "laggy", "lazy", "crawl", "bottleneck", "snail"],
                "causes": ["bandwidth", "latency", "dns", "isp_throttling", "congestion"],
                "priority": 1,
            },
            "down": {
                "keywords": ["down", "offline", "unreachable", "cannot connect", "no internet", "disconnect"],
                "causes": ["connection", "dns", "gateway", "isp", "firewall"],
                "priority": 1,
            },
            "intermittent": {
                "keywords": ["intermittent", "sometimes", "random", "unstable", "inconsistent", "fluctuat"],
                "causes": ["signal", "interference", "congestion", "isp", "cable"],
                "priority": 2,
            },
            "timeout": {
                "keywords": ["timeout", "time out", "expired", "timed out"],
                "causes": ["latency", "firewall", "timeout_settings", "connection"],
                "priority": 2,
            },
            "dns": {
                "keywords": ["dns", "cannot resolve", "name resolution", "hostname"],
                "causes": ["dns_server", "dns_cache", "dns_config"],
                "priority": 3,
            },
            "security": {
                "keywords": ["hack", "intrusion", "unauthorized", "breach", "attack", "malware"],
                "causes": ["security", "firewall", "unauthorized_access", "malware"],
                "priority": 1,
            },
        }
        
        # Common root causes and their indicators
        self.root_causes = {
            "dns": {
                "indicators": ["cannot resolve", "dns error", "name resolution failed"],
                "solutions": [
                    "Flush DNS cache: ipconfig /flushdns (Windows) or sudo systemctl restart systemd-resolved (Linux)",
                    "Change DNS servers to 8.8.8.8 and 8.8.4.4 (Google) or 1.1.1.1 (Cloudflare)",
                    "Check DNS server connectivity",
                ],
            },
            "isp_throttling": {
                "indicators": ["slow during peak", "speed drops", "bandwidth limit"],
                "solutions": [
                    "Test speeds at different times",
                    "Contact ISP with evidence",
                    "Consider upgrading plan",
                    "Use VPN to bypass throttling (if legal in your area)",
                ],
            },
            "bandwidth": {
                "indicators": ["slow download", "slow upload", "multiple devices"],
                "solutions": [
                    "Check bandwidth usage on router",
                    "Close bandwidth-heavy applications",
                    "Upgrade internet plan",
                    "Use QoS settings to prioritize traffic",
                ],
            },
            "latency": {
                "indicators": ["ping high", "delay", "lag", "slow response"],
                "solutions": [
                    "Use wired connection instead of WiFi",
                    "Check distance to router",
                    "Reduce network hops",
                    "Check for network congestion",
                ],
            },
            "firewall": {
                "indicators": ["blocked", "cannot access", "connection refused"],
                "solutions": [
                    "Check firewall rules",
                    "Temporarily disable firewall to test",
                    "Add exception for application",
                    "Check proxy settings",
                ],
            },
            "signal": {
                "indicators": ["weak signal", "disconnect", "drops"],
                "solutions": [
                    "Move closer to router",
                    "Reposition router/antenna",
                    "Use WiFi extender",
                    "Check for interference from other devices",
                ],
            },
        }
    
    async def diagnose(self, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze natural language problem description and identify root cause.
        
        Args:
            scan_results: Results from network scan (may contain user description)
            
        Returns:
            Root cause analysis with solutions
        """
        issues = []
        findings = []
        
        # Extract user description from scan results
        user_description = self._extract_user_description(scan_results)
        
        if not user_description:
            # If no user description, analyze scan results for patterns
            user_description = self._generate_description_from_results(scan_results)
        
        # Analyze description
        problem_analysis = self._analyze_description(user_description)
        
        # Identify root causes
        root_causes = self._identify_root_causes(problem_analysis, scan_results)
        
        # Generate solutions
        solutions = self._generate_solutions(root_causes)
        
        findings.append({
            "finding": "ai_root_cause_analysis",
            "user_description": user_description,
            "identified_problems": problem_analysis.get("problems", []),
            "root_causes": root_causes,
            "confidence": self._calculate_confidence(problem_analysis, root_causes),
        })
        
        if root_causes:
            issues.append({
                "severity": "high",
                "type": "root_cause_identified",
                "title": "Root Cause Analysis Complete",
                "description": f"Identified {len(root_causes)} potential root cause(s)",
                "root_causes": root_causes,
                "solutions": solutions,
            })
        
        return {
            "doctor": "ai_root_cause",
            "status": "completed",
            "issues": issues,
            "findings": findings,
            "analysis": {
                "user_description": user_description,
                "problem_type": problem_analysis.get("primary_problem"),
                "root_causes": root_causes,
                "solutions": solutions,
                "confidence_score": self._calculate_confidence(problem_analysis, root_causes),
            },
            "summary": {
                "root_causes_identified": len(root_causes),
                "solutions_provided": len(solutions),
                "primary_problem": problem_analysis.get("primary_problem"),
            },
        }
    
    def _extract_user_description(self, scan_results: List[Dict[str, Any]]) -> Optional[str]:
        """Extract user description from scan results"""
        for result in scan_results:
            if isinstance(result, dict):
                # Check various possible fields
                for field in ["description", "user_description", "problem", "issue", "query"]:
                    if field in result:
                        desc = result[field]
                        if isinstance(desc, str) and desc.strip():
                            return desc.strip()
        return None
    
    def _generate_description_from_results(self, scan_results: List[Dict[str, Any]]) -> str:
        """Generate description from scan results if no user description provided"""
        # Analyze scan results to generate a description
        descriptions = []
        
        for result in scan_results:
            if isinstance(result, dict):
                if "status" in result and result["status"] != "success":
                    descriptions.append(f"Connection issue detected")
                if "latency" in result and result["latency"] > 100:
                    descriptions.append(f"High latency: {result['latency']}ms")
                if "error" in result:
                    descriptions.append(f"Error: {result['error']}")
        
        if descriptions:
            return ". ".join(descriptions[:3])  # Join first 3 descriptions
        return "Network performance issue"
    
    def _analyze_description(self, description: str) -> Dict[str, Any]:
        """Analyze natural language description"""
        description_lower = description.lower()
        problems = []
        problem_scores = {}
        
        # Check each problem pattern
        for problem_type, pattern_info in self.problem_patterns.items():
            score = 0
            matched_keywords = []
            
            for keyword in pattern_info["keywords"]:
                if keyword in description_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            if score > 0:
                problems.append({
                    "type": problem_type,
                    "score": score,
                    "keywords": matched_keywords,
                    "priority": pattern_info["priority"],
                })
                problem_scores[problem_type] = score
        
        # Determine primary problem
        primary_problem = None
        if problems:
            # Sort by priority and score
            problems_sorted = sorted(
                problems,
                key=lambda x: (x["priority"], x["score"]),
                reverse=True
            )
            primary_problem = problems_sorted[0]["type"]
        
        return {
            "problems": problems,
            "primary_problem": primary_problem,
            "problem_scores": problem_scores,
        }
    
    def _identify_root_causes(
        self, problem_analysis: Dict[str, Any], scan_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify root causes based on problem analysis and scan results"""
        root_causes = []
        
        primary_problem = problem_analysis.get("primary_problem")
        problem_scores = problem_analysis.get("problem_scores", {})
        
        # Map problems to root causes
        if primary_problem:
            pattern_info = self.problem_patterns.get(primary_problem, {})
            potential_causes = pattern_info.get("causes", [])
            
            # Analyze scan results to validate causes
            for cause_type in potential_causes:
                confidence = self._validate_cause(cause_type, scan_results, problem_scores)
                
                if confidence > 30:  # Minimum confidence threshold
                    cause_info = self.root_causes.get(cause_type, {})
                    
                    root_causes.append({
                        "type": cause_type,
                        "confidence": confidence,
                        "indicators": cause_info.get("indicators", []),
                        "description": self._describe_cause(cause_type),
                    })
        
        # Sort by confidence
        root_causes.sort(key=lambda x: x["confidence"], reverse=True)
        
        return root_causes[:3]  # Return top 3 root causes
    
    def _validate_cause(
        self, cause_type: str, scan_results: List[Dict[str, Any]], problem_scores: Dict[str, float]
    ) -> int:
        """Validate root cause with scan results and return confidence score"""
        confidence = 50  # Base confidence
        
        # Enhanced validation with real network metrics
        for result in scan_results:
            if isinstance(result, dict):
                # DNS causes
                if cause_type in ["dns", "dns_server", "dns_cache"]:
                    if any(key in str(result).lower() for key in ["dns", "resolve", "name"]):
                        confidence += 15
                    if result.get("status") in ["dns_error", "resolution_failed"]:
                        confidence += 25
                    if result.get("latency", 0) > 100 and "dns" in str(result).lower():
                        confidence += 10
                
                # Bandwidth causes
                if cause_type == "bandwidth":
                    if any(key in str(result).lower() for key in ["speed", "bandwidth", "throughput"]):
                        confidence += 15
                    if result.get("speed_mbps", 999) < 5:  # Low speed detected
                        confidence += 25
                    if result.get("download_speed_mbps", 999) < 5:
                        confidence += 20
                
                # Latency causes
                if cause_type == "latency":
                    if "latency" in result or "ping" in result:
                        confidence += 15
                    if result.get("latency", 0) > 150:  # High latency
                        confidence += 25
                    if result.get("average_latency_ms", 0) > 100:
                        confidence += 20
                
                # ISP throttling (enhanced detection)
                if cause_type == "isp_throttling":
                    if any(key in str(result).lower() for key in ["throttle", "throttling"]):
                        confidence += 35
                    # Check for speed inconsistencies
                    if result.get("speed_variance", 0) > 1.0:
                        confidence += 15
                    if result.get("confidence_score", 0) > 70:  # From ISP detector
                        confidence += 20
                
                # Connection issues
                if cause_type == "connection":
                    if result.get("status") in ["timeout", "failed", "unreachable"]:
                        confidence += 20
                    if any(key in str(result).lower() for key in ["connect", "reach", "timeout"]):
                        confidence += 10
                
                # Firewall issues
                if cause_type == "firewall":
                    if any(key in str(result).lower() for key in ["firewall", "block", "deny"]):
                        confidence += 20
                    if result.get("status") == "blocked":
                        confidence += 25
        
        # Enhanced problem score analysis
        if "slow" in problem_scores and problem_scores["slow"] >= 2:
            if cause_type in ["bandwidth", "isp_throttling", "latency", "congestion"]:
                confidence += 15
        
        if "down" in problem_scores and problem_scores["down"] >= 1:
            if cause_type in ["connection", "dns", "gateway", "isp"]:
                confidence += 20
        
        if "intermittent" in problem_scores and problem_scores["intermittent"] >= 1:
            if cause_type in ["signal", "congestion", "isp", "cable"]:
                confidence += 15
        
        # Boost confidence for multiple indicators
        indicator_count = 0
        if cause_type in ["dns", "dns_server", "dns_cache"] and any("dns" in str(r).lower() for r in scan_results):
            indicator_count += 1
        if cause_type == "bandwidth" and any(r.get("speed_mbps", 999) < 10 for r in scan_results if isinstance(r, dict)):
            indicator_count += 1
        if cause_type == "latency" and any(r.get("latency", 0) > 100 for r in scan_results if isinstance(r, dict)):
            indicator_count += 1
        
        if indicator_count >= 2:
            confidence += 10
        
        return min(confidence, 95)  # Cap at 95%
    
    def _describe_cause(self, cause_type: str) -> str:
        """Get human-readable description of root cause"""
        descriptions = {
            "dns": "DNS resolution problems - cannot translate domain names to IP addresses",
            "dns_server": "DNS server is unreachable or misconfigured",
            "dns_cache": "DNS cache is corrupted or outdated",
            "bandwidth": "Insufficient bandwidth - connection speed is too slow",
            "latency": "High network latency - delays in data transmission",
            "isp_throttling": "ISP is throttling your connection speed",
            "congestion": "Network congestion - too much traffic on network",
            "firewall": "Firewall is blocking connections",
            "signal": "Weak WiFi signal or interference",
            "connection": "Physical connection problem",
            "gateway": "Default gateway is unreachable",
            "isp": "ISP service outage or problem",
        }
        
        return descriptions.get(cause_type, f"Network issue: {cause_type}")
    
    def _generate_solutions(self, root_causes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate solutions for identified root causes"""
        solutions = []
        
        for cause in root_causes:
            cause_type = cause["type"]
            cause_info = self.root_causes.get(cause_type, {})
            
            solution_steps = cause_info.get("solutions", [])
            
            if solution_steps:
                solutions.append({
                    "root_cause": cause_type,
                    "description": cause["description"],
                    "confidence": cause["confidence"],
                    "steps": solution_steps,
                    "priority": "high" if cause["confidence"] > 70 else "medium",
                })
        
        return solutions
    
    def _calculate_confidence(
        self, problem_analysis: Dict[str, Any], root_causes: List[Dict[str, Any]]
    ) -> int:
        """Calculate overall confidence score for analysis"""
        if not root_causes:
            return 0
        
        # Base confidence from problem analysis
        problems = problem_analysis.get("problems", [])
        base_confidence = 50 if problems else 30
        
        # Add confidence from root cause validation
        avg_cause_confidence = sum(c["confidence"] for c in root_causes) / len(root_causes)
        
        # Final confidence is weighted average
        final_confidence = int((base_confidence * 0.3) + (avg_cause_confidence * 0.7))
        
        return min(final_confidence, 95)

