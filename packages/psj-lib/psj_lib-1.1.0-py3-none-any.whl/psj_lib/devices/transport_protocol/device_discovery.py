"""Asynchronous device discovery for piezoelectric amplifier devices.

This module provides functionality to automatically discover and identify piezo
devices connected via various transport protocols (Serial/USB and Telnet/Network).
Discovery runs concurrently across all enabled transports and returns a unified
list of detected devices.

Key Features:
    - Concurrent discovery across multiple transport types
    - Configurable discovery scope via DiscoverFlags
    - Device type identification via callback mechanism
    - Automatic transport parameter configuration (optional)
    - Returns DetectedDevice instances with connection information

Typical Usage:
    >>> # Discover all devices on all interfaces
    >>> devices = await DeviceDiscovery.discover_devices(
    ...     flags=DiscoverFlags.ALL_INTERFACES
    ... )
    >>> 
    >>> # Discover only serial-connected devices
    >>> devices = await DeviceDiscovery.discover_devices(
    ...     flags=DiscoverFlags.DETECT_SERIAL
    ... )
"""

import asyncio
import logging
from enum import Flag, auto
from typing import List, Optional

from .transport_protocol import TRANSPORT_REGISTRY, DiscoveryCallback, TransportType
from .transport_types import DetectedDevice

# Global module locker
logger = logging.getLogger(__name__)

class DiscoverFlags(Flag):
    """Configuration flags for device discovery behavior.

    These flags control which interfaces are scanned and what configuration
    actions are performed during discovery. Flags can be combined using the
    bitwise OR operator (|) to enable multiple options.

    Attributes:
        DETECT_SERIAL: Scan for devices on serial/USB ports.
            Enumerates all available serial ports and attempts device
            communication on each.
        
        DETECT_ETHERNET: Scan for devices on the network.
            Performs network discovery (broadcast/multicast or known ports)
            to find Telnet-accessible devices.
        
        ADJUST_COMM_PARAMS: Automatically configure communication parameters.
            For Telnet devices, configures Lantronix XPORT module settings
            (flow control mode, etc.). May add significant discovery time.
        
        ALL_INTERFACES: Enable both serial and ethernet discovery.
            Equivalent to DETECT_SERIAL | DETECT_ETHERNET.
        
        ALL: Enable all discovery features.
            Equivalent to ALL_INTERFACES | ADJUST_COMM_PARAMS.
            Scans all interfaces and configures found devices.

    Example:
        >>> # Discover serial devices only
        >>> flags = DiscoverFlags.DETECT_SERIAL
        >>> 
        >>> # Discover all interfaces without auto-configuration
        >>> flags = DiscoverFlags.DETECT_SERIAL | DiscoverFlags.DETECT_ETHERNET
        >>> # or equivalently:
        >>> flags = DiscoverFlags.ALL_INTERFACES
        >>> 
        >>> # Full discovery with auto-configuration
        >>> flags = DiscoverFlags.ALL
    
    Note:
        - ADJUST_COMM_PARAMS only affects Telnet/network devices
        - Discovery time increases with more enabled options
        - Serial discovery requires appropriate system permissions
    """
    DETECT_SERIAL = auto()
    DETECT_ETHERNET = auto()
    ADJUST_COMM_PARAMS = auto()  # Adjust communication parameters automatically
    ALL_INTERFACES = DETECT_SERIAL | DETECT_ETHERNET
    ALL = ALL_INTERFACES | ADJUST_COMM_PARAMS

    @staticmethod
    def flags_for_transport(transport: Optional[TransportType] = None) -> 'DiscoverFlags':
        """Convert a TransportType to corresponding DiscoverFlags.
        
        This helper method maps transport types to their appropriate discovery
        flags, simplifying selective discovery operations.

        Args:
            transport: The transport type to discover. Options:
                - None: Discover all transport types (returns ALL_INTERFACES)
                - TransportType.SERIAL: Discover serial devices only
                - TransportType.TELNET: Discover network devices only

        Returns:
            DiscoverFlags configured for the specified transport type

        Raises:
            ValueError: If an unsupported/unknown transport type is provided

        Example:
            >>> # Get flags for serial discovery
            >>> flags = DiscoverFlags.flags_for_transport(TransportType.SERIAL)
            >>> # flags == DiscoverFlags.DETECT_SERIAL
            >>> 
            >>> # Get flags for all transports
            >>> flags = DiscoverFlags.flags_for_transport(None)
            >>> # flags == DiscoverFlags.ALL_INTERFACES
        
        Note:
            Commonly used internally by discovery system but available for
            convenience when building discovery configurations.
        """
        if transport is None:
            return DiscoverFlags.ALL_INTERFACES
        elif transport == TransportType.SERIAL:
            return DiscoverFlags.DETECT_SERIAL
        elif transport == TransportType.TELNET:
            return DiscoverFlags.DETECT_ETHERNET
        else:
            raise ValueError(f"Unsupported transport type: {transport}")


class DeviceDiscovery:
    """Internal utility class for discovering piezoelectric devices across transports.
    
    DeviceDiscovery provides a high-level interface for scanning and identifying
    piezo devices connected via Serial (USB/RS-232) and Telnet (network)
    interfaces. Discovery runs concurrently across all enabled transports.
    
    The discovery process:
    1. Scan enabled interfaces based on DiscoverFlags
    2. Attempt basic communication with each found device
    3. Call discovery_cb to identify and filter device types  
    4. Optionally configure communication parameters
    5. Return list of DetectedDevice objects
    
    Example:
        >>> # Discover all devices
        >>> devices = await DeviceDiscovery.discover_devices(
        ...     flags=DiscoverFlags.ALL_INTERFACES
        ... )
        >>> print(f"Found {len(devices)} devices")
        >>> 
        >>> # Create device instances from discoveries
        >>> device_instances = [
        ...     DeviceFactory.from_detected_device(d) for d in devices
        ... ]
    
    Note:
        - This is a utility class with static methods only
        - Discovery can take several seconds to complete
        - Requires appropriate permissions for serial port access
        - Network discovery may be affected by firewalls
    """
    @staticmethod
    async def discover_devices(
        discovery_cb: DiscoveryCallback,
        flags: DiscoverFlags = DiscoverFlags.ALL_INTERFACES,
    ) -> List[DetectedDevice]:
        """Discover devices across enabled transport interfaces.

        Scans for devices using the transports enabled by flags, running
        discovery operations concurrently for better performance. Each
        discovered device is identified using the provided callback.
        
        Discovery Process:
        1. Determine which transports to scan based on flags
        2. Launch concurrent discovery tasks for each enabled transport
        3. Each transport implementation scans its medium:
           - Serial: Enumerate and test all available ports
           - Telnet: Scan network for responding devices
        4. Call discovery_cb for each potential device to:
           - Identify device type (send identification command)
           - Filter for desired device models
           - Extract extended device information
        5. Aggregate results from all transports
        6. Optionally adjust communication parameters if ADJUST_COMM_PARAMS set

        Args:
            discovery_cb: Async callback function for device identification.
                Signature: async def callback(transport: TransportProtocol, 
                                            detected: DetectedDevice) -> bool
                - Receives temporary transport connection and partial DetectedDevice
                - Should identify device type and populate device_id field
                - Returns True to include device, False to skip
                
            flags: Discovery scope and configuration. Options:
                - DiscoverFlags.DETECT_SERIAL: Serial/USB only
                - DiscoverFlags.DETECT_ETHERNET: Network only
                - DiscoverFlags.ALL_INTERFACES: Both transports
                - DiscoverFlags.ADJUST_COMM_PARAMS: Configure devices
                - DiscoverFlags.ALL: All features
                Default: ALL_INTERFACES

        Returns:
            List of DetectedDevice objects, each containing:
                - device_id: Identified device model (e.g., 'd-drive')
                - transport: TransportType (SERIAL or TELNET)
                - identifier: Connection string (port or IP address)
                - extended_info: Optional additional device data

        Example:
            >>> # Custom discovery callback
            >>> async def identify_d_drive(transport, detected):
            ...     await transport.write('identify\r\n')
            ...     response = await transport.read_message()
            ...     if 'd-drive' in response:
            ...         detected.device_id = 'd-drive'
            ...         return True
            ...     return False
            >>> 
            >>> # Discover only d-Drive devices
            >>> devices = await DeviceDiscovery.discover_devices(
            ...     discovery_cb=identify_d_drive,
            ...     flags=DiscoverFlags.ALL_INTERFACES
            ... )
            >>> 
            >>> # Typical usage via PiezoDevice class method
            >>> devices = await DDriveDevice.discover_devices()

        Note:
            - Discovery can take 5-30 seconds depending on scope
            - Serial discovery requires read/write port permissions
            - Network discovery may trigger firewall warnings
            - ADJUST_COMM_PARAMS adds significant time (device resets)
            - Empty list returned if no devices found
            - Devices must be powered on to be discovered
        """

        devices: List[DetectedDevice] = []

        # Create discovery tasks for each enabled transport type
        tasks = [
            protocol.discover_devices(discovery_cb)
            for transport_type, protocol in TRANSPORT_REGISTRY.items()
            if flags & DiscoverFlags.flags_for_transport(transport_type)
        ]

        # Run all discovery tasks concurrently and gather results
        results = await asyncio.gather(*tasks)

        for result in results:
            devices.extend(result)

        return devices