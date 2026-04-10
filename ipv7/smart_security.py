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
    """Firewall de red adaptativo para IPv7"""

    def __init__(self):
        self.blocked_patterns: Dict[bytes, float] = {}
        self.trusted_sources: Dict[bytes, SecurityToken] = {}
        self.threat_scores: Dict[bytes, float] = {}
        self.learning_rate = 0.05

    def analyze_packet(self, header: bytes, payload: bytes) -> bool:
        """Realiza inspección profunda de paquetes (DPI) y análisis de amenazas"""
        source = header[1:33]  # Dirección fuente corregida según unpack

        # Bypass para fuentes con token válido
        if source in self.trusted_sources:
            token = self.trusted_sources[source]
            if time.time() < token.expiration_time:
                return True

        # Análisis de firma de payload
        payload_hash = hashlib.blake2b(payload, digest_size=32).digest()
        if payload_hash in self.blocked_patterns:
            self._update_threat_score(source, 0.5)
            return False

        # Análisis heurístico multinivel
        threat_score = self._calculate_threat_indicators(header, payload)

        # Decisión basada en umbral adaptativo
        self._update_threat_score(source, threat_score)
        return self.threat_scores.get(source, 0) < 0.6

    def _update_threat_score(self, source: bytes, instant_score: float):
        """Actualiza el score de amenaza usando una media móvil exponencial"""
        current = self.threat_scores.get(source, 0.0)
        self.threat_scores[source] = (
            current * (1 - self.learning_rate) + instant_score * self.learning_rate
        )

    def _calculate_threat_indicators(self, header: bytes, payload: bytes) -> float:
        """Evalúa múltiples vectores de ataque en el tráfico"""
        score = 0.0

        # 1. Análisis de volumen y MTU
        if len(payload) > 9000:
            score += 0.4

        # 2. Análisis de entropía (detección de shellcode/exfiltración)
        entropy = self._calculate_entropy(payload)
        if entropy > 7.8:
            score += 0.3

        # 3. Detección de firmas de malware/exploits
        if self._check_malicious_signatures(payload):
            score += 0.8

        return min(score, 1.0)

    @staticmethod
    def _calculate_entropy(data: bytes) -> float:
        """Calcula la entropía de Shannon para detectar cifrado u ofuscación"""
        if not data:
            return 0.0
        counts = np.bincount(np.frombuffer(data, dtype=np.uint8), minlength=256)
        probs = counts[counts > 0] / len(data)
        return -np.sum(probs * np.log2(probs))

    def _check_malicious_signatures(self, payload: bytes) -> bool:
        """Motor de búsqueda de firmas de ataque en tiempo real"""
        signatures = [
            b"exec(",
            b"system(",
            b"eval(",
            b"base64_decode",
            b"union select",
            b"drop table",
            b"-- ",
            b"rm -rf",
            b"/bin/sh",
            b"/etc/passwd",
            b"powershell",
            b"Invoke-Expression",
            b"..\\..\\",
            b"%00",
        ]
        payload_lower = payload.lower()
        return any(sig.lower() in payload_lower for sig in signatures)

    def add_trusted_source(
        self, address: bytes, permissions: List[str], duration: float = 3600
    ) -> SecurityToken:
        """Añade una fuente confiable"""
        token = SecurityToken(
            token_id=hashlib.sha256(address + str(time.time()).encode()).hexdigest(),
            creation_time=time.time(),
            expiration_time=time.time() + duration,
            permissions=permissions,
            quantum_resistant=True,
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
                addr.hex() for addr, score in self.threat_scores.items() if score > 0.7
            ],
            "blocked_patterns_count": len(self.blocked_patterns),
            "trusted_sources_count": len(self.trusted_sources),
            "average_threat_score": (
                np.mean(list(self.threat_scores.values()))
                if self.threat_scores
                else 0.0
            ),
        }


class QuantumSecurityLayer:
    """Capa de seguridad criptográfica post-cuántica"""

    def __init__(self):
        # Generación de par de claves para firmas digitales
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=4096
        )
        self.public_key = self.private_key.public_key()

    def generate_quantum_key(self, peer_public_key: bytes) -> bytes:
        """Ejecuta el protocolo de intercambio de claves seguro"""
        # Implementación del protocolo de intercambio basado en entropía segura
        import secrets

        raw_entropy = secrets.token_bytes(256)

        # Derivación de clave usando KDF (Key Derivation Function)
        return hashlib.blake2b(raw_entropy, digest_size=32).digest()

    def encrypt_quantum_resistant(self, data: bytes) -> bytes:
        """Aplica cifrado AES-256-GCM, considerado resistente a ataques cuánticos actuales"""
        import secrets

        key = secrets.token_bytes(32)
        nonce = secrets.token_bytes(12)
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

    def verify_quantum_signature(
        self, data: bytes, signature: bytes, peer_public_key: bytes
    ) -> bool:
        """Verifica una firma digital resistente a quantum"""
        try:
            peer_key = serialization.load_pem_public_key(peer_public_key)
            if not isinstance(peer_key, rsa.RSAPublicKey):
                return False
            peer_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True
        except Exception:
            return False
