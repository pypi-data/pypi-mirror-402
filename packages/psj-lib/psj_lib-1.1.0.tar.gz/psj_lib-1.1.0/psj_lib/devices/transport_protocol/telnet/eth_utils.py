import ipaddress
import re
import socket

import psutil


def is_valid_ip(address: str) -> bool:
    """Validate if a string is a valid IPv4 or IPv6 address.
    
    Uses the ipaddress module to parse and validate IP address formats.
    Supports both IPv4 (e.g., '192.168.1.1') and IPv6 (e.g., '::1') formats.
    
    Args:
        address: String to validate as an IP address
    
    Returns:
        True if address is valid IPv4 or IPv6 format, False otherwise
    
    Example:
        >>> is_valid_ip('192.168.1.1')
        True
        >>> is_valid_ip('256.1.1.1')
        False
        >>> is_valid_ip('2001:db8::1')
        True
        >>> is_valid_ip('not-an-ip')
        False
    """
    try:
        ipaddress.ip_address(address)
        return True
    except ValueError:
        return False


_MAC_REGEX = re.compile(
    r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$|'  # e.g. 01:23:45:67:89:ab or 01-23-45-67-89-ab
    r'^([0-9A-Fa-f]{12})$'  # e.g. 0123456789ab (no separators)
)


def is_valid_mac(address: str) -> bool:
    """Validate if a string is a valid MAC address.
    
    Checks against common MAC address formats using regex pattern matching.
    Supports both separator-based and no-separator formats.
    
    Supported formats:
    - Colon separated: '01:23:45:67:89:AB'
    - Hyphen separated: '01-23-45-67-89-AB'
    - No separators: '0123456789AB'
    
    Case-insensitive for hex digits (a-f or A-F).
    
    Args:
        address: String to validate as a MAC address
    
    Returns:
        True if address matches valid MAC format, False otherwise
    
    Example:
        >>> is_valid_mac('00:80:A3:12:34:56')
        True
        >>> is_valid_mac('00-80-A3-12-34-56')
        True
        >>> is_valid_mac('0080A3123456')
        True
        >>> is_valid_mac('invalid')
        False
        >>> is_valid_mac('00:80:A3:12:34')  # Too short
        False
    """
    return bool(_MAC_REGEX.match(address))


def get_active_ethernet_ips():
    """Get all active network interfaces with their IPv4 addresses.
    
    Enumerates all network interfaces on the system, filters for active (UP)
    interfaces, and extracts their IPv4 addresses. This is used for network
    device discovery to determine which interfaces to broadcast from.
    
    The function checks interface status via psutil and only returns interfaces
    that are currently active and have IPv4 addresses assigned.

    Returns:
        List of tuples, each containing:
        - str: Interface name (e.g., 'eth0', 'en0', 'Ethernet 1')
        - str: IPv4 address in dotted decimal format (e.g., '192.168.1.50')
        
        Returns empty list if no active interfaces with IPv4 addresses.
    
    Example:
        >>> interfaces = get_active_ethernet_ips()
        >>> for name, ip in interfaces:
        ...     print(f"{name}: {ip}")
        >>> # eth0: 192.168.1.50
        >>> # wlan0: 192.168.1.51
    
    Note:
        - Only returns IPv4 addresses (AF_INET family)
        - Interface must be UP (operational status)
        - Includes all active interfaces (Ethernet, Wi-Fi, VPN, etc.)
        - Used by discover_lantronix_devices_async for multi-interface discovery
        - Cross-platform (Windows, Linux, macOS) via psutil
    """
    active_ethernet_ips = []

    # Retrieve network statistics (contains information about the status)
    stats = psutil.net_if_stats()

    # Iterate through all interfaces
    for interface, addrs in psutil.net_if_addrs().items():
        # Check if the interface is active (UP)
        # if stats[interface].isup and ("eth" in interface.lower() or "en" in interface.lower()):
        if stats[interface].isup:
            for addr in addrs:
                if addr.family == socket.AF_INET:  # Only IPv4 addresses
                    active_ethernet_ips.append((interface, addr.address))

    return active_ethernet_ips