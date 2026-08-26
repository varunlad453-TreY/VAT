"""
Infrastructure Adapter: Multi-Vendor Regex Telemetry Parser
Tokenizes and normalizes syslogs and telemetry events for Cisco, Juniper, VeloCloud, and Arista.
"""

import re
from typing import List, Optional

from backend.application.ports.telemetry_parser import ITelemetryParser
from backend.domain.entities.telemetry import ParsedTelemetry
from backend.domain.enums import ProtocolType, SeverityLevel, VendorPlatform


class RegexTelemetryParser(ITelemetryParser):
    """Multi-vendor regex telemetry parser implementing ITelemetryParser."""

    def parse_log(self, raw_log: str, device_hint: Optional[str] = None) -> ParsedTelemetry:
        """Parse raw log line or telemetry block and return normalized domain entity."""
        text = raw_log.strip()
        lower = text.lower()

        vendor = VendorPlatform.GENERIC.value
        event_code = None
        protocol = ProtocolType.GENERAL.value
        interface = None
        peer_ip = None
        severity = SeverityLevel.WARNING.value
        category = "routing"
        keywords = []

        # 1. Vendor & Event Code Identification
        # ── Cisco IOS-XE / IOS-XR
        if "%" in text and any(k in text for k in ["%OSPF-", "%BGP-", "%LINK-", "%SYS-", "%LINEPROTO-", "%LDP-"]):
            vendor = VendorPlatform.CISCO.value
            code_match = re.search(r'(%[A-Z0-9_]+-[0-9]+-[A-Z0-9_]+)', text)
            if code_match:
                event_code = code_match.group(1)

        # ── Juniper Junos OS
        elif any(k in text for k in ["rpd[", "RPD_", "SNMP_TRAP_", "KMD_VPN_", "CHASSISD_", "alarmd["]):
            vendor = VendorPlatform.JUNIPER.value
            code_match = re.search(r'([A-Z0-9_]+_[A-Z0-9_]+)', text)
            if code_match:
                event_code = code_match.group(1)

        # ── VMware VeloCloud SD-WAN
        elif any(k in lower for k in ["velocloud", "velobrain", "edge_", "vcmp", "tunnel_dead", "qoe_drop", "pmtud"]):
            vendor = VendorPlatform.VELOCLOUD.value
            category = "sdwan"
            protocol = ProtocolType.IPSEC.value
            code_match = re.search(r'([A-Z_]{4,30})', text)
            if code_match and code_match.group(1) in ["EDGE_LINK_DEGRADATION", "TUNNEL_DEAD", "QOE_DROP", "PMTUD_BLACKHOLE"]:
                event_code = code_match.group(1)

        # ── Arista EOS
        elif any(k in text for k in ["%MLAG-", "%VXLAN-", "%EVPN-", "Arista"]):
            vendor = VendorPlatform.ARISTA.value
            category = "switching"
            code_match = re.search(r'(%[A-Z0-9_]+-[0-9]+-[A-Z0-9_]+)', text)
            if code_match:
                event_code = code_match.group(1)

        # Fallback vendor matching based on typical interface naming
        if vendor == VendorPlatform.GENERIC.value:
            if re.search(r'\b(ge-|xe-|et-|so-)\d+/\d+/\d+', text):
                vendor = VendorPlatform.JUNIPER.value
            elif re.search(r'\b(gigabitethernet|tengigabitethernet|fastethernet)\d+', lower):
                vendor = VendorPlatform.CISCO.value
            elif re.search(r'\bethernet\d+/\d+', lower):
                vendor = VendorPlatform.ARISTA.value

        # 2. Protocol Identification
        if "bgp" in lower or (event_code and "BGP" in event_code):
            protocol = ProtocolType.BGP.value
            category = "routing"
            keywords.append("bgp")
        elif "ospf" in lower or (event_code and "OSPF" in event_code):
            protocol = ProtocolType.OSPF.value
            category = "routing"
            keywords.append("ospf")
        elif "mlag" in lower or (event_code and "MLAG" in event_code):
            protocol = ProtocolType.EVPN.value
            category = "switching"
            keywords.append("mlag")
        elif "vxlan" in lower or "evpn" in lower:
            protocol = ProtocolType.EVPN.value
            category = "switching"
            keywords.append("evpn")
        elif "crc" in lower or "fcs" in lower or "link" in lower:
            protocol = ProtocolType.INTERFACE.value if vendor != VendorPlatform.VELOCLOUD.value else ProtocolType.IPSEC.value
            if vendor != VendorPlatform.VELOCLOUD.value:
                category = "switching"
            keywords.append("interface" if vendor != VendorPlatform.VELOCLOUD.value else "sdwan")

        # 3. Interface Extraction
        intf_match = re.search(
            r'\b((?:gigabitethernet|tengigabitethernet|fastethernet|ethernet|ge-|xe-|et-|port-channel|ge|xe|eth)\s*[\d\/\.\:\-]+)\b',
            text,
            re.IGNORECASE,
        )
        if intf_match:
            interface = intf_match.group(1).strip()
            keywords.append(interface)

        # 4. Peer / Target IP Address Extraction
        ip_match = re.search(r'\b(?:nbr|neighbor|peer|to|from)\s+([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\b', text, re.IGNORECASE)
        if ip_match:
            peer_ip = ip_match.group(1)
            keywords.append(peer_ip)
        else:
            generic_ip = re.search(r'\b([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\b', text)
            if generic_ip:
                peer_ip = generic_ip.group(1)

        # 5. Normalized Severity
        if any(s in lower for s in ["down", "dead", "reset", "expired", "split_brain", "critical", "fail", "fatal"]):
            severity = SeverityLevel.CRITICAL.value
        elif any(s in lower for s in ["error", "degraded", "retransmission", "mismatch", "loss"]):
            severity = SeverityLevel.ERROR.value
        elif any(s in lower for s in ["warning", "flap", "timeout"]):
            severity = SeverityLevel.WARNING.value
        else:
            severity = SeverityLevel.INFO.value

        # 6. Device Hostname Extraction
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

    def batch_parse(self, logs: List[str], device_hint: Optional[str] = None) -> List[ParsedTelemetry]:
        """Batch parse multiple raw logs."""
        return [self.parse_log(log, device_hint=device_hint) for log in logs if log.strip()]
