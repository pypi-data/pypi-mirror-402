"""Example 1: Device Discovery and Connection

This example demonstrates how to:
- Discover available Piezoamplifiers on all interfaces (Serial and Telnet)
- Connect to a discovered device
- Display device information
- List available channels
- Properly disconnect

This is the starting point for all d-Drive operations.
"""

import asyncio
from psj_lib import PiezoDevice, DDriveDevice, DiscoverFlags


async def main():
    print("=" * 60)
    print("Piezo device discovery and connection")
    print("=" * 60)
    
    # Step 1: Discover all available Piezo devices
    print("\n[1] Discovering devices on all interfaces...")
    print("    (This searches both Serial and Telnet connections)")
    
    try:
        # Discover devices on all interfaces (Serial + Telnet)
        devices = await PiezoDevice.discover_devices(
            flags=DiscoverFlags.ALL_INTERFACES
        )
        
        if not devices:
            print("\n❌ No devices found!")
            print("\nTroubleshooting:")
            print("  - Check device is powered on")
            print("  - Verify USB/Serial cable is connected")
            print("  - Check device is on same network (for Telnet)")
            print("  - Ensure no other software has device open")
            return
        
        print(f"\n✓ Found {len(devices)} device(s):")
        print()
        
        # Step 2: Display information about each discovered device
        for i, device in enumerate(devices):
            info = device.device_info
            print(f"Device {i + 1}:")
            print(f"  Type:       {info.device_id}")
            print(f"  Transport:  {info.transport_info.transport.name}")
            print(f"  Identifier: {info.transport_info.identifier}")
            print()
        
        # Step 3: Connect to the first d-Drive device found
        print("[2] Connecting to first d-Drive device...")
        device = next(
            (d for d in devices if isinstance(d, DDriveDevice)),
            None
        )
        
        if device is None:
            print("❌ No d-Drive device found!")
            return
        
        await device.connect()
        print("✓ Connected successfully!")
        
        # Step 4: Display device information
        print("\n[3] Connected device Information:")
        info = device.device_info
        print(f"  Device Type: {info.device_id}")
        print(f"  Connection:  {info.transport_info.transport.name} "
              f"on {info.transport_info.identifier}")
        
        # Step 5: Display available channels
        print("\n[4] Available Channels:")
        if not device.channels:
            print("  No channels found!")
        else:
            print(f"  Total channels: {len(device.channels)}")
            for channel_id, channel in device.channels.items():
                print(f"    - Channel {channel_id}")
        
        # Step 6: Query basic information from channels
        if device.channels:
            for channel_id, channel in device.channels.items():
                print(f"\n[5] Querying Channel {channel_id} Information:")
                
                # Read temperature
                try:
                    temp = await channel.temperature.get()
                    print(f"  Temperature: {temp:.1f}°C")
                except Exception as e:
                    print(f"  Temperature: (error - {e})")
                
                # Read status
                try:
                    status = await channel.status_register.get()
                    print(f"  Status:")
                    print(f"    - Actuator plugged: {status.actor_plugged}")
                    print(f"    - Sensor type: {status.sensor_type.name}")
                    print(f"    - Closed-loop: {status.closed_loop}")
                    print(f"    - Voltage enabled: {status.piezo_voltage_enabled}")
                except Exception as e:
                    print(f"  Status: (error - {e})")

                print()
        
        print("[6] Disconnecting...")
        await device.close()
        print("✓ Disconnected successfully!")
        
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
