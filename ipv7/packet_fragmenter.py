from __future__ import annotations

from typing import Iterator, List, Tuple

from .ipv7_header import IPv7Header


class PacketFragmenter:
    """Fragmenta y re-ensambla paquetes IPv7 respetando el MTU configurado."""

    MTU: int = 9000

    @staticmethod
    def fragment(header: IPv7Header, payload: bytes) -> Iterator[Tuple[IPv7Header, bytes]]:
        """Genera fragmentos del paquete si el payload supera el MTU.

        Si el payload cabe en un solo paquete, produce un único par
        ``(header, payload)``.  De lo contrario, produce tantos fragmentos
        como sean necesarios, cada uno con un header independiente.

        Args:
            header:  Cabecera IPv7 original.
            payload: Datos a fragmentar.

        Yields:
            Tuplas ``(fragment_header, fragment_payload)`` listas para
            transmitir.
        """
        mtu = PacketFragmenter.MTU
        if len(payload) <= mtu:
            yield (header, payload)
            return

        offset = 0
        while offset < len(payload):
            chunk = payload[offset:offset + mtu]
            fragment_header = IPv7Header(
                source=header.source,
                destination=header.destination,
                traffic_priority=header.traffic_priority,
                payload_length=len(chunk),
                next_header=header.next_header,
                hop_limit=header.hop_limit,
                qos_level=header.qos_level,
                geo_location=header.geo_location,
                encryption_enabled=header.encryption_enabled,
                encryption_algorithm=header.encryption_algorithm,
            )
            yield (fragment_header, chunk)
            offset += mtu

    @staticmethod
    def needs_fragmentation(payload_length: int, mtu: int = 9000) -> bool:
        """Determina si un payload requiere fragmentación.

        Args:
            payload_length: Longitud del payload en bytes.
            mtu:            MTU a respetar (por defecto 9000).

        Returns:
            ``True`` si el payload supera el MTU, ``False`` en caso contrario.
        """
        return payload_length > mtu

    @staticmethod
    def reassemble(fragments: List[Tuple[IPv7Header, bytes]]) -> Tuple[IPv7Header, bytes]:
        """Re-ensambla una lista de fragmentos en el paquete original.

        Concatena los payloads en orden y retorna el header del primer
        fragmento como cabecera representativa del paquete completo.

        Args:
            fragments: Lista de tuplas ``(header, payload)`` en orden.

        Returns:
            Tupla ``(first_header, reassembled_payload)``.

        Raises:
            ValueError: Si *fragments* está vacío.
        """
        if not fragments:
            raise ValueError("Cannot reassemble an empty fragment list.")

        first_header = fragments[0][0]
        reassembled_payload = b"".join(payload for _, payload in fragments)
        return (first_header, reassembled_payload)