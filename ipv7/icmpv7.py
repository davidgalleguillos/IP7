import struct
from enum import IntEnum
from dataclasses import dataclass
from typing import Optional


class ICMPv7Type(IntEnum):
    ECHO_REPLY = 0
    DESTINATION_UNREACHABLE = 1
    PACKET_TOO_BIG = 2
    TIME_EXCEEDED = 3
    PARAMETER_PROBLEM = 4
    ECHO_REQUEST = 128
    ROUTER_ADVERTISEMENT = 134
    ROUTER_SOLICITATION = 135


@dataclass
class ICMPv7Message:
    """Mensaje de control para el protocolo IPv7"""

    type: ICMPv7Type
    code: int = 0
    checksum: int = 0
    data: bytes = b""

    def pack(self) -> bytes:
        """Serializa el mensaje ICMPv7"""
        # Pack header: Type(B), Code(B), Checksum(H)
        header = struct.pack("!BBH", self.type, self.code, 0)

        # Calcular checksum simple (Internet Checksum)
        full_msg = header + self.data
        self.checksum = self._calculate_checksum(full_msg)

        # Re-pack con el checksum correcto
        header = struct.pack("!BBH", self.type, self.code, self.checksum)
        return header + self.data

    @classmethod
    def unpack(cls, data: bytes) -> "ICMPv7Message":
        """Deserializa bytes a un mensaje ICMPv7"""
        if len(data) < 4:
            raise ValueError("ICMPv7 message too short")

        msg_type, code, checksum = struct.unpack("!BBH", data[:4])
        payload = data[4:]

        return cls(
            type=ICMPv7Type(msg_type), code=code, checksum=checksum, data=payload
        )

    @staticmethod
    def _calculate_checksum(data: bytes) -> int:
        """Calcula el checksum de 16 bits para el mensaje"""
        if len(data) % 2:
            data += b"\x00"

        s = sum(struct.unpack(f"!{len(data)//2}H", data))
        s = (s >> 16) + (s & 0xFFFF)
        s += s >> 16
        return ~s & 0xFFFF
