"""
VAT Enterprise Domain Enums & Value Constants
"""

from enum import Enum


class VendorPlatform(str, Enum):
    """Supported network hardware and software vendor platforms."""
    CISCO = "cisco"
    JUNIPER = "juniper"
    VELOCLOUD = "velocloud"
    ARISTA = "arista"
    NOKIA = "nokia"
    HUAWEI = "huawei"
    GENERIC = "generic"


class ProtocolType(str, Enum):
    """Supported network protocol families."""
    BGP = "bgp"
    OSPF = "ospf"
    IPSEC = "ipsec"
    EVPN = "evpn"
    INTERFACE = "interface"
    GENERAL = "general"


class SeverityLevel(str, Enum):
    """Normalized carrier incident severity grades."""
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class RiskLevel(str, Enum):
    """Remediation operational blast radius risk classification."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ConfigMode(str, Enum):
    """Target configuration modes for router/switch CLI."""
    INTERFACE = "interface"
    ROUTER_BGP = "router bgp"
    ROUTER_OSPF = "router ospf"
    SET = "set"
    SYSTEM = "system"
    CLI = "cli"
