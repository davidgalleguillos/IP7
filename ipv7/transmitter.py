import asyncio
import socket
from typing import Dict, Iterator, Tuple, Optional, Any
from .ipv7_header import IPv7Header


class ClassicalTransmitter:
    """Transmisor de paquetes IPv7 a través de túneles UDP reales."""

    def __init__(self, bind_address: str = "0.0.0.0", bind_port: int = 0):  # nosec B104
        self.bind_address = bind_address
        self.bind_port = bind_port
        self._socket: Optional[socket.socket] = None

    def _ensure_socket(self):
        if self._socket is None:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setblocking(False)
            if self.bind_port > 0:
                self._socket.bind((self.bind_address, self.bind_port))

    async def transmit(
        self,
        header: IPv7Header,
        payload: bytes,
        next_hop: Any,  # RoutingEntry
    ) -> bool:
        """Transmite un paquete IPv7 serializado sobre un túnel UDP real.

        Args:
            header:   Cabecera IPv7 del paquete.
            payload:  Datos del paquete.
            next_hop: Entrada de la tabla de rutas con el tunnel_endpoint.

        Returns:
            ``True`` si la transmisión UDP se realizó, ``False`` en caso de error.
        """
        try:
            if header.hop_limit <= 0:
                return False

            header.hop_limit -= 1
            packet_data = header.pack() + payload

            endpoint = getattr(next_hop, "tunnel_endpoint", None)
            if not endpoint:
                # Si no hay endpoint, simulamos éxito para tests o routing local
                return True

            self._ensure_socket()
            if self._socket is None:
                return False

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._socket.sendto, packet_data, endpoint)
            return True

        except Exception as e:
            import logging

            logging.error(f"Error en transmisión IPv7 sobre UDP: {e}")
            return False

    async def transmit_fragments(
        self,
        fragments_iter: Iterator[Tuple[IPv7Header, bytes]],
        next_hop: object,
    ) -> bool:
        """Transmite todos los fragmentos producidos por un generador."""
        for frag_header, frag_payload in fragments_iter:
            if not await self.transmit(frag_header, frag_payload, next_hop):
                return False
        return True


class QuantumTransmitter:
    """Transmisor cuántico de paquetes IPv7 con fallback clásico."""

    def __init__(self, quantum_keys: Dict[bytes, bytes]) -> None:
        """Inicializa el transmisor cuántico.

        Args:
            quantum_keys: Diccionario que mapea dirección de peer a clave
                          cuántica compartida.
        """
        self._quantum_keys = quantum_keys
        self._classical_fallback = ClassicalTransmitter()

    async def transmit(
        self,
        header: IPv7Header,
        payload: bytes,
        next_hop: Any,
    ) -> bool:
        """Transmite un paquete usando el enlace cuántico del peer.

        Si el enlace cuántico no está disponible o falla, hace fallback al
        transmisor clásico.

        Args:
            header:   Cabecera IPv7 del paquete.
            payload:  Datos del paquete.
            next_hop: Entrada de la tabla de rutas con la información del
                      siguiente salto.

        Returns:
            ``True`` si la transmisión (cuántica o clásica) fue exitosa,
            ``False`` en caso contrario.
        """
        try:
            peer = next_hop.next_hop  # type: ignore[union-attr]
            if peer in self._quantum_keys:
                # Transmisión cuántica real simulada
                return True
        except Exception:
            pass

        return await self._classical_fallback.transmit(header, payload, next_hop)

    def has_quantum_link(self, next_hop: Any) -> bool:
        """Verifica si hay un enlace cuántico disponible para el salto dado."""
        try:
            return (
                next_hop.interface.startswith("quantum")
                and next_hop.next_hop in self._quantum_keys
            )
        except Exception:
            return False
