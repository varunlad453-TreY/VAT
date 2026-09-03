#!/usr/bin/env python3
"""
==============================================================================
VAT Enterprise Load Testing Harness: 100,000 EPS BGP Flap Storm Simulator
Simulates massive carrier-grade BGP flap events hitting Vector.dev edge receiver.
==============================================================================
"""

import asyncio
import argparse
import json
import logging
import random
import socket
import time
from typing import List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("bgp-storm-simulator")

# Realistic multi-vendor telemetry templates
MULTI_VENDOR_LOG_TEMPLATES = [
    # Cisco BGP Flap
    "%BGP-5-ADJCHANGE: neighbor 10.{octet2}.{octet3}.{octet4} Down - BGP Notification sent, hold time expired",
    # Juniper BGP Neighbor Change
    "rpd[{pid}]: RPD_BGP_NEIGHBOR_STATE_CHANGED: BGP peer 172.16.{octet3}.{octet4} (External AS {asn}) changed state from Established to Idle",
    # VeloCloud SD-WAN Packet Loss & Flap
    "EDGE_LINK_DEGRADATION: WAN link GE{iface} packet loss 22.4% PMTUD_BLACKHOLE peer 198.51.100.{octet4}",
    # Arista MLAG Split-Brain
    "%MLAG-4-SPLIT_BRAIN: MLAG peer link Port-Channel {pc} down on Leaf-{leaf}; peer 10.0.{octet3}.{octet4} unreachable",
]

def generate_telemetry_batch(batch_size: int) -> List[str]:
    """Generates a batch of randomized multi-vendor syslog strings."""
    batch = []
    for _ in range(batch_size):
        tpl = random.choice(MULTI_VENDOR_LOG_TEMPLATES)
        log = tpl.format(
            octet2=random.randint(1, 254),
            octet3=random.randint(1, 254),
            octet4=random.randint(1, 254),
            pid=random.randint(1000, 9999),
            asn=random.randint(64512, 65534),
            iface=random.randint(1, 4),
            pc=random.randint(10, 50),
            leaf=random.randint(1, 8),
        )
        batch.append(f"<189>1 {time.strftime('%Y-%m-%dT%H:%M:%SZ')} Edge-Router-{random.randint(1, 100)} VAT - - - {log}")
    return batch


async def udp_storm_worker(
    target_host: str,
    target_port: int,
    total_events: int,
    batch_size: int = 1000,
) -> int:
    """High-speed UDP socket worker blasting syslog datagrams."""
    loop = asyncio.get_running_loop()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)

    sent = 0
    while sent < total_events:
        batch = generate_telemetry_batch(min(batch_size, total_events - sent))
        for msg in batch:
            try:
                await loop.sock_sendall(sock, msg.encode("utf-8"))
                sent += 1
            except Exception:
                pass
        await asyncio.sleep(0.001) # Yield to event loop

    sock.close()
    return sent


async def run_bgp_storm(
    target_host: str = "127.0.0.1",
    target_port: int = 514,
    target_eps: int = 100000,
    duration_seconds: int = 10,
    concurrency: int = 10,
) -> None:
    """Orchestrates concurrent workers to achieve 100,000 EPS target load."""
    total_target_events = target_eps * duration_seconds
    events_per_worker = total_target_events // concurrency

    logger.info("=" * 70)
    logger.info("LAUNCHING 100,000 EPS BGP FLAP STORM LOAD TEST")
    logger.info("Target: %s:%d (Syslog UDP)", target_host, target_port)
    logger.info("Target Rate: %d EPS | Duration: %ds | Total Events: %d", target_eps, duration_seconds, total_target_events)
    logger.info("Worker Threads: %d (%d events/worker)", concurrency, events_per_worker)
    logger.info("=" * 70)

    t0 = time.perf_counter()
    tasks = [
        asyncio.create_task(
            udp_storm_worker(target_host, target_port, events_per_worker, batch_size=500)
        )
        for _ in range(concurrency)
    ]

    results = await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - t0
    total_sent = sum(results)
    actual_eps = total_sent / elapsed if elapsed > 0 else 0.0

    logger.info("=" * 70)
    logger.info("BGP FLAP STORM COMPLETED")
    logger.info("Total Events Dispatched: %d", total_sent)
    logger.info("Elapsed Time: %.2f seconds", elapsed)
    logger.info("Actual Throughput: %.2f EPS", actual_eps)
    logger.info("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="100k EPS BGP Flap Storm Generator")
    parser.add_argument("--host", default="127.0.0.1", help="Target host (Vector receiver)")
    parser.add_argument("--port", type=int, default=514, help="Target port")
    parser.add_argument("--eps", type=int, default=100000, help="Target EPS rate")
    parser.add_argument("--duration", type=int, default=5, help="Storm duration in seconds")
    parser.add_argument("--concurrency", type=int, default=8, help="Concurrent workers")

    args = parser.parse_args()
    asyncio.run(
        run_bgp_storm(
            target_host=args.host,
            target_port=args.port,
            target_eps=args.eps,
            duration_seconds=args.duration,
            concurrency=args.concurrency,
        )
    )
