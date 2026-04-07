class IPv7Error(Exception):
    """Base class for IPv7 related exceptions."""


class RoutingError(IPv7Error):
    """Raised when routing lookup fails or an invalid route is used."""


class QuantumLinkError(IPv7Error):
    """Raised when a quantum link is expected but unavailable or malformed."""
