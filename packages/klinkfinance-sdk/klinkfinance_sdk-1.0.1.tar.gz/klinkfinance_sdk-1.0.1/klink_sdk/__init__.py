"""
Klink Finance SDK for Python

Official Python SDK for the Klink Finance platform.
Provides access to both Publisher and Advertiser APIs.
"""

from .klink_sdk import KlinkSDK
from .types import Config
from .exceptions import (
    KlinkException,
    KlinkConfigException,
    KlinkAuthException,
    KlinkAPIException,
    KlinkNetworkException
)

__version__ = "1.0.0"
__all__ = [
    "KlinkSDK",
    "Config",
    "KlinkException",
    "KlinkConfigException",
    "KlinkAuthException",
    "KlinkAPIException",
    "KlinkNetworkException",
]
