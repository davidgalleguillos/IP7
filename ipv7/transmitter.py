from __future__ import annotations

from typing import Dict, Iterator, Tuple

from .ipv7_header import IPv7Header


class ClassicalTransmitter:
    """Transmisor clásico (no cuántico) de paquetes IPv7."""

    async def transmit(
        self,
        header: IPv7Header,
        payload: bytes,
        next_hop: object,
    ) -> bool:
        """Transmite un único paquete por un enlace clásico.

        Decrementa el ``hop_limit`` del header, serializa el paquete y
        simula el envío.

        Args:
            header:   Cabecera IPv7 del paquete.
            payload:  Datos del paquete.
            next_hop: Entrada de la tabla de rutas con la información del
                      siguiente salto.

        Returns:
            ``True`` si la transmisión fue exitosa, ``False`` si el
            ``hop_limit`` llega a cero o hay un error.
        """
        try:
            if header.hop_limit <= 0:
                return False
            header.hop_limit -= 1
            _packet = header.pack() + payload  # noqa: F841 — placeholder real
            return True
        except Exception:
            return False

    async def transmit_fragments(
        self,
        fragments_iter: Iterator[Tuple[IPv7Header, bytes]],
        next_hop: object,
    ) -> bool:
        """Transmite todos los fragmentos producidos por un generador.

        Itera el generador de fragmentos y transmite cada uno.  Se detiene
        y retorna ``False`` en cuanto algún fragmento falla.

        Args:
            fragments_iter: Iterador/generador de tuplas ``(header, payload)``.
            next_hop:       Entrada de la tabla de rutas del siguiente salto.

        Returns:
            ``True`` si todos los fragmentos se transmitieron correctamente,
            ``False`` si al menos uno falló.
        """
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
        next_hop: object,
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
            _key = self._quantum_keys[peer]  # noqa: F841 — placeholder real
            # Aquí iría la lógica cuántica real (QKD, entanglement, etc.)
            return True
        except Exception:
            return await self._classical_fallback.transmit(header, payload, next_hop)

    def has_quantum_link(self, next_hop: object) -> bool:
        """Verifica si hay un enlace cuántico disponible para *next_hop*.

        Args:
            next_hop: Entrada de la tabla de rutas a verificar.

        Returns:
            ``True`` si la interfaz empieza con ``'quantum'`` y existe una
            clave cuántica registrada para el peer.
        """
        try:
            interface: str = next_hop.interface  # type: ignore[union-attr]
            peer: bytes = next_hop.next_hop  # type: ignore[union-attr]
            return interface.startswith("quantum") and peer in self._quantum_keys
        except AttributeError:
            return False