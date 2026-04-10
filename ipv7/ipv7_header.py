from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Optional
import struct


class QoSLevel(Enum):
    BEST_EFFORT = 0
    GUARANTEED = 1
    REALTIME = 2
    QUANTUM = 3


@dataclass
class GeoLocation:
    latitude: float
    longitude: float
    altitude: Optional[float] = None

    def pack(self) -> bytes:
        return struct.pack("!ddd", self.latitude, self.longitude, self.altitude or 0.0)

    @classmethod
    def unpack(cls, data: bytes) -> "GeoLocation":
        lat, lon, alt = struct.unpack("!ddd", data)
        return cls(latitude=lat, longitude=lon, altitude=alt if alt != 0 else None)


@dataclass
class IPv7Header:
    """Cabecera del protocolo IPv7 con soporte para direccionamiento de 256 bits"""

    source: bytes  # 256 bits = 32 bytes
    destination: bytes  # 256 bits = 32 bytes
    traffic_priority: int = 0  # 32 bits
    payload_length: int = 0
    next_header: int = 0
    hop_limit: int = 64
    qos_level: QoSLevel = QoSLevel.BEST_EFFORT
    geo_location: Optional[GeoLocation] = None
    encryption_enabled: bool = False
    encryption_algorithm: Optional[str] = None
    version: int = 7
    fragment_id: int = 0  # 32 bits para identificar fragmentos del mismo paquete
    fragment_offset: int = 0  # 16 bits para el desplazamiento del fragmento
    more_fragments: bool = False  # Flag para indicar si hay más fragmentos

    @classmethod
    def from_string_addresses(cls, source: str, destination: str, **kwargs):
        """Crear header desde direcciones en formato string"""
        return cls(
            source=cls._address_to_bytes(source),
            destination=cls._address_to_bytes(destination),
            **kwargs,
        )

    @staticmethod
    def _address_to_bytes(address: str) -> bytes:
        """Convierte una dirección IPv7 string a bytes (256 bits)."""
        if not address.startswith("q256:"):
            raise ValueError("IPv7 addresses must start with q256:")
        hex_part = address[5:]  # after 'q256:'
        if len(hex_part) != 64:
            raise ValueError(
                f"IPv7 address must have exactly 64 hex characters after q256:, got {len(hex_part)}"
            )
        try:
            return bytes.fromhex(hex_part)
        except ValueError:
            raise ValueError(f"IPv7 address contains invalid hex characters: {address}")

    def pack(self) -> bytes:
        """Serializa la cabecera a bytes"""
        header = bytearray()
        header.extend(struct.pack("!B", self.version))
        header.extend(self.source)
        header.extend(self.destination)
        header.extend(struct.pack("!L", self.traffic_priority))
        header.extend(
            struct.pack("!IBI", self.payload_length, self.next_header, self.hop_limit)
        )
        header.extend(struct.pack("!B", self.qos_level.value))

        # Fragmentación
        header.extend(
            struct.pack(
                "!IHB",
                self.fragment_id,
                self.fragment_offset,
                1 if self.more_fragments else 0,
            )
        )

        # Geo location
        if self.geo_location:
            header.extend(b"\x01")  # Has geo
            header.extend(self.geo_location.pack())
        else:
            header.extend(b"\x00")  # No geo

        # Encryption
        header.extend(struct.pack("!?", self.encryption_enabled))
        if self.encryption_enabled:
            algo = (
                self.encryption_algorithm.encode() if self.encryption_algorithm else b""
            )
            header.extend(struct.pack("!H", len(algo)))
            header.extend(algo)

        return bytes(header)

    @classmethod
    def unpack(cls, data: bytes) -> "IPv7Header":
        """Deserializa bytes a una cabecera"""
        # Minimum size: 1(ver)+32(src)+32(dst)+4(prio)+9(len/nh/hl)+1(qos)+7(frag)+1(geo_flag)+1(enc_flag) = 88
        if len(data) < 88:
            raise ValueError(f"IPv7 header too short: {len(data)} bytes (minimum 88)")

        version = data[0]
        if version != 7:
            raise ValueError(f"Invalid IPv7 version: {version}")

        pos = 1
        source = data[pos : pos + 32]
        pos += 32
        destination = data[pos : pos + 32]
        pos += 32

        traffic_priority = struct.unpack("!L", data[pos : pos + 4])[0]
        pos += 4

        payload_length, next_header, hop_limit = struct.unpack(
            "!IBI", data[pos : pos + 9]
        )
        pos += 9

        qos_value = struct.unpack("!B", data[pos : pos + 1])[0]
        pos += 1
        qos_level = QoSLevel(qos_value)

        # Fragmentación
        fragment_id, fragment_offset, more_frag_val = struct.unpack(
            "!IHB", data[pos : pos + 7]
        )
        more_fragments = more_frag_val == 1
        pos += 7

        # Geo location
        has_geo = data[pos] == 1
        pos += 1
        geo_location = None
        if has_geo:
            geo_location = GeoLocation.unpack(data[pos : pos + 24])
            pos += 24

        # Encryption
        encryption_enabled = struct.unpack("!?", data[pos : pos + 1])[0]
        pos += 1
        encryption_algorithm = None
        if encryption_enabled:
            algo_len = struct.unpack("!H", data[pos : pos + 2])[0]
            pos += 2
            if algo_len > 0:
                encryption_algorithm = data[pos : pos + algo_len].decode()

        return cls(
            version=version,
            source=source,
            destination=destination,
            traffic_priority=traffic_priority,
            payload_length=payload_length,
            next_header=next_header,
            hop_limit=hop_limit,
            qos_level=qos_level,
            fragment_id=fragment_id,
            fragment_offset=fragment_offset,
            more_fragments=more_fragments,
            geo_location=geo_location,
            encryption_enabled=encryption_enabled,
            encryption_algorithm=encryption_algorithm,
        )
