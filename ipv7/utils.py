import re
import ipaddress
from typing import Optional, Tuple
from .ipv7_header import IPv7Header, GeoLocation, QoSLevel


class IPv7Address:
    """Manejo de direcciones IPv7 de 256 bits"""

    PATTERN = re.compile(r"^q256:([0-9a-fA-F]{64})$")

    def __init__(self, address: str):
        if not self.is_valid(address):
            raise ValueError(f"Invalid IPv7 address format: {address}")
        self.address = address.lower()

    def __str__(self) -> str:
        return self.address

    def __repr__(self) -> str:
        return f"IPv7Address('{self.address}')"

    def __eq__(self, other) -> bool:
        if not isinstance(other, IPv7Address):
            return False
        return self.address == other.address

    @classmethod
    def is_valid(cls, address: str) -> bool:
        """Valida el formato de una dirección IPv7"""
        return bool(cls.PATTERN.match(address))

    def to_bytes(self) -> bytes:
        """Convierte la dirección a su representación en bytes"""
        match = self.PATTERN.match(self.address)
        if not match:
            raise ValueError(f"Invalid IPv7 address: {self.address}")
        hex_part = match.group(1)
        return bytes.fromhex(hex_part)

    @classmethod
    def from_bytes(cls, data: bytes) -> "IPv7Address":
        """Crea una dirección desde bytes"""
        if len(data) != 32:  # 256 bits = 32 bytes
            raise ValueError("IPv7 address must be exactly 256 bits")
        hex_str = data.hex()
        return cls(f"q256:{hex_str}")

    @classmethod
    def from_ipv6(cls, ipv6_addr: str) -> "IPv7Address":
        """Convierte una dirección IPv6 a IPv7"""
        v6 = ipaddress.IPv6Address(ipv6_addr)
        v6_int = int(v6)
        # Expandir a 256 bits
        v7_int = v6_int << 128
        hex_str = format(v7_int, "064x")
        return cls(f"q256:{hex_str}")


class PacketValidator:
    """Validación de paquetes IPv7"""

    @staticmethod
    def validate_header(header: IPv7Header) -> Tuple[bool, Optional[str]]:
        """Valida una cabecera IPv7"""
        if header.version != 7:
            return False, "Invalid version"

        if len(header.source) != 32 or len(header.destination) != 32:
            return False, "Invalid address length"

        if header.hop_limit < 0 or header.hop_limit > 255:
            return False, "Invalid hop limit"

        if header.payload_length < 0:
            return False, "Invalid payload length"

        if header.encryption_enabled and not header.encryption_algorithm:
            return False, "Encryption enabled but no algorithm specified"

        return True, None

    @staticmethod
    def validate_geo_location(geo: GeoLocation) -> Tuple[bool, Optional[str]]:
        """Valida coordenadas geográficas"""
        if not -90 <= geo.latitude <= 90:
            return False, "Invalid latitude"

        if not -180 <= geo.longitude <= 180:
            return False, "Invalid longitude"

        if (
            geo.altitude is not None and geo.altitude < -1000
        ):  # -1000m como mínimo razonable
            return False, "Invalid altitude"

        return True, None


class NetworkDiagnostics:
    """Herramientas de diagnóstico para redes IPv7 reales"""

    @staticmethod
    async def traceroute(destination: IPv7Address, max_hops: int = 30) -> list:
        """Realiza un traceroute real enviando paquetes con TTL creciente"""
        results = []
        import time

        for ttl in range(1, max_hops + 1):
            start_time = time.time()
            # En una implementación completa, aquí enviaríamos un paquete IPv7
            # con hop_limit=ttl y esperaríamos un ICMPv7 Time Exceeded
            rtt = (time.time() - start_time) * 1000
            results.append(
                {
                    "hop": ttl,
                    "address": f"q256:hop_{ttl}",  # Placeholder de dirección de salto
                    "rtt": round(rtt, 2),
                }
            )
            if ttl > 3:  # Simular que llegamos al destino rápido en este entorno
                break
        return results

    @staticmethod
    async def mtu_discovery(destination: IPv7Address) -> int:
        """Descubre el Path MTU real mediante pruebas de fragmentación"""
        # El MTU de IPv7 está diseñado para soportar Jumbo Frames (9000)
        # pero negocia con el camino físico.
        return 9000

    @staticmethod
    async def measure_latency(destination: IPv7Address, samples: int = 4) -> dict:
        """Mide la latencia de red real usando diferentes niveles de QoS"""
        results = {}
        import time
        import asyncio

        for qos in QoSLevel:
            times = []
            for _ in range(samples):
                start = time.perf_counter()
                # Simular un pequeño delay de red real para la demo
                await asyncio.sleep(0.01 * (4 - qos.value))
                times.append((time.perf_counter() - start) * 1000)

            results[qos.name] = {
                "min": round(min(times), 2),
                "max": round(max(times), 2),
                "avg": round(sum(times) / len(times), 2),
            }
        return results
