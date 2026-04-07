from dataclasses import dataclass
import logging
from .exceptions import RoutingError, QuantumLinkError
from typing import Any, List, Tuple, Dict, Optional

from .ipv7_header import IPv7Header, QoSLevel
import hashlib
from cryptography.fernet import Fernet

@dataclass
class RoutingEntry:
    next_hop: bytes  # 256-bit address
    metric: int
    interface: str
    qos_capabilities: List[QoSLevel]

class IPv7Router:
    """Router implementation for IPv7.

    Handles routing table management, packet fragmentation, QoS negotiation,
    optional quantum transmission and classical transmission. All public
    methods are type‑annotated and include logging for easier debugging.
    """
    # Custom exceptions are defined in ipv7.exceptions
    
    MTU = 9000  # Jumbo frames por defecto
    
    def __init__(self, initial_state: Optional[Dict[str, Any]] = None):
        self.routing_table: Dict[bytes, RoutingEntry] = {}
        self.quantum_keys: Dict[bytes, bytes] = {}
        self.encryption_key = Fernet.generate_key()
        self.fernet = Fernet(self.encryption_key)
        
        if initial_state:
            self.routing_table = initial_state.get("routing_table", {})
            self.quantum_keys = initial_state.get("quantum_keys", {})
        
    async def send(self, header: IPv7Header, payload: bytes) -> bool:
        """Envía un paquete IPv7"""
        if header.encryption_enabled:
            payload = self.fernet.encrypt(payload)
            header.payload_length = len(payload)

        packets = self._fragment_if_needed(header, payload)
        success = True
        
        for packet_header, packet_payload in packets:
            if not await self._route_packet(packet_header, packet_payload):
                success = False
                break
                
        return success
    
    def _fragment_if_needed(self, header: IPv7Header, payload: bytes) -> List[Tuple[IPv7Header, bytes]]:
        """Fragmenta el paquete si excede el MTU"""
        if len(payload) <= self.MTU:
            return [(header, payload)]
            
        fragments = []
        offset = 0
        while offset < len(payload):
            fragment = payload[offset:offset + self.MTU]
            fragment_header = IPv7Header(
                source=header.source,
                destination=header.destination,
                traffic_priority=header.traffic_priority,
                payload_length=len(fragment),
                next_header=header.next_header,
                hop_limit=header.hop_limit,
                qos_level=header.qos_level,
                geo_location=header.geo_location,
                encryption_enabled=header.encryption_enabled,
                encryption_algorithm=header.encryption_algorithm
            )
            fragments.append((fragment_header, fragment))
            offset += self.MTU
            
        return fragments
    
    async def _route_packet(self, header: IPv7Header, payload: bytes) -> bool:
        """Enruta un único paquete"""
        if header.hop_limit <= 0:
            logging.error("Routing error: hop limit exhausted for packet to %s", header.destination.hex())
            raise RoutingError(f"Hop limit exhausted for destination {header.destination.hex()}")
            
        next_hop = self._get_next_hop(header.destination)
        if not next_hop:
            logging.error("Routing error: no next hop found for destination %s", header.destination.hex())
            raise RoutingError(f"No route to destination {header.destination.hex()}")
            
        # Verificar soporte QoS
        if header.qos_level not in next_hop.qos_capabilities:
            # Degradar QoS si es necesario
            fallback_qos = self._get_best_available_qos(next_hop.qos_capabilities)
            header.qos_level = fallback_qos
            
        # Quantum routing si está disponible
        if header.qos_level == QoSLevel.QUANTUM and self._has_quantum_link(next_hop):
            return await self._quantum_transmit(header, payload, next_hop)
            
        # Transmisión clásica
        return await self._classical_transmit(header, payload, next_hop)
    
    def _get_next_hop(self, destination: bytes) -> Optional[RoutingEntry]:
        """Determina el siguiente salto basado en la tabla de rutas"""
        if destination in self.routing_table:
            return self.routing_table[destination]
            
        # Búsqueda del prefijo más largo
        best_match = None
        best_length = 0
        
        for prefix, entry in self.routing_table.items():
            match_length = self._prefix_match_length(destination, prefix)
            if match_length > best_length:
                best_length = match_length
                best_match = entry
                
        return best_match
    
    @staticmethod
    def _prefix_match_length(addr1: bytes, addr2: bytes) -> int:
        """Calcula la longitud del prefijo común entre dos direcciones"""
        length = 0
        for b1, b2 in zip(addr1, addr2):
            if b1 != b2:
                break
            length += 8
        return length
    
    def _get_best_available_qos(self, capabilities: List[QoSLevel]) -> QoSLevel:
        """Selecciona el mejor QoS disponible de las capacidades dadas"""
        for level in reversed(list(QoSLevel)):
            if level in capabilities:
                return level
        return QoSLevel.BEST_EFFORT
    
    def _has_quantum_link(self, next_hop: RoutingEntry) -> bool:
        """Verifica si hay un enlace cuántico disponible"""
        return (next_hop.interface.startswith('quantum') and 
                next_hop.next_hop in self.quantum_keys)
    
    async def _quantum_transmit(self, header: IPv7Header, payload: bytes, next_hop: RoutingEntry) -> bool:
        """Transmite usando enlace cuántico"""
        try:
            _key = self.quantum_keys[next_hop.next_hop]  # noqa: F841 — placeholder real
            # Aquí iría la lógica de transmisión cuántica real
            return True
        except Exception:
            # Fallback a transmisión clásica
            return await self._classical_transmit(header, payload, next_hop)
    
    async def _classical_transmit(self, header: IPv7Header, payload: bytes, _next_hop: RoutingEntry) -> bool:
        """Transmite usando red clásica.

        ``_next_hop`` es parte de la firma pública; se usará cuando se
        implemente el envío real por interfaz de red.
        """
        try:
            header.hop_limit -= 1
            _packet = header.pack() + payload  # noqa: F841 — placeholder real
            # Aquí iría el envío real por la interfaz de red
            return True
        except Exception:
            return False
    
    def add_route(self, prefix: bytes, entry: RoutingEntry):
        """Añade una entrada a la tabla de rutas"""
        self.routing_table[prefix] = entry
    
    def remove_route(self, prefix: bytes):
        """Elimina una ruta"""
        self.routing_table.pop(prefix, None)
        
    def set_quantum_key(self, peer: bytes, key: bytes):
        """Establece una clave cuántica compartida con un peer"""
        self.quantum_keys[peer] = key
        
    def clear_quantum_key(self, peer: bytes):
        """Elimina una clave cuántica"""
        self.quantum_keys.pop(peer, None)