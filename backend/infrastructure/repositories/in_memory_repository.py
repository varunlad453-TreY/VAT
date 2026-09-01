"""
Infrastructure Adapter: In-Memory Knowledge & Vector Repository
Enterprise air-gapped fallback repository for offline operations.
"""

import hashlib
import logging
import math
from typing import Any, Dict, List, Optional

from backend.application.ports.vector_repository import IVectorRepository
from backend.domain.entities.citation import KnowledgeChunk
from config.settings import get_settings

logger = logging.getLogger(__name__)

# Multi-Vendor In-Memory Fallback Knowledge Base
ENTERPRISE_FALLBACK_CORPUS: List[Dict[str, Any]] = [
    # ── CISCO OSPF ────────────────────────────────────────────────────────────
    {
        "id": 1,
        "source_url": "https://www.cisco.com/c/en/us/support/docs/ip/open-shortest-path-first-ospf/13684-12.html",
        "title": "Troubleshoot OSPF Neighbors Stuck in Exstart/Exchange State",
        "vendor": "cisco",
        "product_family": "routing",
        "protocol": "ospf",
        "error_codes": ["%OSPF-5-ADJCHG", "EXSTART", "MTU_MISMATCH"],
        "chunk_text": (
            "OSPF neighbors stuck in EXSTART/EXCHANGE state. Syslog: %OSPF-5-ADJCHG: Process 1, Nbr 192.168.1.2 on "
            "GigabitEthernet0/0/1 from EXSTART to DOWN, Neighbor Down: Too many retransmissions. Cause: In Exstart state, "
            "routers negotiate master-slave and exchange DBD packets. MTU mismatch causes the router with the smaller MTU "
            "to reject or drop the neighbor's larger DBD packet. Fix: 'show interface <id> | include MTU', 'ip mtu 1500', "
            "or 'ip ospf mtu-ignore'."
        ),
    },
    {
        "id": 2,
        "source_url": "https://www.cisco.com/c/en/us/support/docs/ip/open-shortest-path-first-ospf/13699-29.html",
        "title": "Troubleshoot Common Problems with OSPF",
        "vendor": "cisco",
        "product_family": "routing",
        "protocol": "ospf",
        "error_codes": ["%OSPF-5-ADJCHG", "OSPF_HELLO_MISMATCH"],
        "chunk_text": (
            "OSPF Neighbor Formation Conditions: Both routers must agree on Area ID, Subnet Mask, Hello (10s) and Dead (40s) "
            "timers, and authentication keys. Duplicate router IDs prevent SPF calculation and cause routing loops. "
            "Diagnostics: 'show ip ospf interface', 'show ip ospf neighbor', 'clear ip ospf process'."
        ),
    },
    # ── CISCO BGP ────────────────────────────────────────────────────────────
    {
        "id": 3,
        "source_url": "https://www.cisco.com/c/en/us/support/docs/ip/border-gateway-protocol-bgp/13753-25.html",
        "title": "Troubleshoot Common BGP Issues and Neighbor Reset",
        "vendor": "cisco",
        "product_family": "routing",
        "protocol": "bgp",
        "error_codes": ["%BGP-5-ADJCHANGE", "HOLD_TIMER_EXPIRED", "NOTIFICATION_SENT"],
        "chunk_text": (
            "BGP neighbor session reset. Syslog: %BGP-5-ADJCHANGE: neighbor 10.10.10.1 Down - BGP Notification sent, "
            "hold time expired. Causes: 1. Keepalive packets dropped due to high CPU or Path MTU blackhole on transit path. "
            "2. MD5 authentication password mismatch (%BGP-3-NOTIFICATION 2/2). 3. AS number mismatch or TTL expiration. "
            "Resolution: 'show ip bgp summary', 'show ip bgp neighbors <ip>', 'neighbor <ip> timers 30 90', 'ping <ip> df-bit size 1400'."
        ),
    },
    # ── JUNIPER JUNOS BGP ────────────────────────────────────────────────────
    {
        "id": 4,
        "source_url": "https://www.juniper.net/documentation/us/en/software/junos/bgp/topics/topic-map/troubleshooting-bgp-sessions.html",
        "title": "Troubleshoot Junos OS BGP Peering and Neighbor State Flapping",
        "vendor": "juniper",
        "product_family": "routing",
        "protocol": "bgp",
        "error_codes": ["RPD_BGP_NEIGHBOR_STATE_CHANGED", "BGP_HOLD_TIME_EXPIRED"],
        "chunk_text": (
            "Junos OS BGP Peering Failure. Syslog: rpd[1234]: RPD_BGP_NEIGHBOR_STATE_CHANGED: BGP peer 172.16.1.1 (External AS 65001) "
            "changed state from Established to Idle (event HoldTimer). Causes: 1. Hold timer timeout due to transit packet drops or DDoS "
            "rate limiting on RE lo0. 2. Max prefix limit exceeded. Resolution: 'show bgp summary', 'show bgp neighbor 172.16.1.1', "
            "'set protocols bgp group EXTERNAL neighbor 172.16.1.1 hold-time 90', 'ping 172.16.1.1 size 1472 do-not-fragment'."
        ),
    },
    # ── VELOCLOUD SD-WAN ─────────────────────────────────────────────────────
    {
        "id": 5,
        "source_url": "https://docs.vmware.com/en/VMware-SD-WAN/troubleshooting-overlay-tunnels.html",
        "title": "Troubleshoot VeloCloud SD-WAN Overlay Tunnels and Packet Loss",
        "vendor": "velocloud",
        "product_family": "sdwan",
        "protocol": "ipsec",
        "error_codes": ["EDGE_LINK_DEGRADATION", "TUNNEL_DEAD", "QOE_DROP", "PMTUD_BLACKHOLE"],
        "chunk_text": (
            "VeloCloud SD-WAN Overlay Degradation. Alert: EDGE_LINK_DEGRADATION: WAN link GE3 packet loss 18.4% exceeding SLA. "
            "VeloBrain QoE score drops below 3.0. Causes: 1. Path MTU blackhole on ISP underlay dropping UDP 2426 (VCMP) packets. "
            "2. Shaper capacity misconfiguration. Fix: Configure Path MTU clamp to 1360 bytes on WAN interface profile, set CIR bandwidth "
            "shaper to 90% of provisioned link, set UDP 2426 keepalive to 15s."
        ),
    },
    # ── ARISTA EOS MLAG ──────────────────────────────────────────────────────
    {
        "id": 6,
        "source_url": "https://www.arista.com/en/support/toi/eos-4-24-0f/14545-evpn-vxlan-troubleshooting",
        "title": "Troubleshoot Arista EOS EVPN-VXLAN and MLAG Split-Brain",
        "vendor": "arista",
        "product_family": "switching",
        "protocol": "evpn",
        "error_codes": ["%MLAG-4-SPLIT_BRAIN", "%LINEPROTO-5-UPDOWN", "EVPN_TYPE2_DROP"],
        "chunk_text": (
            "Arista EOS MLAG Split-Brain Isolation. Syslog: %MLAG-4-SPLIT_BRAIN: MLAG peer link down; secondary nodes isolated. "
            "Hosts experience packet drops and MAC address flapping. Cause: Physical peer-link port-channel down while heartbeat is active. "
            "Resolution: Pre-check 'show mlag', configure 'reload-delay mlag 300' to prevent dual-active forwarding, restore peer-link "
            "interface with 'interface Ethernet1/1, 1/2' -> 'no shutdown', post-check 'show mlag'."
        ),
    },
]


from backend.infrastructure.adapters.remote_embedding_client import embedding_client


class InMemoryVectorRepository(IVectorRepository):
    """In-memory fallback implementation of IVectorRepository for air-gapped operations."""

    def __init__(self, corpus: Optional[List[Dict[str, Any]]] = None) -> None:
        self._corpus: List[Dict[str, Any]] = list(corpus if corpus is not None else ENTERPRISE_FALLBACK_CORPUS)

    def embed_text(self, text: str) -> List[float]:
        """Generate normalized 384-dimensional vector embedding via remote client or deterministic fallback."""
        return embedding_client.embed_text_sync(text)

    async def embed_text_async(self, text: str) -> List[float]:
        """Asynchronously generate normalized 384-dimensional vector embedding."""
        return await embedding_client.embed_text(text)

    async def find_relevant_docs(
        self,
        query_text: str,
        limit: int = 3,
        vendor: Optional[str] = None,
        protocol: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute in-memory keyword, token, and vendor-preference scoring.
        """
        v_filter = vendor.lower() if vendor and vendor.lower() not in ["generic", "multi_vendor", "all"] else None
        p_filter = protocol.lower() if protocol and protocol.lower() != "general" else None
        query_lower = query_text.lower()

        scored_corpus = []
        for item in self._corpus:
            score = 0.50
            if v_filter and item.get("vendor", "").lower() == v_filter:
                score += 0.20
            if p_filter and item.get("protocol", "").lower() == p_filter:
                score += 0.15

            # Error code matching
            for code in item.get("error_codes", []):
                if code.lower() in query_lower:
                    score += 0.35
                    break

            # Keyword heuristics
            if "exstart" in query_lower and "exstart" in item["chunk_text"].lower():
                score += 0.30
            if "hold time" in query_lower and "hold" in item["chunk_text"].lower():
                score += 0.35
            if "bgp" in query_lower and "bgp" in item["chunk_text"].lower():
                score += 0.25
            if "loss" in query_lower and "loss" in item["chunk_text"].lower():
                score += 0.25
            if "mlag" in query_lower and "mlag" in item["chunk_text"].lower():
                score += 0.35
            if "split-brain" in query_lower or "split_brain" in query_lower:
                if "split-brain" in item["chunk_text"].lower() or "split_brain" in item["chunk_text"].lower():
                    score += 0.35

            score = min(score, 0.98)
            scored_corpus.append({
                "id": item.get("id", 1),
                "source_url": item["source_url"],
                "title": item["title"],
                "vendor": item["vendor"],
                "protocol": item.get("protocol", "general"),
                "chunk_text": item["chunk_text"],
                "similarity": round(score, 3),
            })

        scored_corpus.sort(key=lambda x: x["similarity"], reverse=True)
        return scored_corpus[:limit]

    async def index_chunks(self, chunks: List[KnowledgeChunk]) -> int:
        """Add documentation chunks into in-memory store."""
        for chunk in chunks:
            self._corpus.append({
                "id": len(self._corpus) + 1,
                "source_url": chunk.source_url,
                "title": chunk.title,
                "vendor": chunk.vendor,
                "product_family": chunk.product_family,
                "protocol": chunk.protocol,
                "error_codes": chunk.error_codes,
                "chunk_text": chunk.chunk_text,
            })
        return len(chunks)

    async def is_healthy(self) -> bool:
        """In-memory store is always healthy."""
        return True
