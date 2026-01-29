"""Example 4: PID Tuning

This example demonstrates how to:
- Configure PID controller parameters
- Read out current PID settings

PID tuning is critical for optimal closed-loop performance.
"""

import asyncio
from psj_lib import DDriveDevice, TransportType


async def main():
    print("=" * 60)
    print("d-Drive PID Tuning Example")
    print("=" * 60)
    
    # Connect to device (adjust COM port as needed)
    device = DDriveDevice(TransportType.SERIAL, 'COM1')
    await device.connect()
    print(f"✓ Connected to device with {len(device.channels)} channel(s)\n")
    
    channel = device.channels[0]
    
    try:
        # Enable closed-loop control
        print("[1] Enabling closed-loop control...")
        await channel.closed_loop_controller.set(True)
        print("✓ Closed-loop enabled\n")
        
        # Read current PID parameters
        print("[2] Current PID Parameters:")
        p = await channel.pid_controller.get_p()
        i = await channel.pid_controller.get_i()
        d = await channel.pid_controller.get_d()
        print(f"  P (Proportional): {p:.2f}")
        print(f"  I (Integral):     {i:.2f}")
        print(f"  D (Derivative):   {d:.2f}\n")
        
        # Set new PID settings
        print("[3] Set new PID settings...")
        await channel.pid_controller.set(p=0.0, i=0.0, d=0.0)
        print("  Set: P=0.0, I=0.0, D=0.0\n")

        # Set to a test position
        print("[4] Moving to test position (50 µm)...")
        await channel.setpoint.set(50.0)
        print("✓ Move command sent\n")
        
        # Restore original settings
        print("[5] Restoring original PID settings...")
        await channel.pid_controller.set(p=p, i=i, d=d)
        print("✓ Original settings restored\n")
        
    finally:
        await device.close()
        print("✓ Disconnected")
    
    print("\n" + "=" * 60)
    print("PID Tuning Tips:")
    print("- Start with low gains and increase gradually")
    print("- P gain affects response speed")
    print("- I gain eliminates steady-state error")
    print("- D gain reduces overshoot and oscillation")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
