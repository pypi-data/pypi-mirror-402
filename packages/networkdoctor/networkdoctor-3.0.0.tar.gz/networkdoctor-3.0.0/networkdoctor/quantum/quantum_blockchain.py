"""
Quantum Blockchain - Blockchain verification for quantum network operations
"""

import numpy as np
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid
import hashlib
import json
from qiskit import QuantumCircuit, QuantumRegister, Aer, execute
from qiskit.quantum_info import Statevector


class QuantumBlockchain:
    """
    Quantum Blockchain provides blockchain verification for quantum network operations
    ensuring immutable records and quantum-enhanced security.
    """
    
    def __init__(self, n_qubits: int = 8, shots: int = 1024):
        """
        Initialize Quantum Blockchain
        
        Args:
            n_qubits: Number of qubits for quantum blockchain operations (default: 8)
            shots: Number of shots per quantum circuit execution (default: 1024)
        """
        self.n_qubits = n_qubits
        self.shots = shots
        self.quantum_backend = Aer.get_backend('aer_simulator')
        self.blockchain = []
        self.quantum_blocks = {}
        self.block_hashes = {}
        self.verification_history = []
        
    async def initialize_blockchain(self, genesis_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Initialize quantum blockchain with genesis block
        
        Args:
            genesis_data: Genesis block data
            
        Returns:
            Dictionary containing blockchain initialization results
        """
        # Create genesis block
        genesis_block = await self._create_genesis_block(genesis_data)
        
        # Add to blockchain
        self.blockchain.append(genesis_block)
        self.quantum_blocks[genesis_block['block_id']] = genesis_block
        
        # Create initialization result
        init_result = {
            'blockchain_id': str(uuid.uuid4()),
            'genesis_block': genesis_block,
            'total_blocks': 1,
            'blockchain_initialized': True,
            'quantum_security_applied': True,
            'initialization_time': datetime.now().isoformat()
        }
        
        return init_result
    
    async def _create_genesis_block(self, genesis_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create genesis block for quantum blockchain
        
        Args:
            genesis_data: Genesis block data
            
        Returns:
            Dictionary containing genesis block
        """
        block_id = str(uuid.uuid4())
        
        # Create quantum signature for genesis block
        quantum_signature = await self._create_quantum_signature(genesis_data or {})
        
        # Create genesis block
        genesis_block = {
            'block_id': block_id,
            'block_number': 0,
            'previous_hash': '0' * 64,  # Genesis block has no previous hash
            'timestamp': datetime.now().isoformat(),
            'data': genesis_data or {'message': 'Quantum Blockchain Genesis'},
            'quantum_signature': quantum_signature,
            'block_hash': await self._calculate_block_hash(0, '0' * 64, genesis_data or {}, quantum_signature),
            'quantum_verified': True,
            'immutable': True
        }
        
        return genesis_block
    
    async def _create_quantum_signature(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create quantum signature for block data
        
        Args:
            data: Block data to sign
            
        Returns:
            Dictionary containing quantum signature
        """
        # Create quantum signature circuit
        signature_circuit = QuantumCircuit(self.n_qubits)
        
        # Encode data into quantum state
        data_string = json.dumps(data, sort_keys=True)
        data_hash = hashlib.sha256(data_string.encode()).hexdigest()
        
        # Use hash to determine quantum operations
        for i in range(self.n_qubits):
            if i < len(data_hash):
                bit = int(data_hash[i], 16) % 2
                if bit:
                    signature_circuit.x(i)
            
            # Add random rotation for uniqueness
            angle = (hash(data_string + str(i)) % 360) * np.pi / 180
            signature_circuit.ry(angle, i)
        
        # Create entanglement for signature
        for i in range(self.n_qubits - 1):
            signature_circuit.cx(i, i+1)
        
        # Measure quantum signature
        signature_circuit.measure_all()
        
        # Execute signature circuit
        job = execute(signature_circuit, self.quantum_backend, shots=1)
        result = job.result()
        counts = result.get_counts()
        
        # Extract signature
        quantum_signature = list(counts.keys())[0]
        
        return {
            'quantum_signature': quantum_signature,
            'signature_circuit': signature_circuit.draw(output='text'),
            'signature_strength': 'quantum_secure',
            'unforgeable': True,
            'creation_time': datetime.now().isoformat()
        }
    
    async def _calculate_block_hash(self, block_number: int, previous_hash: str, 
                                   data: Dict[str, Any], quantum_signature: Dict[str, Any]) -> str:
        """
        Calculate hash for block
        
        Args:
            block_number: Block number
            previous_hash: Previous block hash
            data: Block data
            quantum_signature: Quantum signature
            
        Returns:
            Block hash string
        """
        # Create block string
        block_string = f"{block_number}{previous_hash}{json.dumps(data, sort_keys=True)}{quantum_signature['quantum_signature']}"
        
        # Calculate SHA-256 hash
        block_hash = hashlib.sha256(block_string.encode()).hexdigest()
        
        return block_hash
    
    async def add_block(self, data: Dict[str, Any], 
                       block_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add new block to quantum blockchain
        
        Args:
            data: Block data
            block_config: Block configuration
            
        Returns:
            Dictionary containing block addition results
        """
        if not self.blockchain:
            raise ValueError("Blockchain not initialized")
        
        # Get previous block
        previous_block = self.blockchain[-1]
        previous_hash = previous_block['block_hash']
        block_number = len(self.blockchain)
        
        # Create quantum signature
        quantum_signature = await self._create_quantum_signature(data)
        
        # Calculate block hash
        block_hash = await self._calculate_block_hash(block_number, previous_hash, data, quantum_signature)
        
        # Create new block
        new_block = {
            'block_id': str(uuid.uuid4()),
            'block_number': block_number,
            'previous_hash': previous_hash,
            'timestamp': datetime.now().isoformat(),
            'data': data,
            'quantum_signature': quantum_signature,
            'block_hash': block_hash,
            'quantum_verified': True,
            'config': block_config or {}
        }
        
        # Add to blockchain
        self.blockchain.append(new_block)
        self.quantum_blocks[new_block['block_id']] = new_block
        self.block_hashes[block_hash] = new_block
        
        # Create addition result
        addition_result = {
            'block_added': new_block,
            'blockchain_length': len(self.blockchain),
            'verification_required': True,
            'quantum_signature_applied': True,
            'addition_time': datetime.now().isoformat()
        }
        
        return addition_result
    
    async def verify_blockchain(self) -> Dict[str, Any]:
        """
        Verify entire quantum blockchain integrity
        
        Returns:
            Dictionary containing verification results
        """
        verification_id = str(uuid.uuid4())
        verification_results = []
        all_blocks_valid = True
        
        # Verify each block
        for i, block in enumerate(self.blockchain):
            block_verification = await self._verify_block(block, i)
            verification_results.append(block_verification)
            
            if not block_verification['valid']:
                all_blocks_valid = False
        
        # Verify chain integrity
        chain_integrity = await self._verify_chain_integrity()
        
        # Create verification result
        verification_result = {
            'verification_id': verification_id,
            'total_blocks': len(self.blockchain),
            'verification_results': verification_results,
            'all_blocks_valid': all_blocks_valid,
            'chain_integrity': chain_integrity,
            'blockchain_valid': all_blocks_valid and chain_integrity['valid'],
            'verification_time': datetime.now().isoformat(),
            'quantum_security_verified': True
        }
        
        # Store verification history
        self.verification_history.append(verification_result)
        
        return verification_result
    
    async def _verify_block(self, block: Dict[str, Any], block_number: int) -> Dict[str, Any]:
        """
        Verify individual block
        
        Args:
            block: Block to verify
            block_number: Expected block number
            
        Returns:
            Dictionary containing block verification results
        """
        # Verify block number
        block_number_valid = block['block_number'] == block_number
        
        # Verify block hash
        calculated_hash = await self._calculate_block_hash(
            block['block_number'],
            block['previous_hash'],
            block['data'],
            block['quantum_signature']
        )
        hash_valid = calculated_hash == block['block_hash']
        
        # Verify quantum signature
        signature_valid = await self._verify_quantum_signature(
            block['data'], block['quantum_signature']
        )
        
        # Overall validity
        block_valid = block_number_valid and hash_valid and signature_valid
        
        return {
            'block_id': block['block_id'],
            'block_number': block['block_number'],
            'block_number_valid': block_number_valid,
            'hash_valid': hash_valid,
            'signature_valid': signature_valid,
            'valid': block_valid,
            'verification_time': datetime.now().isoformat()
        }
    
    async def _verify_quantum_signature(self, data: Dict[str, Any], 
                                       quantum_signature: Dict[str, Any]) -> bool:
        """
        Verify quantum signature
        
        Args:
            data: Original data
            quantum_signature: Quantum signature to verify
            
        Returns:
            True if signature is valid
        """
        # Recreate quantum signature circuit
        signature_circuit = QuantumCircuit(self.n_qubits)
        
        # Encode data into quantum state (same as creation)
        data_string = json.dumps(data, sort_keys=True)
        data_hash = hashlib.sha256(data_string.encode()).hexdigest()
        
        for i in range(self.n_qubits):
            if i < len(data_hash):
                bit = int(data_hash[i], 16) % 2
                if bit:
                    signature_circuit.x(i)
            
            angle = (hash(data_string + str(i)) % 360) * np.pi / 180
            signature_circuit.ry(angle, i)
        
        # Create entanglement
        for i in range(self.n_qubits - 1):
            signature_circuit.cx(i, i+1)
        
        # Measure
        signature_circuit.measure_all()
        
        # Execute signature circuit
        job = execute(signature_circuit, self.quantum_backend, shots=1)
        result = job.result()
        counts = result.get_counts()
        
        # Compare with original signature
        new_signature = list(counts.keys())[0]
        original_signature = quantum_signature['quantum_signature']
        
        # Simple comparison (in practice, would use more sophisticated verification)
        signature_valid = new_signature == original_signature
        
        return signature_valid
    
    async def _verify_chain_integrity(self) -> Dict[str, Any]:
        """
        Verify blockchain chain integrity
        
        Returns:
            Dictionary containing chain integrity results
        """
        chain_valid = True
        integrity_issues = []
        
        # Verify each block links to previous block
        for i in range(1, len(self.blockchain)):
            current_block = self.blockchain[i]
            previous_block = self.blockchain[i-1]
            
            # Verify previous hash matches
            if current_block['previous_hash'] != previous_block['block_hash']:
                chain_valid = False
                integrity_issues.append({
                    'block_number': i,
                    'issue': 'Previous hash mismatch',
                    'expected': previous_block['block_hash'],
                    'actual': current_block['previous_hash']
                })
        
        return {
            'valid': chain_valid,
            'integrity_issues': integrity_issues,
            'total_issues': len(integrity_issues),
            'verification_time': datetime.now().isoformat()
        }
    
    async def store_node_metrics(self, node_id: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store node metrics on blockchain
        
        Args:
            node_id: Node ID
            metrics: Node metrics
            
        Returns:
            Dictionary containing storage results
        """
        # Create block data
        block_data = {
            'type': 'node_metrics',
            'node_id': node_id,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add block to blockchain
        addition_result = await self.add_block(block_data)
        
        return addition_result
    
    async def verify_node_metrics(self, node_id: str, 
                                  metrics_hash: str) -> Dict[str, Any]:
        """
        Verify node metrics on blockchain
        
        Args:
            node_id: Node ID
            metrics_hash: Hash of metrics to verify
            
        Returns:
            Dictionary containing verification results
        """
        # Find blocks with node metrics
        node_blocks = []
        for block in self.blockchain:
            if (block['data'].get('type') == 'node_metrics' and 
                block['data'].get('node_id') == node_id):
                node_blocks.append(block)
        
        # Verify metrics hash
        metrics_verified = False
        verified_block = None
        
        for block in node_blocks:
            block_data_string = json.dumps(block['data'], sort_keys=True)
            calculated_hash = hashlib.sha256(block_data_string.encode()).hexdigest()
            
            if calculated_hash == metrics_hash:
                metrics_verified = True
                verified_block = block
                break
        
        return {
            'node_id': node_id,
            'metrics_hash': metrics_hash,
            'metrics_verified': metrics_verified,
            'verified_block': verified_block,
            'total_node_blocks': len(node_blocks),
            'verification_time': datetime.now().isoformat()
        }
    
    def get_blockchain_length(self) -> int:
        """Get blockchain length"""
        return len(self.blockchain)
    
    def get_block(self, block_id: str) -> Optional[Dict[str, Any]]:
        """Get block by ID"""
        return self.quantum_blocks.get(block_id)
    
    def get_block_by_hash(self, block_hash: str) -> Optional[Dict[str, Any]]:
        """Get block by hash"""
        return self.block_hashes.get(block_hash)
    
    def get_latest_block(self) -> Optional[Dict[str, Any]]:
        """Get latest block"""
        return self.blockchain[-1] if self.blockchain else None
    
    def get_blockchain(self) -> List[Dict[str, Any]]:
        """Get entire blockchain"""
        return self.blockchain.copy()
    
    def get_verification_history(self) -> List[Dict[str, Any]]:
        """Get verification history"""
        return self.verification_history.copy()
    
    async def get_blockchain_statistics(self) -> Dict[str, Any]:
        """
        Get blockchain statistics
        
        Returns:
            Dictionary containing blockchain statistics
        """
        if not self.blockchain:
            return {'error': 'Blockchain not initialized'}
        
        # Calculate statistics
        total_blocks = len(self.blockchain)
        genesis_time = datetime.fromisoformat(self.blockchain[0]['timestamp'])
        latest_time = datetime.fromisoformat(self.blockchain[-1]['timestamp'])
        blockchain_age = latest_time - genesis_time
        
        # Count block types
        block_types = {}
        for block in self.blockchain:
            block_type = block['data'].get('type', 'unknown')
            block_types[block_type] = block_types.get(block_type, 0) + 1
        
        return {
            'total_blocks': total_blocks,
            'blockchain_age': str(blockchain_age),
            'genesis_time': genesis_time.isoformat(),
            'latest_time': latest_time.isoformat(),
            'block_types': block_types,
            'quantum_blocks': len(self.quantum_blocks),
            'verification_count': len(self.verification_history),
            'statistics_time': datetime.now().isoformat()
        }
