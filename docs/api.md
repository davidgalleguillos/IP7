# IPv7 Protocol API Reference

Este documento describe las principales clases y métodos disponibles en la implementación de referencia de IPv7.

## IPv7 Core (`ipv7.ipv7_core`)

### `IPv7Router`
El motor principal de enrutamiento.

- **`__init__(initial_state=None)`**: Inicializa el router. Puede cargar un estado previo (tabla de rutas, llaves).
- **`async send(header, payload)`**: Envía un paquete. Maneja fragmentación y selección de interfaz.
- **`add_route(prefix, entry)`**: Añade una ruta estática.
- **`remove_route(prefix)`**: Elimina una ruta.

### `RoutingEntry`
Estructura de datos para una entrada en la tabla de rutas.
- `next_hop`: Dirección de 256 bits del siguiente salto.
- `metric`: Costo de la ruta.
- `interface`: Nombre de la interfaz física/virtual.
- `qos_capabilities`: Lista de niveles de QoS soportados.

---

## AI Routing (`ipv7.ai_routing`)

### `AIRouter`
Gestor de enrutamiento predictivo basado en redes neuronales (LSTM + Attention).

- **`analyze_network_state(state)`**: Devuelve un análisis de salud y recomendaciones.
- **`get_route_recommendation(states)`**: Selecciona la mejor opción entre múltiples estados de red.
- **`train(batch_size, epochs)`**: Entrena el modelo con datos históricos de rendimiento.

---

## Quantum Layer (`ipv7.quantum_layer`)

### `QuantumInterface`
Interfaz para la gestión de canales de comunicación cuántica.

- **`async establish_channel(peer)`**: Negocia un canal cuántico.
- **`async create_entanglement(node_a, node_b)`**: Establece entrelazamiento EPR entre dos nodos.

---

## Persistence (`ipv7.persistence`)

### `StateManager`
Maneja la serialización del estado global del sistema en formato JSON.

- **`load_state()`**: Carga rutas y estadísticas desde `.ipv7_state.json`.
- **`save_state(state)`**: Guarda el estado actual.
- **`update_stats(field, increment)`**: Actualiza contadores globales (paquetes enviados, bloqueados).
