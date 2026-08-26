"""
Real-Time Telemetry Stream Parser & Vendor Detection Service

Tokenizes and normalizes multi-vendor syslogs and telemetry events
(Cisco IOS/XR, Juniper Junos, VMware VeloCloud SD-WAN, and Arista EOS).
"""

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ParsedTelemetry(BaseModel):
    """Normalized telemetry event structure."""
    raw_log: str
    vendor: str = Field(..., description="Detected vendor: 'cisco', 'juniper', 'velocloud', 'arista', 'generic'")
    device_id: str = Field(default="Device-01", description="Extracted device identifier / hostname")
    event_code: Optional[str] = Field(default=None, description="Standardized vendor event code")
    protocol: Optional[str] = Field(default=None, description="Inferred protocol: 'bgp', 'ospf', 'ipsec', 'evpn', 'interface'")
    interface: Optional[str] = Field(default=None, description="Extracted interface name")
    peer_ip: Optional[str] = Field(default=None, description="Extracted neighbor or peer IP address")
    severity: str = Field(default="WARNING", description="Normalized severity: 'CRITICAL', 'ERROR', 'WARNING', 'INFO'")
    category: str = Field(default="routing", description="Event category: 'routing', 'switching', 'sdwan', 'hardware'")
    extracted_keywords: List[str] = Field(default_factory=list, description="Keywords for hybrid vector search")


class TelemetryParserService:
    """Service to automatically parse and normalize multi-vendor raw logs."""

    def parse_log(self, raw_log: str, device_hint: Optional[str] = None) -> ParsedTelemetry:
        """Parse raw log line or telemetry block and return normalized structure."""
        text = raw_log.strip()
        lower = text.lower()

        vendor = "generic"
        event_code = None
        protocol = "general"
        interface = None
        peer_ip = None
        severity = "WARNING"
        category = "routing"
        keywords = []

        # 1. Identify Vendor & Pattern Matches
        # ── Cisco IOS-XE / IOS-XR
        if "%" in text and any(k in text for k in ["%OSPF-", "%BGP-", "%LINK-", "%SYS-", "%LINEPROTO-", "%LDP-"]):
            vendor = "cisco"
            code_match = re.search(r'(%[A-Z0-9_]+-[0-9]+-[A-Z0-9_]+)', text)
            if code_match:
                event_code = code_match.group(1)

        # ── Juniper Junos OS
        elif any(k in text for k in ["rpd[", "RPD_", "SNMP_TRAP_", "KMD_VPN_", "CHASSISD_", "alarmd["]):
            vendor = "juniper"
            code_match = re.search(r'([A-Z0-9_]+_[A-Z0-9_]+)', text)
            if code_match:
                event_code = code_match.group(1)

        # ── VMware VeloCloud SD-WAN
        elif any(k in lower for k in ["velocloud", "velobrain", "edge_", "vcmp", "tunnel_dead", "qoe_drop", "pmtud"]):
            vendor = "velocloud"
            category = "sdwan"
            protocol = "ipsec"
            code_match = re.search(r'([A-Z_]{4,30})', text)
            if code_match and code_match.group(1) in ["EDGE_LINK_DEGRADATION", "TUNNEL_DEAD", "QOE_DROP", "PMTUD_BLACKHOLE"]:
                event_code = code_match.group(1)

        # ── Arista EOS
        elif any(k in text for k in ["%MLAG-", "%VXLAN-", "%EVPN-", "Arista"]):
            vendor = "arista"
            category = "switching"
            code_match = re.search(r'(%[A-Z0-9_]+-[0-9]+-[A-Z0-9_]+)', text)
            if code_match:
                event_code = code_match.group(1)

        # Fallback vendor matching based on typical interface naming
        if vendor == "generic":
            if re.search(r'\b(ge-|xe-|et-|so-)\d+/\d+/\d+', text):
                vendor = "juniper"
            elif re.search(r'\b(gigabitethernet|tengigabitethernet|fastethernet)\d+', lower):
                vendor = "cisco"
            elif re.search(r'\bethernet\d+/\d+', lower):
                vendor = "arista"

        # 2. Extract Protocol
        if "bgp" in lower or (event_code and "BGP" in event_code):
            protocol = "bgp"
            category = "routing"
            keywords.append("bgp")
        elif "ospf" in lower or (event_code and "OSPF" in event_code):
            protocol = "ospf"
            category = "routing"
            keywords.append("ospf")
        elif "mlag" in lower or (event_code and "MLAG" in event_code):
            protocol = "evpn"
            category = "switching"
            keywords.append("mlag")
        elif "vxlan" in lower or "evpn" in lower:
            protocol = "evpn"
            category = "switching"
            keywords.append("evpn")
        elif "crc" in lower or "fcs" in lower or "link" in lower:
            protocol = "interface" if vendor != "velocloud" else "ipsec"
            if vendor != "velocloud":
                category = "switching"
            keywords.append("interface" if vendor != "velocloud" else "sdwan")

        # 3. Extract Interface
        intf_match = re.search(
            r'\b((?:gigabitethernet|tengigabitethernet|fastethernet|ethernet|ge-|xe-|et-|port-channel|ge|xe|eth)\s*[\d\/\.\:\-]+)\b',
            text,
            re.IGNORECASE,
        )
        if intf_match:
            interface = intf_match.group(1).strip()
            keywords.append(interface)

        # 4. Extract Peer / Target IP Address
        ip_match = re.search(r'\b(?:nbr|neighbor|peer|to|from)\s+([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\b', text, re.IGNORECASE)
        if ip_match:
            peer_ip = ip_match.group(1)
            keywords.append(peer_ip)
        else:
            generic_ip = re.search(r'\b([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\b', text)
            if generic_ip:
                peer_ip = generic_ip.group(1)

        # 5. Extract Severity
        if any(s in lower for s in ["down", "dead", "reset", "expired", "split_brain", "critical", "fail", "fatal"]):
            severity = "CRITICAL"
        elif any(s in lower for s in ["error", "degraded", "retransmission", "mismatch", "loss"]):
            severity = "ERROR"
        elif any(s in lower for s in ["warning", "flap", "timeout"]):
            severity = "WARNING"
        else:
            severity = "INFO"

        # 6. Extract Device Hostname
        dev_name = device_hint or "Core-Router-01"
        host_match = re.search(r'([A-Za-z0-9\-_]+(?:-sw|-rt|-gw|-edge)[A-Za-z0-9\-_]*)', text, re.IGNORECASE)
        if host_match:
            dev_name = host_match.group(1)

        if event_code:
            keywords.append(event_code)

        return ParsedTelemetry(
            raw_log=text,
            vendor=vendor,
            device_id=dev_name,
            event_code=event_code,
            protocol=protocol,
            interface=interface,
            peer_ip=peer_ip,
            severity=severity,
            category=category,
            extracted_keywords=keywords,
        )


telemetry_parser = TelemetryParserService()
