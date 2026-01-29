"""
evoSentinel - Advanced Python Runtime Guard & Self-Healing Engine

Author: Daksha Dubey
License: MIT

A production-grade SDK for runtime defense and self-healing using
probabilistic decision-making and adaptive control systems.
"""

from .api import Sentinel, sentinel
from .errors import (
    SentinelError,
    SentinelBlockedError,
    SentinelQuarantinedError,
    SentinelOverloadError
)

__all__ = [
    "Sentinel",
    "sentinel",
    "SentinelError",
    "SentinelBlockedError",
    "SentinelQuarantinedError",
    "SentinelOverloadError"
]
