import asyncio
import logging
import socket
from dataclasses import dataclass
from enum import Enum, IntFlag
from typing import Dict, List, Optional, Tuple

import telnetlib3

from .eth_utils import get_active_ethernet_ips


@dataclass
class NetworkEndpoint:
    """Represents a discovered Lantronix XPORT network endpoint.
    
    Contains the identifying information for a Lantronix device found during
    network discovery via UDP broadcast.
    
    Attributes:
        mac: MAC address in format 'XX:XX:XX:XX:XX:XX' (uppercase)
        ip: IPv4 address in dotted decimal format (e.g., '192.168.1.100')
    
    Example:
        >>> endpoint = NetworkEndpoint(mac='00:80:A3:12:34:56', ip='192.168.1.100')
        >>> print(f"Device at {endpoint.ip} has MAC {endpoint.mac}")
    """
    mac: str
    ip: str


# Define constants
BROADCAST_IP = '255.255.255.255'
UDP_PORT = 30718  # Lantronix Discovery Protocol port
TELNET_PORT = 23  # Telnet Port (default: 23)
TIMEOUT = 0.4  # Timeout for UDP response

# Global module locker
logger = logging.getLogger(__name__)


class FlowControlMode(Enum):
    """Flow control modes for Lantronix XPORT serial-to-ethernet adapters.
    
    These modes control how the XPORT handles XON/XOFF flow control characters
    during serial communication. Different modes determine whether flow control
    is applied and whether control characters are forwarded to the host.
    
    For device communication, XON_XOFF_PASS_TO_HOST mode is required to
    allow the host application to see flow control characters sent by the device.
    
    Attributes:
        NO_FLOW_CONTROL (0x00): No flow control applied. Data flows without
            any throttling. Use when devices don't support flow control.
        
        XON_XOFF (0x01): Software flow control using XON (0x11) and XOFF (0x13)
            characters. XPORT handles flow control internally and strips these
            characters. Not suitable for piezo devices.
        
        RTS_CTS (0x02): Hardware flow control using RTS (Request to Send) and
            CTS (Clear to Send) pins. Physical wiring required. Not typically
            used with piezo devices.
        
        XON_XOFF_PASS_TO_HOST (0x05): Software flow control where XON/XOFF
            characters are forwarded to the host instead of being handled by
            the XPORT. **Required for piezo device communication.** This allows
            the library to use XON as a message delimiter.
    
    Example:
        >>> # Configure XPORT for piezo device use
        >>> await configure_flow_control(
        ...     '192.168.1.100',
        ...     FlowControlMode.XON_XOFF_PASS_TO_HOST
        ... )
    
    Note:
        - XON_XOFF_PASS_TO_HOST is the default and recommended mode
    """

    NO_FLOW_CONTROL = 0x00
    """No flow control is applied."""

    XON_XOFF = 0x01
    """Software-based flow control using XON/XOFF characters."""

    RTS_CTS = 0x02
    """Hardware flow control using RTS (Request to Send) and CTS (Clear to Send) lines."""

    XON_XOFF_PASS_TO_HOST = 0x05
    """Software-based flow control using XON/XOFF characters - pass XON/XOFF characters to the host."""



async def send_udp_broadcast_async(local_ip: str) -> List[Tuple[bytes, Tuple[str, int]]]:
    """Send UDP broadcast for Lantronix device discovery from specific interface.
    
    Sends a Lantronix Device Discovery Protocol packet (0x00 0x00 0x00 0xF6)
    via UDP broadcast on port 30718 from the specified local IP address.
    Listens for responses within a timeout period.
    
    This function binds to a specific network interface to send the broadcast,
    allowing discovery on multi-homed systems.

    Args:
        local_ip: Local IP address of the network interface to use for broadcast
            (e.g., '192.168.1.50'). Must be a valid IP on an active interface.

    Returns:
        List of tuples, each containing:
        - bytes: Raw response data from Lantronix device
        - Tuple[str, int]: Source address (IP, port) of responding device
        
        Returns empty list if no devices respond or on error.

    Example:
        >>> # Broadcast on specific interface
        >>> responses = await send_udp_broadcast_async('192.168.1.50')
        >>> for data, (ip, port) in responses:
        ...     print(f"Response from {ip}:{port}")
    
    Note:
        - Uses UDP port 30718 (Lantronix Discovery Protocol)
        - Timeout is 0.4 seconds (400ms)
        - Broadcast to 255.255.255.255
        - Requires appropriate network permissions
        - May not work on networks that block broadcasts
        - Errors are logged but don't raise exceptions
    """
    # Create a UDP socket
    loop = asyncio.get_event_loop()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((local_ip, UDP_PORT))
    s.setblocking(False)  # Non-blocking mode

    # List to store responses
    broadcast_responses = []

    # Set up a UDP broadcast message
    try:
        s.sendto(bytearray([0x00, 0x00, 0x00, 0xF6]), (BROADCAST_IP, UDP_PORT))  # Lantronix Discovery Packet

        # Timeout for receiving responses
        async def receive_response():
            while True:
                received_data = await loop.sock_recvfrom(s, 65565)
                broadcast_responses.append(received_data)

        # Use asyncio's event loop to wait for responses
        await asyncio.wait_for(receive_response(), timeout=TIMEOUT)
    except asyncio.TimeoutError:
        pass
    except (ValueError, IndexError) as e:
        logger.error("Error sending UDP broadcast: %s", e)
        broadcast_responses = []
    finally:
        s.close()

    return broadcast_responses


def find_device_by_mac(device_list: List[NetworkEndpoint], target_mac: str) -> Optional[str]:
    """Search for a device by MAC address in discovered device list.
    
    Linear search through list of NetworkEndpoint objects to find a device
    with matching MAC address and return its IP address.

    Args:
        device_list: List of discovered NetworkEndpoint objects with mac and ip
        target_mac: MAC address to search for (format: 'XX:XX:XX:XX:XX:XX')

    Returns:
        IP address string if device found, None otherwise
    
    Example:
        >>> devices = await discover_lantronix_devices_async()
        >>> ip = find_device_by_mac(devices, '00:80:A3:12:34:56')
        >>> if ip:
        ...     print(f"Device found at {ip}")
    
    Note:
        - Case-sensitive MAC address comparison
        - Returns first match only
        - Helper function used by discover_lantronix_device_async
    """
    for dev in device_list:
        if dev.mac == target_mac:
            return dev.ip
    return None


async def discover_lantronix_devices_async() -> List[NetworkEndpoint]:
    """Discover all Lantronix XPORT devices on all active network interfaces.
    
    Sends UDP broadcast discovery packets from each active Ethernet interface
    on the system and collects responses from Lantronix devices. Discovery
    runs concurrently across all interfaces for efficiency.
    
    Process:
    1. Enumerate all active Ethernet interfaces with IP addresses
    2. Send UDP broadcast from each interface concurrently
    3. Parse responses to extract MAC and IP addresses
    4. Filter for valid Lantronix devices (MAC prefix 00:80:A3)
    5. Return aggregated list of discovered endpoints

    Returns:
        List of NetworkEndpoint objects, each containing:
        - mac: Device MAC address (format: 'XX:XX:XX:XX:XX:XX')
        - ip: Device IP address (format: 'xxx.xxx.xxx.xxx')
        
        Returns empty list if no devices found.

    Example:
        >>> # Discover all Lantronix devices on network
        >>> devices = await discover_lantronix_devices_async()
        >>> for device in devices:
        ...     print(f"Found device at {device.ip} (MAC: {device.mac})")
        >>> 
        >>> # Found device at 192.168.1.100 (MAC: 00:80:A3:12:34:56)
        >>> # Found device at 192.168.10.50 (MAC: 00:80:A3:AB:CD:EF)
    
    Note:
        - Discovers devices on all active Ethernet interfaces
        - Each interface discovery runs concurrently (parallel)
        - Only returns devices with Lantronix MAC prefix (00:80:A3)
        - Requires network broadcast support
        - May find duplicate devices if they're on multiple subnets
    """
    device_list: List[NetworkEndpoint] = []
    ips = [ip for _, ip in get_active_ethernet_ips()]

    async def discover_from_ip(ip: str) -> List[NetworkEndpoint]:
        responses = await send_udp_broadcast_async(ip)
        network_endpoints = parse_responses(responses)
        if network_endpoints:
            for endpoint in network_endpoints:
                logger.info("Interface %s detected device: %s", ip, endpoint)
        return network_endpoints

    # Launch all discovery coroutines in parallel
    results = await asyncio.gather(*(discover_from_ip(ip) for ip in ips))

    # Flatten list of lists
    for r in results:
        device_list.extend(r)

    return device_list


async def discover_lantronix_device_async(target_mac: str) -> Optional[str]:
    """Discover IP address of a specific Lantronix device by MAC address.
    
    Performs network discovery to find all Lantronix devices, then searches
    for a device matching the specified MAC address and returns its IP.

    Args:
        target_mac: MAC address to search for (format: 'XX:XX:XX:XX:XX:XX').
            Must have Lantronix prefix '00:80:A3'. Case-insensitive.

    Returns:
        IP address string (e.g., '192.168.1.100') if device found, None otherwise

    Example:
        >>> # Find device by MAC address
        >>> ip = await discover_lantronix_device_async('00:80:A3:12:34:56')
        >>> if ip:
        ...     print(f"Device found at {ip}")
        ...     protocol = TelnetProtocol(ip)
        ...     await protocol.connect()
        ... else:
        ...     print("Device not found on network")
    
    Note:
        - Searches all active network interfaces
        - Returns None if device not found or not powered on
        - Useful when you know device MAC but not current IP (DHCP)
    """
    devices = await discover_lantronix_devices_async()
    return find_device_by_mac(devices, target_mac)


def send_udp_broadcast(local_ip: str) -> List[Tuple[bytes, Tuple[str, int]]]:
    """Send UDP broadcast for device discovery (synchronous version).
    
    Synchronous blocking version of send_udp_broadcast_async. Sends Lantronix
    Discovery Protocol packet via UDP broadcast and collects responses.
    
    **Prefer using send_udp_broadcast_async for async code.**
    
    Args:
        local_ip: Local IP address of interface to broadcast from
    
    Returns:
        List of tuples, each containing:
        - bytes: Raw 30-byte response from device
        - Tuple[str, int]: Source (IP, port) of responding device
        
        Returns empty list if no responses or on error.
    
    Example:
        >>> responses = send_udp_broadcast('192.168.1.50')
        >>> for data, (ip, port) in responses:
        ...     print(f"Response from {ip}")
    
    Note:
        - Blocking I/O - not suitable for async applications
        - Uses socket.settimeout for response collection
        - For async code, use send_udp_broadcast_async instead
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((local_ip, UDP_PORT))
    s.settimeout(TIMEOUT)

    try:
        # Send discovery packet (Lantronix Device Discovery Protocol)
        s.sendto(bytearray([0x00, 0x00, 0x00, 0xF6]), (BROADCAST_IP, UDP_PORT))

        broadcast_responses = []
        while True:
            try:
                received_data = s.recvfrom(65565)  # Receive message (msg, (ip, port))
                broadcast_responses.append(received_data)
            except socket.timeout:
                break  # Exit loop when no more responses arrive

    except (ValueError, IndexError) as e:
        logger.error("Error sending UDP broadcast: %s", e)
        broadcast_responses = []

    finally:
        s.close()  # Ensure socket is closed
    return broadcast_responses


def discover_lantronix_devices() -> List[NetworkEndpoint]:
    """Discover Lantronix devices on network (synchronous version).
    
    Synchronous blocking version of discover_lantronix_devices_async.
    Sends UDP broadcasts from all active Ethernet interfaces sequentially
    and returns first successful discovery result.
    
    **Prefer using discover_lantronix_devices_async for async code.**

    Returns:
        List of NetworkEndpoint objects from first successful interface, or
        empty list if no devices found on any interface
    
    Example:
        >>> devices = discover_lantronix_devices()
        >>> for device in devices:
        ...     print(f"Found {device.mac} at {device.ip}")
    
    Note:
        - Blocking I/O - not suitable for async applications
        - Checks interfaces sequentially (not parallel)
        - Returns after first successful discovery
        - For async code, use discover_lantronix_devices_async instead
    """
    for _, ip in get_active_ethernet_ips():
        device_responses = send_udp_broadcast(ip)
        if not device_responses:
            continue
        device_list = parse_responses(device_responses)
        if device_list:
            return device_list
    return []


def discover_lantronix_device(target_mac: str) -> Optional[str]:
    """Discover specific Lantronix device by MAC address (synchronous version).

    Synchronous blocking version of discover_lantronix_device_async.
    Performs network discovery and searches for device with matching MAC.
    
    **Prefer using discover_lantronix_device_async for async code.**

    Args:
        target_mac: MAC address to search for (format: 'XX:XX:XX:XX:XX:XX')

    Returns:
        IP address string if device found, None otherwise
    
    Example:
        >>> ip = discover_lantronix_device('00:80:A3:12:34:56')
        >>> if ip:
        ...     print(f"Device at {ip}")
    
    Note:
        - Blocking I/O - not suitable for async applications
        - For async code, use discover_lantronix_device_async instead
        - Does not validate MAC address format (no ValueError raised)
    """
    devices = discover_lantronix_devices()
    return find_device_by_mac(devices, target_mac)


LANTRONIX_RESPONSE_SIZE = 30  # Expected size of Lantronix response
LAMNTONIX_MAC_PREFIX = "00:80:A3"  # Lantronix MAC address prefix


def parse_responses(response_list: List[Tuple[bytes, Tuple[str, int]]]) -> List[NetworkEndpoint]:
    """Parse Lantronix discovery protocol responses to extract device information.
    
    Processes raw UDP response data from Lantronix devices, extracting MAC
    addresses and validating they are genuine Lantronix devices. Only devices
    with proper response size and Lantronix MAC prefix are included.
    
    Response Format:
        Lantronix devices respond with 30 bytes containing device configuration.
        MAC address is encoded in bytes 24-29 (hex offset 48-59).

    Args:
        response_list: List of tuples from UDP responses, each containing:
            - bytes: Raw 30-byte response data
            - Tuple[str, int]: Source (IP, port) of responding device

    Returns:
        List of NetworkEndpoint objects for valid Lantronix devices. Each contains:
        - mac: Extracted MAC address (uppercase, format 'XX:XX:XX:XX:XX:XX')
        - ip: IP address from response source
        
        Returns empty list if no valid responses.

    Example:
        >>> responses = await send_udp_broadcast_async('192.168.1.50')
        >>> endpoints = parse_responses(responses)
        >>> for endpoint in endpoints:
        ...     print(f"{endpoint.mac} at {endpoint.ip}")
    
    Note:
        - Expects exactly 30-byte responses (LANTRONIX_RESPONSE_SIZE)
        - Validates MAC prefix is '00:80:A3' (Lantronix OUI)
        - Invalid responses are silently skipped with error logging
        - MAC addresses are returned in uppercase with colons
    """
    parsed_devices = []
    for data, address in response_list:
        try:
            if len(data) != LANTRONIX_RESPONSE_SIZE:
                continue
            mac_hex = data.hex()
            mac_address = ':'.join(mac_hex[48:60][i:i + 2] for i in range(0, 12, 2)).upper()
            if not mac_address.startswith(LAMNTONIX_MAC_PREFIX):
                continue
            parsed_devices.append(NetworkEndpoint(mac=mac_address, ip=address[0]))
        except Exception as e:
            logger.error("Error parsing response: %s", e)

    return parsed_devices



async def configure_flow_control(host: str, mode: FlowControlMode = FlowControlMode.XON_XOFF_PASS_TO_HOST) -> bool:
    """Configure Lantronix XPORT serial flow control mode.
    
    Connects to the XPORT configuration port (9999) via Telnet, navigates the
    configuration menu, sets the flow control mode for Channel 1, saves the
    configuration, and waits for device reboot. This is required to enable
    proper communication with piezo devices.
    
    The function automatically:
    1. Connects to XPORT configuration interface (port 9999)
    2. Reads current configuration to check if change needed
    3. If needed, navigates menu to flow control setting
    4. Sets specified flow control mode
    5. Saves configuration to non-volatile memory
    6. Waits for device to reboot and become available
    
    Configuration Process:
        - Opens Telnet to port 9999 (XPORT config interface)
        - Navigates through 19 Channel 1 configuration parameters
        - Changes parameter #2 (flow control)
        - Saves with menu option '9'
        - Waits up to 25 seconds for reboot completion

    Args:
        host: IP address of Lantronix XPORT device to configure
        mode: Desired flow control mode. Default: XON_XOFF_PASS_TO_HOST

    Returns:
        True if configuration was changed
        False if configuration was already set to desired mode (no change)

    Raises:
        asyncio.TimeoutError: If:
            - Cannot connect to config port within 7 seconds
            - Device doesn't reboot within 25 seconds

    Example:
        >>> # Configure XPORT for piezo device communication
        >>> changed = await configure_flow_control('192.168.1.100')
        >>> if changed:
        ...     print("XPORT configured and rebooted")
        ... else:
        ...     print("XPORT already configured correctly")
        >>> 
        >>> # Set different mode
        >>> await configure_flow_control(
        ...     '192.168.1.100',
        ...     FlowControlMode.NO_FLOW_CONTROL
        ... )
    
    Note:
        - Configuration is saved to XPORT non-volatile memory
        - Requires access to TCP port 9999 (config port)
        - Safe to call repeatedly (checks if change needed first)
        - XON_XOFF_PASS_TO_HOST mode is required for this library
    """

    CHANNEL1_PARAM_COUNT = 19
    PARAM_FLOW_CONTROL = 2
    STORE_CONFIG_MENU_OPTION = "9\r"
    port = 9999

    async def connect_telnet(host: str):
        """
        Connect to XPORT configuration port 9999
        """
        return await asyncio.wait_for(telnetlib3.open_connection(host, port), timeout=7)

    async def read_data(reader, size=2048, context=""):
        """
        Asnyc read data with debug output
        """
        data = await reader.read(size)
        logger.debug("Read data (%s): %r", context, data)
        return data

    async def write_data(writer, data, context=""):
        """
        Write data with debug output
        """
        writer.write(data)
        logger.debug("Write data (%s): %r", context, data)

    async def verify_rebooted(timeout: int):
        """
        Verify that the device has rebooted by checking if it is possible to connect to the telnet port 9999
        """
        try:
            await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
        except asyncio.TimeoutError as e:
            raise asyncio.TimeoutError(f"Timeout: Unable to connect to {host}:{port} within {timeout} seconds") from e


    reader, writer = await connect_telnet(host)

    try:
        await read_data(reader, 1024, "initial connection message")
        await write_data(writer, "\r", "initial prompt")
        await asyncio.sleep(0.1)
        configuration = await read_data(reader, 4096, "configuration setup")

        if f"Flow 0{mode.value}" in configuration:
            logger.info("Flow control already set to %s", mode.name)
            return False

        await write_data(writer, "1\r", "enter channel 1 config")
        for i in range(CHANNEL1_PARAM_COUNT):
            await asyncio.sleep(0.05)
            await read_data(reader, 2048, f"menu param {i}")
            data_to_write = f"0{mode.value}\r" if i == PARAM_FLOW_CONTROL else "\r"
            await write_data(writer, data_to_write, f"menu param {i} input")

        await asyncio.sleep(0.05)
        await read_data(reader, 2048, "post param config")
        await write_data(writer, STORE_CONFIG_MENU_OPTION, "store config")
        await read_data(reader, 2048, "store config response")
        await asyncio.sleep(5)

    finally:
        writer.close()
        reader.close()

    await verify_rebooted(25)
    return True


# async Main execution
async def main_async():
    # TARGET_MAC: str = "00:80:A3:79:C6:18"
    # ip = await discover_lantronix_device_async(TARGET_MAC)
    # if ip:
    #     print(f"Device with MAC {TARGET_MAC} found at IP: {ip}")
    # else:
    #     print(f"Device with MAC {TARGET_MAC} not found.")
    network_endpoints = await discover_lantronix_devices_async()
    print("Devices found:")
    for network_endpoint in network_endpoints:
        print(network_endpoint)


def main():
    TARGET_MAC: str = "00:80:A3:79:C6:18"
    ip = discover_lantronix_device(TARGET_MAC)
    if ip:
        print(f"Device with MAC {TARGET_MAC} found at IP: {ip}")
    else:
        print(f"Device with MAC {TARGET_MAC} not found.")


# Running the async main function
if __name__ == "__main__":
    asyncio.run(main_async())
    # main()
    # asyncio.run(configure_flow_control("192.168.10.177", FlowControlMode.XON_XOFF))