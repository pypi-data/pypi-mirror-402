class SentinelError(Exception):
    """Base error for evoSentinel."""
    pass

class SentinelBlockedError(SentinelError):
    """Raised when execution is blocked due to high risk."""
    pass

class SentinelQuarantinedError(SentinelError):
    """Raised when a function is currently in quarantine."""
    pass

class SentinelOverloadError(SentinelError):
    """Raised when the system is overloaded (e.g., concurrency limits)."""
    pass
