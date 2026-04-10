import argparse
import asyncio
import sys
import os
from typing import List
from ipv7 import (
    IPv7Header,
    IPv7Router,
    QoSLevel,
    AIRouter,
    NetworkState,
    QuantumInterface,
    SmartFirewall,
)
from ipv7.ipv7_core import RoutingEntry
from ipv7.persistence import StateManager

# Inicialización del gestor de estado
state_mgr = StateManager()


async def cmd_send(args):
    """Simula el envío de un paquete IPv7 usando la tabla de rutas persistente"""
    print("\n[SEND] Preparando paquete...")
    state = state_mgr.load_state()
    router = IPv7Router(initial_state=state)

    try:
        header = IPv7Header.from_string_addresses(
            source=args.source,
            destination=args.dest,
            traffic_priority=args.priority,
            qos_level=QoSLevel[args.qos],
            encryption_enabled=args.encrypt,
        )

        payload = args.payload.encode()
        success = await router.send(header, payload)

        if success:
            state_mgr.update_stats("packets_sent")
            print(f"  Desde: {args.source}")
            print(f"  Hacia: {args.dest}")
            print(f"  QoS: {args.qos} | Cifrado: {args.encrypt}")
            print("\n  [✓] Paquete enviado y enrutado correctamente.")
        else:
            print(
                f"\n  [x] Fallo en el enrutamiento: No hay ruta hacia {args.dest} o el TTL expiró."
            )
    except Exception as e:
        print(f"  [ERROR] {str(e)}")


async def cmd_route(args):
    """Gestión de la tabla de enrutamiento y análisis IA"""
    state = state_mgr.load_state()

    if args.route_action == "list":
        print("\n[ROUTE] Tabla de Enrutamiento Actual:")
        if not state["routing_table"]:
            print("  (Vacía)")
        for prefix, entry in state["routing_table"].items():
            print(
                f"  Prefix: {prefix.hex()[:16]}... -> Next Hop: {entry.next_hop.hex()[:16]}... [{entry.interface}] Metric: {entry.metric}"
            )

    elif args.route_action == "add":
        # Usar la lógica central de parsing de direcciones
        dest_bytes = IPv7Header._address_to_bytes(args.dest)
        next_hop_bytes = IPv7Header._address_to_bytes(args.next_hop)

        entry = RoutingEntry(
            next_hop=next_hop_bytes,
            metric=args.metric,
            interface=args.interface,
            qos_capabilities=list(QoSLevel),
        )
        state["routing_table"][dest_bytes] = entry
        state_mgr.save_state(state)
        print(f"\n  [✓] Ruta añadida hacia {args.dest} vía {args.interface}")

    elif args.route_action == "del":
        dest_bytes = IPv7Header._address_to_bytes(args.dest)
        if dest_bytes in state["routing_table"]:
            del state["routing_table"][dest_bytes]
            state_mgr.save_state(state)
            print(f"\n  [✓] Ruta hacia {args.dest} eliminada.")
        else:
            print(f"\n  [!] No se encontró la ruta hacia {args.dest}")

    elif args.route_action == "analyze":
        print("\n[ROUTE] Analizando recomendaciones de IA...")
        ns = NetworkState(
            args.latency,
            args.bandwidth,
            args.congestion,
            args.error_rate,
            args.quantum,
            QoSLevel.BEST_EFFORT,
        )
        ai = AIRouter()
        analysis = ai.analyze_network_state(ns)
        print(f"  Salud de red: {analysis['health']}")
        print(f"  Cuello de botella: {analysis['bottleneck'] or 'Ninguno'}")
        for rec in analysis["recommendations"]:
            print(f"  - {rec}")


async def cmd_quantum(args):
    """Gestiona canales cuánticos"""
    qi = QuantumInterface()
    peer_bytes = args.peer.encode().ljust(32, b"\x00")[:32]

    if args.action == "establish":
        success = await qi.establish_channel(peer_bytes)
        if success:
            state_mgr.update_stats("quantum_channels")
            print(f"  [✓] Canal cuántico establecido con {args.peer}")
        else:
            print(f"  [x] Fallo al establecer canal con {args.peer}.")
    elif args.action == "list":
        print("\n[QUANTUM] Canales activos (Simulados)")
        # En una implementación real, esto vendría del Manager
        print("  - qlink-01: ACTIVE")


async def cmd_status(args):
    """Muestra el estado global del sistema"""
    state = state_mgr.load_state()
    stats = state["stats"]
    print("\n" + "=" * 40)
    print("      IPv7 SYSTEM STATUS MONITOR")
    print("=" * 40)
    print(f"  Paquetes Enviados:  {stats['packets_sent']}")
    print(f"  Paquetes Bloqueados: {stats['packets_blocked']}")
    print(f"  Canales Cuánticos:  {stats['quantum_channels']}")
    print(f"  Rutas Activas:      {len(state['routing_table'])}")
    print("-" * 40)
    print("  Seguridad:          ACTIVE (Adaptive ML)")
    print("  Routing Engine:     AI-OPTIMIZED")
    print("=" * 40)


async def cmd_smoke_test(args):
    """Prueba completa usando el StateManager"""
    print("\nIniciando Smoke Test con Persistencia...")
    # 1. Limpiar/Resetear para el test? (Opcional)
    # 2. Añadir Ruta
    dest = "q256:smoke-target"
    dest_bytes = IPv7Header._address_to_bytes(dest)
    state = state_mgr.load_state()
    state["routing_table"][dest_bytes] = RoutingEntry(
        next_hop=IPv7Header._address_to_bytes("q256:next-hop"),
        metric=1,
        interface="eth0",
        qos_capabilities=list(QoSLevel),
    )
    state_mgr.save_state(state)

    # 3. Enviar Paquete
    router = IPv7Router(initial_state=state)
    header = IPv7Header.from_string_addresses("q256:source", dest)
    success = await router.send(header, b"Smoke Test Payload")

    if success:
        state_mgr.update_stats("packets_sent")
        print("  [✓] Test de persistencia y envío: EXITOSO")
    else:
        print("  [x] Test de envío: FALLIDO")


def main():
    parser = argparse.ArgumentParser(description="IPv7 Protocol CLI Tool & Simulator")
    subparsers = parser.add_subparsers(dest="command", help="Comandos")

    # Send
    send_p = subparsers.add_parser("send", help="Enviar paquete")
    send_p.add_argument("--source", default="q256:local_node")
    send_p.add_argument("--dest", required=True)
    send_p.add_argument("--payload", default="Ping IPv7")
    send_p.add_argument("--priority", type=int, default=1)
    send_p.add_argument(
        "--qos", choices=[e.name for e in QoSLevel], default="BEST_EFFORT"
    )
    send_p.add_argument("--encrypt", action="store_true")

    # Route
    route_p = subparsers.add_parser("route", help="Gestión de rutas e IA")
    route_subs = route_p.add_subparsers(dest="route_action")

    route_subs.add_parser("list", help="Listar rutas")

    add_p = route_subs.add_parser("add", help="Añadir ruta")
    add_p.add_argument("dest")
    add_p.add_argument("next_hop")
    add_p.add_argument("--interface", default="eth0")
    add_p.add_argument("--metric", type=int, default=1)

    del_p = route_subs.add_parser("del", help="Eliminar ruta")
    del_p.add_argument("dest")

    analyze_p = route_subs.add_parser("analyze", help="Análisis IA")
    analyze_p.add_argument("--latency", type=float, default=50.0)
    analyze_p.add_argument("--bandwidth", type=float, default=1000.0)
    analyze_p.add_argument("--congestion", type=float, default=0.2)
    analyze_p.add_argument("--error-rate", type=float, default=0.001)
    analyze_p.add_argument("--quantum", action="store_true")

    # Quantum
    quant_p = subparsers.add_parser("quantum", help="Operaciones cuánticas")
    quant_subs = quant_p.add_subparsers(dest="action")
    est_p = quant_subs.add_parser("establish")
    est_p.add_argument("--peer", required=True)
    quant_subs.add_parser("list")

    # Status
    subparsers.add_parser("status", help="Estado del sistema")

    # Smoke test
    subparsers.add_parser("smoke-test", help="Prueba integral")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    cmds = {
        "send": cmd_send,
        "route": cmd_route,
        "quantum": cmd_quantum,
        "status": cmd_status,
        "smoke-test": cmd_smoke_test,
    }

    asyncio.run(cmds[args.command](args))


if __name__ == "__main__":
    main()
