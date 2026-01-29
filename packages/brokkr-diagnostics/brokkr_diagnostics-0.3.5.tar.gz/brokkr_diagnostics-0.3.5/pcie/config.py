# PCIe Error Flag Classifications and Data Models

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class PCIeDevice:
    """Represents a single PCIe device"""
    bus_id: str
    vendor_id: str
    device_id: str
    class_id: str
    revision_id: str
    subsystem_vendor: Optional[str] = None
    subsystem_device: Optional[str] = None
    config_space: Optional[bytes] = None
    link_speed: Optional[str] = None
    link_width: Optional[str] = None
    errors: List[str] = field(default_factory=list)


@dataclass
class LspciCheckResult:
    """Results from lspci diagnostic checks"""
    timestamp: datetime
    lspci_available: bool
    tree_view: Optional[str] = None
    devices_list: Optional[str] = None
    verbose_dump: Optional[str] = None
    devices: List[PCIeDevice] = field(default_factory=list)
    nvidia_devices: List[PCIeDevice] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# Critical uncorrectable errors (data corruption risk)
CRITICAL_UE_FLAGS = {
    "DLP+",       # Data Link Protocol Error
    "SDES+",      # Surprise Down Error Status
    "TLP+",       # Transaction Layer Packet Error
    "FCP+",       # Flow Control Protocol Error
    "CmpltTO+",   # Completion Timeout
    "CmpltAbrt+", # Completer Abort
    "UnxCmplt+",  # Unexpected Completion
    "RxOF+",      # Receiver Overflow
    "MalfTLP+",   # Malformed TLP
    "ECRC+",      # ECRC Error
    "ACSViol+",   # ACS Violation
}

# Benign uncorrectable (usually software probing)
BENIGN_UE_FLAGS = {
    "UnsupReq+",  # Unsupported Request
}

# Critical correctable errors
CRITICAL_CE_FLAGS = {
    "RxErr+",     # Receiver Error
    "BadTLP+",    # Bad TLP
    "BadDLLP+",   # Bad DLLP
    "Rollover+",  # Replay Number Rollover
    "Timeout+",   # Replay Timer Timeout
}

# Benign correctable
BENIGN_CE_FLAGS = {
    "AdvNonFatalErr+",  # Advisory Non-Fatal Error
}
