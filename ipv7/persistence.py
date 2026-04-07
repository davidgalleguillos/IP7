import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import asdict, is_dataclass
from .ipv7_core import RoutingEntry
from .ipv7_header import QoSLevel

STATE_FILE = ".ipv7_state.json"

class StateManager:
    """Gestiona la persistencia del estado simulado del protocolo IPv7"""
    
    def __init__(self, file_path: str = STATE_FILE):
        self.file_path = file_path
        self._ensure_file_exists()
        
    def _ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            self.save_state({
                "routing_table": {},
                "quantum_keys": {},
                "stats": {
                    "packets_sent": 0,
                    "packets_blocked": 0,
                    "quantum_channels": 0
                }
            })
            
    def load_state(self) -> Dict[str, Any]:
        """Carga el estado desde el archivo JSON"""
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                
            # Reconstituir RoutingEntry objetos
            if "routing_table" in data:
                table = {}
                for prefix_hex, entry_data in data["routing_table"].items():
                    # Convertir prefijo de hex a bytes
                    prefix = bytes.fromhex(prefix_hex)
                    # Convertir QoS levels de strings a Enums
                    qos_caps = [QoSLevel[q] for q in entry_data["qos_capabilities"]]
                    
                    table[prefix] = RoutingEntry(
                        next_hop=bytes.fromhex(entry_data["next_hop"]),
                        metric=entry_data["metric"],
                        interface=entry_data["interface"],
                        qos_capabilities=qos_caps
                    )
                data["routing_table"] = table
                
            # Reconstituir Quantum Keys
            if "quantum_keys" in data:
                qkeys = {}
                for peer_hex, key_hex in data["quantum_keys"].items():
                    qkeys[bytes.fromhex(peer_hex)] = bytes.fromhex(key_hex)
                data["quantum_keys"] = qkeys
                
            return data
        except (json.JSONDecodeError, KeyError, ValueError):
            return {
                "routing_table": {},
                "quantum_keys": {},
                "stats": {
                    "packets_sent": 0,
                    "packets_blocked": 0,
                    "quantum_channels": 0
                }
            }
            
    def save_state(self, state: Dict[str, Any]):
        """Guarda el estado en el archivo JSON"""
        serializable = {}
        
        # Serializar RoutingTable
        if "routing_table" in state:
            table = {}
            for prefix, entry in state["routing_table"].items():
                table[prefix.hex()] = {
                    "next_hop": entry.next_hop.hex(),
                    "metric": entry.metric,
                    "interface": entry.interface,
                    "qos_capabilities": [q.name for q in entry.qos_capabilities]
                }
            serializable["routing_table"] = table
            
        # Serializar Quantum Keys
        if "quantum_keys" in state:
            qkeys = {}
            for peer, key in state["quantum_keys"].items():
                qkeys[peer.hex()] = key.hex()
            serializable["quantum_keys"] = qkeys
            
        # Stats son simples dicts
        serializable["stats"] = state.get("stats", {
            "packets_sent": 0, 
            "packets_blocked": 0, 
            "quantum_channels": 0
        })
        
        with open(self.file_path, 'w') as f:
            json.dump(serializable, f, indent=4)
            
    def update_stats(self, field: str, increment: int = 1):
        """Actualiza una estadística específica de forma atómica (carga-modifica-guarda)"""
        state = self.load_state()
        if field in state["stats"]:
            state["stats"][field] += increment
            self.save_state(state)
