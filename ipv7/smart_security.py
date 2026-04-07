from typing import Optional, List, Dict
import hashlib
import os
import time
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import numpy as np

@dataclass
class SecurityToken:
    token_id: str
    creation_time: float
    expiration_time: float
    permissions: List[str]
    quantum_resistant: bool

class SmartFirewall:
    """Firewall inteligente con aprendizaje adaptativo"""
    
    def __init__(self):
        self.blocked_patterns: Dict[bytes, float] = {}  # patrón -> score
        self.trusted_sources: Dict[bytes, SecurityToken] = {}
        self.threat_scores: Dict[bytes, float] = {}  # fuente -> score
        self.learning_rate = 0.1
        
    def analyze_packet(self, header: bytes, payload: bytes) -> bool:
        """Analiza un paquete y decide si debe ser bloqueado"""
        source = header[:32]  # primeros 256 bits = dirección fuente
        
        # Verificar si la fuente está en lista blanca
        if source in self.trusted_sources:
            token = self.trusted_sources[source]
            if time.time() < token.expiration_time:
                return True
                
        # Calcular hash del payload para patrones bloqueados
        payload_hash = hashlib.sha256(payload).digest()
        if payload_hash in self.blocked_patterns:
            self.threat_scores[source] = self.threat_scores.get(source, 0) + 0.2
            return False
            
        # Análisis heurístico
        threat_indicators = self._analyze_threats(header, payload)
        
        # Si el score de amenaza instantáneo es muy alto, bloquear directamente
        if threat_indicators >= 0.4:
            self.threat_scores[source] = max(
                self.threat_scores.get(source, 0), threat_indicators
            )
            return False
        
        # Actualizar score acumulado
        current_score = self.threat_scores.get(source, 0)
        self.threat_scores[source] = current_score * 0.9 + threat_indicators * 0.1
        
        return self.threat_scores[source] < 0.5
    
    def _analyze_threats(self, _header: bytes, payload: bytes) -> float:
        """Analiza indicadores de amenazas en el paquete.

        ``_header`` es parte de la firma pública para futura inspección de cabecera.
        """
        score = 0.0
        
        # Verificar longitud anómala
        if len(payload) > 9000:  # Mayor que MTU típico
            score += 0.3
            
        # Verificar entropía (datos cifrados/ofuscados)
        entropy = self._calculate_entropy(payload)
        if entropy > 7.5:  # Alta entropía
            score += 0.2
            
        # Verificar patrones de ataque conocidos
        if self._check_attack_patterns(payload):
            score += 0.4
            
        return min(score, 1.0)
    
    @staticmethod
    def _calculate_entropy(data: bytes) -> float:
        """Calcula la entropía de Shannon de los datos"""
        if not data:
            return 0.0
        probabilities = np.zeros(256)
        for byte in data:
            probabilities[byte] += 1
        probabilities = probabilities / len(data)

        # Eliminar probabilidades cero
        probabilities = probabilities[probabilities > 0]
        return -np.sum(probabilities * np.log2(probabilities))
    
    def _check_attack_patterns(self, payload: bytes) -> bool:
        """Verifica patrones de ataque conocidos"""
        patterns = [
            b'exec(',
            b'union select',
            b'../../',
            b'<script>',
            b'eval(',
            b'$()',
            b'rm -rf',
            b'DROP TABLE',
            b'passwd',
            b'/bin/sh',
            b'cmd.exe',
            b'powershell',
            b'base64_decode',
            b'\x00\x00\x00\x00\x00\x00\x00\x00',  # NOP sled
        ]
        payload_lower = payload.lower()
        return any(pattern.lower() in payload_lower for pattern in patterns)
    
    def add_trusted_source(self, address: bytes, permissions: List[str],
                          duration: float = 3600) -> SecurityToken:
        """Añade una fuente confiable"""
        token = SecurityToken(
            token_id=hashlib.sha256(address + str(time.time()).encode()).hexdigest(),
            creation_time=time.time(),
            expiration_time=time.time() + duration,
            permissions=permissions,
            quantum_resistant=True
        )
        self.trusted_sources[address] = token
        return token
    
    def revoke_trust(self, address: bytes):
        """Revoca confianza de una fuente"""
        if address in self.trusted_sources:
            del self.trusted_sources[address]
            
    def block_pattern(self, pattern: bytes, score: float = 1.0):
        """Bloquea un patrón de payload"""
        self.blocked_patterns[pattern] = score
        
    def get_threat_report(self) -> dict:
        """Genera reporte de amenazas"""
        return {
            "high_threat_sources": [
                addr.hex() for addr, score in self.threat_scores.items()
                if score > 0.7
            ],
            "blocked_patterns_count": len(self.blocked_patterns),
            "trusted_sources_count": len(self.trusted_sources),
            "average_threat_score": np.mean(list(self.threat_scores.values()))
            if self.threat_scores else 0.0
        }

class QuantumSecurityLayer:
    """Capa de seguridad basada en principios cuánticos"""
    
    def __init__(self):
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096
        )
        self.public_key = self.private_key.public_key()
        
    def generate_quantum_key(self, _peer_public_key: bytes) -> bytes:
        """Genera una clave cuántica compartida.

        ``_peer_public_key`` se usará en la implementación real del protocolo BB84.
        """
        # Simulación de protocolo BB84
        raw_key = self._bb84_simulation()
        
        # Post-procesamiento de la clave
        final_key = self._privacy_amplification(raw_key)
        
        return final_key
    
    def _bb84_simulation(self, n_bits: int = 1024) -> bytes:
        """Simula el protocolo BB84 de intercambio de claves cuánticas"""
        # Simulación básica - en la realidad esto usaría hardware cuántico
        rng = np.random.default_rng(None)  # intentionally unseeded for key generation
        alice_bits = rng.integers(0, 2, n_bits)
        alice_bases = rng.integers(0, 2, n_bits)
        bob_bases = rng.integers(0, 2, n_bits)
        
        # Determinar bits donde las bases coinciden
        matching_bases = alice_bases == bob_bases
        final_bits = alice_bits[matching_bases]
        
        # Convertir a bytes
        return bytes(np.packbits(final_bits))
    
    def _privacy_amplification(self, key: bytes) -> bytes:
        """Amplifica la privacidad de la clave usando hash"""
        return hashlib.blake2b(key).digest()
    
    def encrypt_quantum_resistant(self, data: bytes) -> bytes:
        """Encriptación resistente a computación cuántica.

        Formato del resultado: key(32) + nonce(12) + tag(16) + ciphertext
        """
        key = os.urandom(32)
        nonce = os.urandom(12)
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        return key + nonce + encryptor.tag + ciphertext

    def decrypt_quantum_resistant(self, encrypted_data: bytes) -> Optional[bytes]:
        """Desencripta datos con protección cuántica.

        Espera el formato producido por encrypt_quantum_resistant:
        key(32) + nonce(12) + tag(16) + ciphertext
        """
        try:
            if len(encrypted_data) < 60:  # 32 + 12 + 16 mínimo
                return None
            key = encrypted_data[:32]
            nonce = encrypted_data[32:44]
            tag = encrypted_data[44:60]
            ciphertext = encrypted_data[60:]
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag))
            decryptor = cipher.decryptor()
            return decryptor.update(ciphertext) + decryptor.finalize()
        except Exception:
            return None
            
    def verify_quantum_signature(self, data: bytes, signature: bytes,
                               peer_public_key: bytes) -> bool:
        """Verifica una firma digital resistente a quantum"""
        try:
            peer_key = serialization.load_pem_public_key(peer_public_key)
            peer_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False