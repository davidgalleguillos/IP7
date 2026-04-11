from dataclasses import dataclass
import logging
from .exceptions import RoutingError, QuantumLinkError
from typing import Any, List, Tuple, Dict, Optional

from .ipv7_header import IPv7Header, QoSLevel
from .transmitter import ClassicalTransmitter
from .discovery import DiscoveryService
import hashlib
import random
import asyncio
import socket
import logging
from cryptography.fernet import Fernet


@dataclass
class RoutingEntry:
    next_hop: bytes  # 256-bit address
    metric: int
    interface: str
    qos_capabilities: List[QoSLevel]
    tunnel_endpoint: Optional[Tuple[str, int]] = None  # (IPv4/v6, port) para túnel UDP


class IPv7Router:
    """Router real para IPv7 que utiliza túneles UDP y auto-descubrimiento."""

    MTU = 9000

    def __init__(
        self,
        initial_state: Optional[Dict[str, Any]] = None,
        bind_port: int = 8767,
        local_address: str = "q256:local_node",
    ):
        self.routing_table: Dict[bytes, RoutingEntry] = {}
        self.quantum_keys: Dict[bytes, bytes] = {}
        self.encryption_key = Fernet.generate_key()
        self.fernet = Fernet(self.encryption_key)
        self._fragment_counter = random.randint(0, 0xFFFFFFFF)
        self.bind_port = bind_port
        self.local_address = local_address
        self.transmitter = ClassicalTransmitter(bind_port=bind_port)
        self._running = False
        self.discovery_service = DiscoveryService(
            ipv7_address=local_address,
            udp_tunnel_port=bind_port,
            on_node_discovered=self._auto_configure_tunnel,
        )

        if initial_state:
            self.routing_table = initial_state.get("routing_table", {})
            self.quantum_keys = initial_state.get("quantum_keys", {})

    async def start(self):
        """Inicia el servicio de escucha de red y el auto-descubrimiento"""
        if self._running:
            return
        self._running = True
        loop = asyncio.get_running_loop()

        # Crear socket de escucha
        listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        listen_sock.setblocking(False)
        listen_sock.bind(("0.0.0.0", self.bind_port))  # nosec B104

        logging.info(
            f"IPv7 Router ({self.local_address}) escuchando en puerto UDP {self.bind_port}"
        )

        # Iniciar descubrimiento
        await self.discovery_service.start()

        while self._running:
            # Recibir datos usando executor para no bloquear el loop
            data, addr = await loop.run_in_executor(None, listen_sock.recvfrom, 65535)
            asyncio.create_task(self._handle_incoming_packet(data, addr))

    async def _auto_configure_tunnel(self, node_v7: str, node_ip: str, node_port: int):
        """Configura automáticamente un túnel hacia un nodo descubierto"""
        dest_bytes = IPv7Header._address_to_bytes(node_v7)
        if dest_bytes not in self.routing_table:
            entry = RoutingEntry(
                next_hop=dest_bytes,
                metric=1,
                interface="auto-discovered",
                qos_capabilities=list(QoSLevel),
                tunnel_endpoint=(node_ip, node_port),
            )
            self.add_route(dest_bytes, entry)
            logging.info(
                f"Ruta auto-configurada hacia {node_v7} via {node_ip}:{node_port}"
            )

    async def _handle_incoming_packet(self, data: bytes, addr: Tuple[str, int]):
        """Procesa un paquete IPv7 recibido por el túnel UDP"""
        try:
            header = IPv7Header.unpack(data)
            payload = data[len(header.pack()) :]

            logging.info(f"Paquete IPv7 recibido de {header.source.hex()} vía {addr}")

            # Aquí iría la lógica de entrega local o reenvío
            # Si el destino somos nosotros (implementar local_address), procesar
            # Si no, reenviar usando _route_packet

        except Exception as e:
            logging.error(f"Error al procesar paquete entrante: {e}")

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

    def _fragment_if_needed(
        self, header: IPv7Header, payload: bytes
    ) -> List[Tuple[IPv7Header, bytes]]:
        """Fragmenta el paquete si excede el MTU"""
        if len(payload) <= self.MTU:
            return [(header, payload)]

        fragments = []
        offset = 0
        self._fragment_counter = (self._fragment_counter + 1) & 0xFFFFFFFF

        while offset < len(payload):
            chunk_size = min(len(payload) - offset, self.MTU)
            fragment = payload[offset : offset + chunk_size]

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
                encryption_algorithm=header.encryption_algorithm,
                fragment_id=self._fragment_counter,
                fragment_offset=offset,
                more_fragments=(offset + chunk_size < len(payload)),
            )
            fragments.append((fragment_header, fragment))
            offset += chunk_size

        return fragments

    async def _route_packet(self, header: IPv7Header, payload: bytes) -> bool:
        """Enruta un único paquete utilizando el transmisor real"""
        if header.hop_limit <= 0:
            raise RoutingError(
                f"Hop limit exhausted for destination {header.destination.hex()}"
            )

        next_hop = self._get_next_hop(header.destination)
        if not next_hop:
            raise RoutingError(f"No route to destination {header.destination.hex()}")

        # Verificar soporte QoS
        if header.qos_level not in next_hop.qos_capabilities:
            fallback_qos = self._get_best_available_qos(next_hop.qos_capabilities)
            header.qos_level = fallback_qos

        # Transmisión real usando el transmisor configurado
        return await self.transmitter.transmit(header, payload, next_hop)

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
        return (
            next_hop.interface.startswith("quantum")
            and next_hop.next_hop in self.quantum_keys
        )

    async def _quantum_transmit(
        self, header: IPv7Header, payload: bytes, next_hop: RoutingEntry
    ) -> bool:
        """Transmite usando enlace cuántico"""
        try:
            _key = self.quantum_keys[next_hop.next_hop]  # noqa: F841 — placeholder real
            # Aquí iría la lógica de transmisión cuántica real
            return True
        except Exception:
            # Fallback a transmisión clásica
            return await self._classical_transmit(header, payload, next_hop)

    async def _classical_transmit(
        self, header: IPv7Header, payload: bytes, _next_hop: RoutingEntry
    ) -> bool:
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
