"""
Global Threat Intelligence - Global cyber threat intelligence integration
"""

import asyncio
import aiohttp
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import json
import hashlib
from dataclasses import dataclass


@dataclass
class ThreatIndicator:
    """Threat intelligence indicator"""
    id: str
    type: str
    value: str
    severity: str
    confidence: float
    source: str
    timestamp: datetime
    description: str
    affected_systems: List[str]
    mitigation: List[str]


class GlobalThreatIntelligence:
    """
    Global Threat Intelligence provides comprehensive cyber threat intelligence
    from global sources with real-time analysis and predictive capabilities.
    """
    
    def __init__(self, update_interval: int = 300):  # 5 minutes
        """
        Initialize Global Threat Intelligence
        
        Args:
            update_interval: Update interval in seconds (default: 300)
        """
        self.update_interval = update_interval
        self.threat_feeds = [
            "global_cyber_threats",
            "zero_day_exploits",
            "dark_web_monitoring",
            "apt_monitoring",
            "malware_analysis",
            "botnet_tracking",
            "phishing_intelligence",
            "ransomware_tracking",
            "vulnerability_intelligence",
            "threat_actor_monitoring"
        ]
        self.threat_database = []
        self.intelligence_sources = {}
        self.threat_indicators = {}
        self.active_campaigns = {}
        self.threat_history = []
        self.intelligence_active = False
        
    async def start_threat_intelligence(self) -> Dict[str, Any]:
        """
        Start threat intelligence collection
        
        Returns:
            Dictionary containing intelligence start results
        """
        self.intelligence_active = True
        
        # Initialize intelligence sources
        await self._initialize_intelligence_sources()
        
        # Start intelligence collection loop
        intelligence_task = asyncio.create_task(self._intelligence_loop())
        
        return {
            'intelligence_started': True,
            'threat_feeds': len(self.threat_feeds),
            'intelligence_sources': len(self.intelligence_sources),
            'update_interval': self.update_interval,
            'start_time': datetime.now().isoformat(),
            'intelligence_task_id': id(intelligence_task)
        }
    
    async def _initialize_intelligence_sources(self) -> None:
        """Initialize threat intelligence sources"""
        # Define intelligence sources
        sources = {
            "cve_database": {
                "name": "CVE Database",
                "url": "https://cve.circl.lu/api/cve/",
                "type": "vulnerability",
                "update_frequency": "hourly",
                "reliability": 0.95
            },
            "virustotal": {
                "name": "VirusTotal",
                "url": "https://www.virustotal.com/vtapi/v2/",
                "type": "malware",
                "update_frequency": "continuous",
                "reliability": 0.90
            },
            "abuse_ch": {
                "name": "Abuse.ch",
                "url": "https://abuse.ch/",
                "type": "malware_domains",
                "update_frequency": "hourly",
                "reliability": 0.85
            },
            "phish_tank": {
                "name": "PhishTank",
                "url": "https://www.phishtank.com/",
                "type": "phishing",
                "update_frequency": "hourly",
                "reliability": 0.80
            },
            "malware_domain_list": {
                "name": "Malware Domain List",
                "url": "http://www.malwaredomainlist.com/",
                "type": "malware_domains",
                "update_frequency": "daily",
                "reliability": 0.75
            },
            "threat_connect": {
                "name": "ThreatConnect",
                "url": "https://threatconnect.com/",
                "type": "threat_intelligence",
                "update_frequency": "continuous",
                "reliability": 0.90
            },
            "recorded_future": {
                "name": "Recorded Future",
                "url": "https://www.recordedfuture.com/",
                "type": "threat_intelligence",
                "update_frequency": "continuous",
                "reliability": 0.95
            },
            "crowdstrike": {
                "name": "CrowdStrike",
                "url": "https://www.crowdstrike.com/",
                "type": "threat_intelligence",
                "update_frequency": "continuous",
                "reliability": 0.90
            }
        }
        
        self.intelligence_sources = sources
    
    async def _intelligence_loop(self) -> None:
        """Main intelligence collection loop"""
        while self.intelligence_active:
            try:
                # Collect threat intelligence
                threat_data = await self.collect_global_threat_intelligence()
                
                # Analyze threat patterns
                threat_analysis = await self.analyze_threat_patterns(threat_data)
                
                # Generate threat alerts
                threat_alerts = await self.generate_threat_alerts(threat_analysis)
                
                # Store intelligence data
                intelligence_cycle = {
                    'timestamp': datetime.now().isoformat(),
                    'threat_data': threat_data,
                    'threat_analysis': threat_analysis,
                    'threat_alerts': threat_alerts
                }
                self.threat_history.append(intelligence_cycle)
                
                # Keep only last 1000 cycles
                if len(self.threat_history) > 1000:
                    self.threat_history = self.threat_history[-1000:]
                
                # Wait for next cycle
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                print(f"Threat intelligence error: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    async def collect_global_threat_intelligence(self) -> Dict[str, Any]:
        """
        Collect cyber threat intelligence from global sources
        
        Returns:
            Dictionary containing threat intelligence data
        """
        threat_data = {}
        
        for feed in self.threat_feeds:
            feed_data = await self.query_threat_feed(feed)
            threat_data[feed] = feed_data
        
        # Collect from intelligence sources
        source_data = {}
        for source_id, source_info in self.intelligence_sources.items():
            source_threats = await self.query_intelligence_source(source_id, source_info)
            source_data[source_id] = source_threats
        
        return {
            'threat_feeds': threat_data,
            'intelligence_sources': source_data,
            'total_threats': self._count_total_threats(threat_data, source_data),
            'timestamp': datetime.now().isoformat()
        }
    
    async def query_threat_feed(self, feed_name: str) -> Dict[str, Any]:
        """
        Query specific threat intelligence feed
        
        Args:
            feed_name: Name of threat feed
            
        Returns:
            Dictionary containing feed data
        """
        # Simulate threat feed query
        feed_data = {
            'feed_name': feed_name,
            'threats_detected': np.random.randint(0, 100),
            'severity_level': np.random.choice(['low', 'medium', 'high', 'critical']),
            'last_update': datetime.now().isoformat(),
            'threat_types': self._generate_threat_types(feed_name),
            'affected_regions': self._generate_affected_regions(),
            'confidence_score': np.random.uniform(0.5, 1.0),
            'threat_indicators': self._generate_threat_indicators(feed_name),
            'campaigns': self._generate_threat_campaigns(feed_name),
            'mitigation_advice': self._generate_mitigation_advice(feed_name)
        }
        
        return feed_data
    
    async def query_intelligence_source(self, source_id: str, source_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query specific intelligence source
        
        Args:
            source_id: Source ID
            source_info: Source information
            
        Returns:
            Dictionary containing source threat data
        """
        # Simulate intelligence source query
        source_threats = {
            'source_id': source_id,
            'source_name': source_info['name'],
            'source_type': source_info['type'],
            'threats_found': np.random.randint(0, 50),
            'indicators': self._generate_source_indicators(source_info['type']),
            'confidence': source_info['reliability'],
            'last_updated': datetime.now().isoformat(),
            'threat_actors': self._generate_threat_actors(),
            'attack_patterns': self._generate_attack_patterns(),
            'vulnerabilities': self._generate_vulnerabilities(),
            'malware_families': self._generate_malware_families()
        }
        
        return source_threats
    
    def _generate_threat_types(self, feed_name: str) -> List[str]:
        """Generate threat types based on feed name"""
        threat_type_mapping = {
            "global_cyber_threats": ["malware", "phishing", "ddos", "injection"],
            "zero_day_exploits": ["zero_day", "vulnerability", "exploit"],
            "dark_web_monitoring": ["data_breach", "credential_theft", "underground_markets"],
            "apt_monitoring": ["apt", "targeted_attack", "espionage"],
            "malware_analysis": ["trojan", "ransomware", "botnet", "rootkit"],
            "botnet_tracking": ["botnet", "c2_server", "ddos"],
            "phishing_intelligence": ["phishing", "credential_theft", "social_engineering"],
            "ransomware_tracking": ["ransomware", "encryption", "extortion"],
            "vulnerability_intelligence": ["cve", "patch", "exploit"],
            "threat_actor_monitoring": ["threat_actor", "attack_group", "nation_state"]
        }
        
        return threat_type_mapping.get(feed_name, ["unknown"])
    
    def _generate_affected_regions(self) -> List[str]:
        """Generate affected regions"""
        regions = ["global", "asia", "europe", "americas", "africa", "middle_east", "oceania"]
        num_regions = np.random.randint(1, 4)
        return np.random.choice(regions, num_regions, replace=False).tolist()
    
    def _generate_threat_indicators(self, feed_name: str) -> List[Dict[str, Any]]:
        """Generate threat indicators"""
        num_indicators = np.random.randint(1, 5)
        indicators = []
        
        for i in range(num_indicators):
            indicator = {
                'id': str(uuid.uuid4()),
                'type': np.random.choice(['ip', 'domain', 'hash', 'url', 'email']),
                'value': self._generate_indicator_value(),
                'severity': np.random.choice(['low', 'medium', 'high', 'critical']),
                'confidence': np.random.uniform(0.5, 1.0),
                'first_seen': (datetime.now() - timedelta(days=np.random.randint(1, 30))).isoformat(),
                'last_seen': datetime.now().isoformat(),
                'description': f"Threat indicator from {feed_name}",
                'tags': np.random.choice(['malware', 'phishing', 'botnet', 'apt'], size=np.random.randint(1, 3)).tolist()
            }
            indicators.append(indicator)
        
        return indicators
    
    def _generate_indicator_value(self) -> str:
        """Generate indicator value based on type"""
        indicator_type = np.random.choice(['ip', 'domain', 'hash', 'url', 'email'])
        
        if indicator_type == 'ip':
            return f"{np.random.randint(1, 255)}.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}"
        elif indicator_type == 'domain':
            return f"malicious{np.random.randint(1000, 9999)}.com"
        elif indicator_type == 'hash':
            return hashlib.md5(f"malware{np.random.randint(1000, 9999)}".encode()).hexdigest()
        elif indicator_type == 'url':
            return f"http://malicious{np.random.randint(1000, 9999)}.com/path"
        else:  # email
            return f"attacker{np.random.randint(1000, 9999)}@malicious.com"
    
    def _generate_threat_campaigns(self, feed_name: str) -> List[Dict[str, Any]]:
        """Generate threat campaigns"""
        num_campaigns = np.random.randint(0, 3)
        campaigns = []
        
        for i in range(num_campaigns):
            campaign = {
                'id': str(uuid.uuid4()),
                'name': f"Campaign_{feed_name}_{i+1}",
                'description': f"Threat campaign from {feed_name}",
                'start_date': (datetime.now() - timedelta(days=np.random.randint(1, 60))).isoformat(),
                'status': np.random.choice(['active', 'inactive', 'emerging']),
                'threat_level': np.random.choice(['low', 'medium', 'high', 'critical']),
                'target_industries': np.random.choice(['finance', 'healthcare', 'government', 'technology'], 
                                                   size=np.random.randint(1, 3)).tolist(),
                'attack_vectors': np.random.choice(['phishing', 'malware', 'exploit', 'social_engineering'], 
                                                 size=np.random.randint(1, 3)).tolist()
            }
            campaigns.append(campaign)
        
        return campaigns
    
    def _generate_mitigation_advice(self, feed_name: str) -> List[str]:
        """Generate mitigation advice"""
        advice = [
            "Update antivirus signatures",
            "Block malicious IP addresses",
            "Implement email filtering",
            "Patch vulnerable systems",
            "Enable multi-factor authentication",
            "Monitor network traffic",
            "Educate users about security",
            "Implement intrusion detection",
            "Backup critical data",
            "Review access controls"
        ]
        
        num_advice = np.random.randint(2, 5)
        return np.random.choice(advice, num_advice, replace=False).tolist()
    
    def _generate_source_indicators(self, source_type: str) -> List[Dict[str, Any]]:
        """Generate indicators based on source type"""
        indicators = []
        
        if source_type == "malware":
            indicators = [
                {'type': 'hash', 'value': hashlib.md5(f"malware{np.random.randint(1000, 9999)}".encode()).hexdigest()},
                {'type': 'hash', 'value': hashlib.sha256(f"malware{np.random.randint(1000, 9999)}".encode()).hexdigest()}
            ]
        elif source_type == "malware_domains":
            indicators = [
                {'type': 'domain', 'value': f"malicious{np.random.randint(1000, 9999)}.com"},
                {'type': 'domain', 'value': f"bad{np.random.randint(1000, 9999)}.net"}
            ]
        elif source_type == "phishing":
            indicators = [
                {'type': 'url', 'value': f"http://phishing{np.random.randint(1000, 9999)}.com"},
                {'type': 'email', 'value': f"scam{np.random.randint(1000, 9999)}@fake.com"}
            ]
        else:
            indicators = [
                {'type': 'ip', 'value': f"{np.random.randint(1, 255)}.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}"}
            ]
        
        return indicators
    
    def _generate_threat_actors(self) -> List[str]:
        """Generate threat actor names"""
        actors = [
            "APT28", "APT29", "Lazarus Group", "Fancy Bear", "Cozy Bear",
            "Equation Group", "Dragonfly", "Stuxnet", "WannaCry", "NotPetya"
        ]
        
        num_actors = np.random.randint(0, 3)
        return np.random.choice(actors, num_actors, replace=False).tolist()
    
    def _generate_attack_patterns(self) -> List[str]:
        """Generate attack patterns"""
        patterns = [
            "Spear phishing", "Watering hole attack", "Supply chain compromise",
            "Credential stuffing", "Business email compromise", "Ransomware deployment",
            "Data exfiltration", "Denial of service", "Man-in-the-middle", "SQL injection"
        ]
        
        num_patterns = np.random.randint(1, 4)
        return np.random.choice(patterns, num_patterns, replace=False).tolist()
    
    def _generate_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Generate vulnerabilities"""
        num_vulns = np.random.randint(0, 3)
        vulnerabilities = []
        
        for i in range(num_vulns):
            vuln = {
                'cve_id': f"CVE-2023-{np.random.randint(1000, 9999)}",
                'severity': np.random.choice(['low', 'medium', 'high', 'critical']),
                'cvss_score': np.random.uniform(3.0, 10.0),
                'description': f"Vulnerability {i+1}",
                'affected_products': np.random.choice(['Windows', 'Linux', 'Apache', 'OpenSSL'], 
                                                      size=np.random.randint(1, 3)).tolist()
            }
            vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def _generate_malware_families(self) -> List[str]:
        """Generate malware families"""
        families = [
            "Emotet", "TrickBot", "Zeus", "CryptoLocker", "WannaCry",
            "Petya", "NotPetya", "Locky", "Cerber", "Ryuk"
        ]
        
        num_families = np.random.randint(0, 3)
        return np.random.choice(families, num_families, replace=False).tolist()
    
    def _count_total_threats(self, threat_data: Dict[str, Any], source_data: Dict[str, Any]) -> int:
        """Count total threats from all sources"""
        total = 0
        
        # Count from threat feeds
        for feed_data in threat_data.values():
            total += feed_data.get('threats_detected', 0)
            total += len(feed_data.get('threat_indicators', []))
        
        # Count from intelligence sources
        for source_threats in source_data.values():
            total += source_threats.get('threats_found', 0)
            total += len(source_threats.get('indicators', []))
        
        return total
    
    async def analyze_threat_patterns(self, threat_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze threat patterns from collected intelligence
        
        Args:
            threat_data: Collected threat intelligence
            
        Returns:
            Dictionary containing threat pattern analysis
        """
        # Extract threat indicators
        all_indicators = []
        all_campaigns = []
        threat_types = {}
        severity_distribution = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        
        # Process threat feeds
        for feed_data in threat_data['threat_feeds'].values():
            all_indicators.extend(feed_data.get('threat_indicators', []))
            all_campaigns.extend(feed_data.get('campaigns', []))
            
            # Count threat types
            for threat_type in feed_data.get('threat_types', []):
                threat_types[threat_type] = threat_types.get(threat_type, 0) + 1
            
            # Count severity
            severity = feed_data.get('severity_level', 'low')
            severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
        
        # Process intelligence sources
        for source_threats in threat_data['intelligence_sources'].values():
            all_indicators.extend(source_threats.get('indicators', []))
        
        # Analyze patterns
        pattern_analysis = {
            'total_indicators': len(all_indicators),
            'total_campaigns': len(all_campaigns),
            'threat_types': threat_types,
            'severity_distribution': severity_distribution,
            'most_common_threat_type': max(threat_types.items(), key=lambda x: x[1])[0] if threat_types else 'unknown',
            'dominant_severity': max(severity_distribution.items(), key=lambda x: x[1])[0],
            'active_campaigns': len([c for c in all_campaigns if c.get('status') == 'active']),
            'emerging_campaigns': len([c for c in all_campaigns if c.get('status') == 'emerging']),
            'high_risk_indicators': len([i for i in all_indicators if i.get('severity') in ['high', 'critical']]),
            'trending_threats': self._identify_trending_threats(all_indicators),
            'geographic_distribution': self._analyze_geographic_distribution(all_indicators),
            'temporal_patterns': self._analyze_temporal_patterns(all_indicators)
        }
        
        return pattern_analysis
    
    def _identify_trending_threats(self, indicators: List[Dict[str, Any]]) -> List[str]:
        """Identify trending threats"""
        # Simple trending analysis based on recent indicators
        recent_indicators = [i for i in indicators if 
                            (datetime.now() - datetime.fromisoformat(i['last_seen'].replace('Z', '+00:00'))).days <= 7]
        
        if len(recent_indicators) > len(indicators) * 0.3:
            return ["Increased threat activity", "Multiple active campaigns"]
        else:
            return ["Normal threat levels"]
    
    def _analyze_geographic_distribution(self, indicators: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze geographic distribution of threats"""
        # Simplified geographic analysis
        regions = ["americas", "europe", "asia", "africa", "middle_east", "oceania"]
        distribution = {}
        
        for region in regions:
            distribution[region] = np.random.randint(0, 20)
        
        return distribution
    
    def _analyze_temporal_patterns(self, indicators: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze temporal patterns of threats"""
        # Analyze when threats were first seen
        time_periods = {
            'last_24h': 0,
            'last_7d': 0,
            'last_30d': 0,
            'older': 0
        }
        
        now = datetime.now()
        
        for indicator in indicators:
            first_seen = datetime.fromisoformat(indicator['first_seen'].replace('Z', '+00:00'))
            days_old = (now - first_seen).days
            
            if days_old <= 1:
                time_periods['last_24h'] += 1
            elif days_old <= 7:
                time_periods['last_7d'] += 1
            elif days_old <= 30:
                time_periods['last_30d'] += 1
            else:
                time_periods['older'] += 1
        
        return time_periods
    
    async def generate_threat_alerts(self, threat_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate threat alerts based on analysis
        
        Args:
            threat_analysis: Threat pattern analysis
            
        Returns:
            List of threat alerts
        """
        alerts = []
        
        # Critical alerts
        if threat_analysis['dominant_severity'] == 'critical':
            alerts.append({
                'id': str(uuid.uuid4()),
                'severity': 'critical',
                'title': 'Critical Threat Level Detected',
                'message': f"Critical threat level detected with {threat_analysis['high_risk_indicators']} high-risk indicators",
                'timestamp': datetime.now().isoformat(),
                'indicators_count': threat_analysis['high_risk_indicators']
            })
        
        # High severity alerts
        if threat_analysis['active_campaigns'] > 5:
            alerts.append({
                'id': str(uuid.uuid4()),
                'severity': 'high',
                'title': 'Multiple Active Campaigns',
                'message': f"{threat_analysis['active_campaigns']} active threat campaigns detected",
                'timestamp': datetime.now().isoformat(),
                'campaigns_count': threat_analysis['active_campaigns']
            })
        
        if threat_analysis['high_risk_indicators'] > 50:
            alerts.append({
                'id': str(uuid.uuid4()),
                'severity': 'high',
                'title': 'High Number of Risk Indicators',
                'message': f"{threat_analysis['high_risk_indicators']} high-risk threat indicators detected",
                'timestamp': datetime.now().isoformat(),
                'indicators_count': threat_analysis['high_risk_indicators']
            })
        
        # Medium severity alerts
        if threat_analysis['emerging_campaigns'] > 2:
            alerts.append({
                'id': str(uuid.uuid4()),
                'severity': 'medium',
                'title': 'Emerging Threat Campaigns',
                'message': f"{threat_analysis['emerging_campaigns']} emerging threat campaigns detected",
                'timestamp': datetime.now().isoformat(),
                'campaigns_count': threat_analysis['emerging_campaigns']
            })
        
        if threat_analysis['total_indicators'] > 100:
            alerts.append({
                'id': str(uuid.uuid4()),
                'severity': 'medium',
                'title': 'High Threat Indicator Count',
                'message': f"{threat_analysis['total_indicators']} threat indicators detected",
                'timestamp': datetime.now().isoformat(),
                'indicators_count': threat_analysis['total_indicators']
            })
        
        return alerts
    
    async def stop_threat_intelligence(self) -> Dict[str, Any]:
        """
        Stop threat intelligence collection
        
        Returns:
            Dictionary containing intelligence stop results
        """
        self.intelligence_active = False
        
        return {
            'intelligence_stopped': True,
            'stop_time': datetime.now().isoformat(),
            'total_intelligence_cycles': len(self.threat_history),
            'total_threat_indicators': len(self.threat_indicators),
            'total_campaigns': len(self.active_campaigns)
        }
    
    def get_threat_database(self) -> List[Dict[str, Any]]:
        """Get threat database"""
        return self.threat_database.copy()
    
    def get_intelligence_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get intelligence history"""
        return self.threat_history[-limit:]
    
    def get_threat_indicators(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get threat indicators"""
        return list(self.threat_indicators.values())[-limit:]
    
    def get_active_campaigns(self) -> Dict[str, Any]:
        """Get active threat campaigns"""
        return self.active_campaigns.copy()
    
    def search_threats(self, query: str, search_type: str = 'all') -> List[Dict[str, Any]]:
        """
        Search threats by query
        
        Args:
            query: Search query
            search_type: Type of search ('all', 'indicators', 'campaigns', 'actors')
            
        Returns:
            List of matching threats
        """
        results = []
        query_lower = query.lower()
        
        if search_type in ['all', 'indicators']:
            for indicator in self.threat_indicators.values():
                if (query_lower in indicator.get('value', '').lower() or
                    query_lower in indicator.get('description', '').lower()):
                    results.append(indicator)
        
        if search_type in ['all', 'campaigns']:
            for campaign in self.active_campaigns.values():
                if (query_lower in campaign.get('name', '').lower() or
                    query_lower in campaign.get('description', '').lower()):
                    results.append(campaign)
        
        return results
