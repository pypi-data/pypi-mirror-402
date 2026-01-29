"""Example 2: Simple Position Control

This example demonstrates how to:
- Connect to a d-Drive device
- Enable closed-loop control
- Set target positions (setpoint)
- Read actual position from sensor
- Compare open-loop vs closed-loop operation

This is the foundation for all position control applications.
"""

import asyncio
from psj_lib import DDriveDevice, TransportType, DDriveStatusRegister


async def main():
    print("=" * 60)
    print("d-Drive Simple Position Control")
    print("=" * 60)
    
    # Connect to device (adjust COM port as needed)
    device = DDriveDevice(TransportType.SERIAL, 'COM1')
    await device.connect()
    print(f"✓ Connected to device with {len(device.channels)} channel(s)\n")
    
    channel = device.channels[0]
    
    try:
        # Check current status
        print("[1] Reading device status...")
        status: DDriveStatusRegister = await channel.status_register.get()
        print(f"  Actuator connected: {status.actor_plugged}")
        print(f"  Sensor type: {status.sensor_type.name}")
        print(f"  Closed-loop active: {status.closed_loop}\n")
        
        # Test 1: Open-Loop Control
        print("[2] Testing Open-Loop Control...")
        await channel.closed_loop_controller.set(False)
        print("  ✓ Closed-loop disabled (open-loop mode)")
        
        # In open-loop, setpoint directly controls voltage
        await channel.setpoint.set(50.0)
        await asyncio.sleep(1)
        
        setpoint = await channel.setpoint.get()
        position = await channel.position.get()
        print(f"  Setpoint: {setpoint:.2f} V")
        print(f"  Position: {position:.2f} V")
        
        # Test 2: Closed-Loop Control
        print("[3] Testing Closed-Loop Control...")
        await channel.closed_loop_controller.set(True)
        print("  ✓ Closed-loop enabled (feedback control active)")
        
        # Move to different positions
        target_positions = [30.0, 50.0, 70.0, 50.0]
        
        for target in target_positions:
            print(f"\n  Moving to {target:.1f} µm...")
            await channel.setpoint.set(target)
            await asyncio.sleep(1)  # Allow time to settle
            
            actual = await channel.position.get()
            error = abs(target - actual)
            
            print(f"    Target: {target:.2f} µm")
            print(f"    Actual: {actual:.2f} µm")
            print(f"    Error:  {error:.2f} µm")
            
            if error < 0.5:
                print("    ✓ Position achieved!")
            else:
                print("    ⚠ Large position error")
        
        # Final position reading
        print("\n[4] Final Status...")
        final_pos = await channel.position.get()
        temp = await channel.temperature.get()
        print(f"  Position: {final_pos:.2f} µm")
        print(f"  Temperature: {temp:.1f}°C")
        
    finally:
        await device.close()
        print("\n✓ Disconnected")
    
    print("\n" + "=" * 60)
    print("Position Control Summary:")
    print("- Open-loop: Direct voltage control, no feedback")
    print("- Closed-loop: Sensor feedback for precise positioning")
    print("- Always use closed-loop for accurate position control")
    print("- Allow settling time after position changes")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())