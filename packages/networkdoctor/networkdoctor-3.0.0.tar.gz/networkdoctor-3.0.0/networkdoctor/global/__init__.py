"""
NetworkDoctor Global - Global Network Intelligence and Monitoring
"""

__version__ = "3.0.0"
__author__ = "frankvena25"
__email__ = "frankvenas25@gmail.com"

# Global Network Intelligence Modules
from .global_monitor import GlobalNetworkMonitor
from .threat_intelligence import GlobalThreatIntelligence
from .predictive_ai import PredictiveNetworkAI
from .global_orchestrator import GlobalOrchestrator
from .distributed_nodes import DistributedNetworkNodes

__all__ = [
    'GlobalNetworkMonitor',
    'GlobalThreatIntelligence',
    'PredictiveNetworkAI',
    'GlobalOrchestrator',
    'DistributedNetworkNodes'
]
