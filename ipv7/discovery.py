import asyncio
import socket
import json
import logging
from typing import Dict, Any, Optional, Tuple, Callable
from .ipv7_header import QoSLevel


class DiscoveryService:
    """Servicio de auto-descubrimiento para nodos IPv7 en la red local."""

    DISCOVERY_PORT = 8768
    BROADCAST_INTERVAL = 5.0  # Segundos

    def __init__(
        self,
        ipv7_address: str,
        udp_tunnel_port: int,
        on_node_discovered: Optional[Callable[[str, str, int], Any]] = None,
    ):
        self.ipv7_address = ipv7_address
        self.udp_tunnel_port = udp_tunnel_port
        self.on_node_discovered = on_node_discovered
        self._running = False
        self._discovered_nodes: Dict[str, Dict[str, Any]] = {}

    async def start(self):
        """Inicia el servicio de descubrimiento (emision y escucha)"""
        if self._running:
            return
        self._running = True

        # Iniciar listener
        asyncio.create_task(self._listen())
        # Iniciar broadcaster
        asyncio.create_task(self._broadcast())

        logging.info(f"DiscoveryService iniciado para {self.ipv7_address}")

    async def _broadcast(self):
        """Envia anuncios por broadcast UDP periódicamente"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setblocking(False)

        payload = {
            "ipv7": self.ipv7_address,
            "port": self.udp_tunnel_port,
            "version": "0.1.0",
        }
        message = json.dumps(payload).encode()

        while self._running:
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None, sock.sendto, message, ("<broadcast>", self.DISCOVERY_PORT)
                )
            except Exception as e:
                logging.error(f"Error en broadcast de descubrimiento: {e}")
            await asyncio.sleep(self.BROADCAST_INTERVAL)

    async def _listen(self):
        """Escucha anuncios de otros nodos"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # En windows SO_REUSEADDR no es suficiente para permitir múltiples binds al mismo puerto UDP
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            pass  # No disponible en todas las plataformas

        sock.setblocking(False)
        sock.bind(("", self.DISCOVERY_PORT))

        loop = asyncio.get_running_loop()
        while self._running:
            try:
                data, addr = await loop.run_in_executor(None, sock.recvfrom, 1024)
                payload = json.loads(data.decode())

                node_v7 = payload.get("ipv7")
                node_port = payload.get("port")
                node_ip = addr[0]

                if node_v7 and node_v7 != self.ipv7_address:
                    if node_v7 not in self._discovered_nodes:
                        logging.info(
                            f"Nuevo nodo IPv7 descubierto: {node_v7} en {node_ip}:{node_port}"
                        )
                        self._discovered_nodes[node_v7] = {
                            "ip": node_ip,
                            "port": node_port,
                            "last_seen": asyncio.get_event_loop().time(),
                        }
                        if self.on_node_discovered:
                            await self.on_node_discovered(node_v7, node_ip, node_port)
                    else:
                        self._discovered_nodes[node_v7][
                            "last_seen"
                        ] = asyncio.get_event_loop().time()
            except (BlockingIOError, OSError) as e:
                # En Windows, recvfrom en socket no bloqueante lanza WinError 10035 si no hay datos
                if getattr(e, "winerror", None) == 10035 or isinstance(e, BlockingIOError):
                    await asyncio.sleep(1)
                    continue
                if self._running:
                    logging.error(f"Error en escucha de descubrimiento: {e}")
                await asyncio.sleep(1)
            except Exception as e:
                if self._running:
                    logging.error(f"Error inesperado en descubrimiento: {e}")
                await asyncio.sleep(1)

    def stop(self):
        self._running = False
