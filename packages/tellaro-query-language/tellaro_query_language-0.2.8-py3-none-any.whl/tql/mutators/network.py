"""Network-related mutators for IP address operations."""

import ipaddress
from typing import Any, Dict, Optional

from .base import BaseMutator, PerformanceClass


class IsPrivateMutator(BaseMutator):
    """
    Mutator that checks if an IP address is in a private range.

    Performance Characteristics:
    - In-memory: FAST - Simple IP range calculations
    - OpenSearch: MODERATE - Requires post-processing of all results

    This mutator returns True if the IP is in one of the RFC 1918 private ranges:
    - 10.0.0.0/8 (10.0.0.0 - 10.255.255.255)
    - 172.16.0.0/12 (172.16.0.0 - 172.31.255.255)
    - 192.168.0.0/16 (192.168.0.0 - 192.168.255.255)

    Also includes other private/special ranges:
    - 127.0.0.0/8 (loopback)
    - 169.254.0.0/16 (link-local)
    - fc00::/7 (IPv6 unique local)
    - fe80::/10 (IPv6 link-local)

    Used as a filter in queries like: ip | is_private()
    Returns True/False for filtering purposes.

    Example:
        source_ip | is_private()
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(params)
        self.performance_in_memory = PerformanceClass.FAST
        self.performance_opensearch = PerformanceClass.MODERATE

    def apply(self, field_name: str, record: Dict[str, Any], value: Any) -> Any:
        """Check if the value is a private IP address."""
        if value is None:
            return False

        # Handle lists - return True if any IP is private
        if isinstance(value, list):
            return any(self._is_private_ip(str(item)) for item in value if item is not None)

        # Single value
        return self._is_private_ip(str(value))

    def _is_private_ip(self, ip_str: str) -> bool:
        """Check if a single IP address is private."""
        try:
            ip_obj = ipaddress.ip_address(ip_str)

            # Check if it's a private address
            # This includes RFC 1918 for IPv4 and fc00::/7 for IPv6
            if ip_obj.is_private:
                return True

            # Also check other special-use addresses
            if ip_obj.is_loopback:  # 127.0.0.0/8 or ::1
                return True
            if ip_obj.is_link_local:  # 169.254.0.0/16 or fe80::/10
                return True
            if hasattr(ip_obj, "is_reserved") and ip_obj.is_reserved:  # Reserved addresses
                return True

            return False

        except (ValueError, AttributeError):
            # Not a valid IP address
            return False


class IsGlobalMutator(BaseMutator):
    """
    Mutator that checks if an IP address is globally routable.

    Performance Characteristics:
    - In-memory: FAST - Simple IP range calculations
    - OpenSearch: MODERATE - Requires post-processing of all results

    This mutator returns True if the IP is a globally routable address,
    meaning it's not:
    - Private (RFC 1918)
    - Loopback
    - Link-local
    - Multicast
    - Reserved
    - Unspecified

    Used as a filter in queries like: ip | is_global()
    Returns True/False for filtering purposes.

    Example:
        destination_ip | is_global()
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(params)
        self.performance_in_memory = PerformanceClass.FAST
        self.performance_opensearch = PerformanceClass.MODERATE

    def apply(self, field_name: str, record: Dict[str, Any], value: Any) -> Any:
        """Check if the value is a global IP address."""
        if value is None:
            return False

        # Handle lists - return True if any IP is global
        if isinstance(value, list):
            return any(self._is_global_ip(str(item)) for item in value if item is not None)

        # Single value
        return self._is_global_ip(str(value))

    def _is_global_ip(self, ip_str: str) -> bool:  # noqa: C901
        """Check if a single IP address is globally routable."""
        try:
            ip_obj = ipaddress.ip_address(ip_str)

            # Check if it's NOT any of the special-use addresses
            if ip_obj.is_private:
                return False
            if ip_obj.is_loopback:
                return False
            if ip_obj.is_link_local:
                return False
            if ip_obj.is_multicast:
                return False
            if ip_obj.is_unspecified:  # 0.0.0.0 or ::
                return False
            if hasattr(ip_obj, "is_reserved") and ip_obj.is_reserved:
                return False

            # For IPv4, also check some additional ranges
            if isinstance(ip_obj, ipaddress.IPv4Address):
                # Check for special ranges not covered by is_private
                ip_int = int(ip_obj)

                # 0.0.0.0/8 - "This" network
                if ip_int >> 24 == 0:
                    return False

                # 100.64.0.0/10 - Shared address space (CGN)
                if ip_int >> 22 == 0x191:  # 100.64/10
                    return False

                # 198.18.0.0/15 - Benchmarking
                if ip_int >> 17 == 0x18C9:  # 198.18/15
                    return False

                # 240.0.0.0/4 - Reserved (Class E)
                if ip_int >> 28 == 0xF:
                    return False

            # If it passed all checks, it's global
            return True

        except (ValueError, AttributeError):
            # Not a valid IP address
            return False
