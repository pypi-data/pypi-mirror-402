"""
PyKAP - Python Library for KAP (Kamuyu Aydınlatma Platformu) API
A comprehensive Python client for accessing Turkish Public Disclosure Platform data.
"""

from .client import KAPClient
from .models import (
    DisclosureInfo,
    DisclosureDetail,
    MemberInfo,
    FundInfo,
    BlockedDisclosure,
    CAProcessStatus
)

__version__ = "1.0.0"
__author__ = "PyKAP Contributors"
__all__ = [
    "KAPClient",
    "DisclosureInfo",
    "DisclosureDetail", 
    "MemberInfo",
    "FundInfo",
    "BlockedDisclosure",
    "CAProcessStatus"
]
