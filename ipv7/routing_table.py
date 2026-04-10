from __future__ import annotations

from collections import OrderedDict
from typing import Dict, Iterator, Optional

from .ipv7_core import RoutingEntry
from .ipv7_header import IPv7Header


class RoutingTable:
    """Tabla de rutas con cache LRU para lookups eficientes.

    Internamente almacena prefijos mapeados a entradas de ruta y mantiene
    un cache LRU de hasta 256 entradas para acelerar lookups repetidos.
    """

    _CACHE_MAX = 256

    def __init__(self) -> None:
        self._table: Dict[bytes, RoutingEntry] = {}
        self._cache: OrderedDict[bytes, Optional[RoutingEntry]] = OrderedDict()

    # ------------------------------------------------------------------
    # Mutating methods
    # ------------------------------------------------------------------

    def add(self, prefix: bytes, entry: RoutingEntry) -> None:
        """Añade o reemplaza una entrada de ruta y limpia el cache.

        Args:
            prefix: Dirección/prefijo destino (32 bytes).
            entry:  Entrada de ruta asociada al prefijo.
        """
        self._table[prefix] = entry
        self._cache.clear()

    def remove(self, prefix: bytes) -> None:
        """Elimina una entrada de ruta y limpia el cache.

        Args:
            prefix: Dirección/prefijo a eliminar.
        """
        self._table.pop(prefix, None)
        self._cache.clear()

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def lookup(self, destination: bytes) -> Optional[RoutingEntry]:
        """Busca la mejor ruta para *destination*.

        Primero intenta una coincidencia exacta, luego aplica longest-prefix
        match.  El resultado se almacena en el cache LRU.

        Args:
            destination: Dirección destino (32 bytes).

        Returns:
            La ``RoutingEntry`` más específica encontrada, o ``None``.
        """
        if destination in self._cache:
            # Mover al final para marcar como recientemente usado
            self._cache.move_to_end(destination)
            return self._cache[destination]

        # Coincidencia exacta
        if destination in self._table:
            result = self._table[destination]
            self._store_in_cache(destination, result)
            return result

        # Longest-prefix match
        best_match: Optional[RoutingEntry] = None
        best_length: int = 0
        for prefix, entry in self._table.items():
            match_length = self._prefix_match_length(destination, prefix)
            if match_length > best_length:
                best_length = match_length
                best_match = entry

        self._store_in_cache(destination, best_match)
        return best_match

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _store_in_cache(self, key: bytes, value: Optional[RoutingEntry]) -> None:
        """Almacena una entrada en el cache, expulsando la más antigua si
        supera el límite de 256 entradas.

        Args:
            key:   Dirección destino usada como clave de cache.
            value: Resultado del lookup (puede ser ``None``).
        """
        self._cache[key] = value
        if len(self._cache) > self._CACHE_MAX:
            self._cache.popitem(last=False)

    @staticmethod
    def _prefix_match_length(addr1: bytes, addr2: bytes) -> int:
        """Calcula la longitud del prefijo común entre dos direcciones usando XOR.

        Para cada byte, si XOR == 0 los 8 bits son iguales; de lo contrario
        se cuentan los bits más significativos en común con
        ``8 - xor.bit_length()``.

        Args:
            addr1: Primera dirección (bytes).
            addr2: Segunda dirección (bytes).

        Returns:
            Número de bits de prefijo coincidentes.
        """
        length = 0
        for b1, b2 in zip(addr1, addr2):
            xor = b1 ^ b2
            if xor == 0:
                length += 8
            else:
                length += 8 - xor.bit_length()
                break
        return length

    # ------------------------------------------------------------------
    # Properties and dunder methods
    # ------------------------------------------------------------------

    @property
    def entries(self) -> Dict[bytes, RoutingEntry]:
        """Retorna el diccionario interno de rutas (solo lectura conceptual)."""
        return self._table

    def __len__(self) -> int:
        return len(self._table)

    def __contains__(self, item: object) -> bool:
        return item in self._table

    def __iter__(self) -> Iterator[bytes]:
        return iter(self._table)
