"""
NetworkDoctor Quantum - Quantum-Enhanced Network Analysis
"""

__version__ = "3.0.0"
__author__ = "frankvena25"
__email__ = "frankvenas25@gmail.com"

# Quantum Network Analysis Modules
from .quantum_analyzer import QuantumNetworkAnalyzer
from .quantum_optimizer import QuantumNetworkOptimizer
from .quantum_security import QuantumSecurity
from .quantum_tunnel import QuantumTunnel
from .quantum_error_correction import QuantumErrorCorrection
from .quantum_key import QuantumKey
from .quantum_blockchain import QuantumBlockchain

__all__ = [
    'QuantumNetworkAnalyzer',
    'QuantumNetworkOptimizer', 
    'QuantumSecurity',
    'QuantumTunnel',
    'QuantumErrorCorrection',
    'QuantumKey',
    'QuantumBlockchain'
]
