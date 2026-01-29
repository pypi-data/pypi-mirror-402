"""Example 7: Filter Configuration

This example demonstrates how to:
- Configure notch filter for resonance suppression
- Configure low-pass filter for noise reduction
- Configure error low-pass filter for PID stability
- Compare system response with different filter settings

Proper filter configuration is essential for stable closed-loop operation.
"""

import asyncio
from psj_lib import DDriveDevice, TransportType


async def main():
    print("=" * 60)
    print("d-Drive Filter Configuration Example")
    print("=" * 60)
    
    # Connect to device
    device = DDriveDevice(TransportType.SERIAL, 'COM1')
    await device.connect()
    print(f"✓ Connected to device\n")
    
    channel = device.channels[0]
    
    try:
        # Enable closed-loop control
        await channel.closed_loop_controller.set(True)
        
        # Test 1: Notch Filter (for resonance suppression)
        print("[1] Configuring Notch Filter...")
        print("  Purpose: Suppress mechanical resonances")
        await channel.notch.set(
            enabled=True,
            frequency=500.0,  # Suppress 500 Hz resonance
            bandwidth=50.0    # 50 Hz bandwidth
        )
        enabled = await channel.notch.get_enabled()
        freq = await channel.notch.get_frequency()
        bw = await channel.notch.get_bandwidth()
        print(f"  ✓ Notch filter: {'Enabled' if enabled else 'Disabled'}")
        print(f"    Frequency: {freq:.1f} Hz, Bandwidth: {bw:.1f} Hz\n")
        
        # Test position step with notch filter
        print("  Testing with notch filter enabled...")
        await channel.setpoint.set(50.0)
        await asyncio.sleep(1)
        pos = await channel.position.get()
        print(f"  Position: {pos:.2f} µm\n")
        
        # Test 2: Low-Pass Filter (for noise reduction)
        print("[2] Configuring Low-Pass Filter...")
        print("  Purpose: Reduce high-frequency noise")
        await channel.lpf.set(
            enabled=True,
            cutoff_frequency=100.0  # 100 Hz cutoff
        )
        lpf_enabled = await channel.lpf.get_enabled()
        lpf_freq = await channel.lpf.get_cutoff_frequency()
        print(f"  ✓ Low-pass filter: {'Enabled' if lpf_enabled else 'Disabled'}")
        print(f"    Cutoff: {lpf_freq:.1f} Hz\n")
        
        # Test position step with LPF
        print("  Testing with low-pass filter enabled...")
        await channel.setpoint.set(70.0)
        await asyncio.sleep(1)
        pos = await channel.position.get()
        print(f"  Position: {pos:.2f} µm\n")
        
        # Test 3: Error Low-Pass Filter (for PID stability)
        print("[3] Configuring Error Low-Pass Filter...")
        print("  Purpose: Filter position error before PID controller")
        await channel.error_lpf.set(
            cutoff_frequency=200.0,  # 200 Hz
            order=2  # 2nd order filter
        )
        err_freq = await channel.error_lpf.get_cutoff_frequency()
        err_order = await channel.error_lpf.get_order()
        print(f"  ✓ Error LPF: Cutoff={err_freq:.1f} Hz, Order={err_order}\n")
        
        # Test position step with error filter
        print("  Testing with error filter enabled...")
        await channel.setpoint.set(30.0)
        await asyncio.sleep(1)
        pos = await channel.position.get()
        print(f"  Position: {pos:.2f} µm\n")
        
        # Test 4: Disable all filters and compare
        print("[4] Testing with all filters disabled...")
        await channel.notch.set(enabled=False)
        await channel.lpf.set(enabled=False)
        # Note: Error LPF typically stays enabled
        
        await channel.setpoint.set(50.0)
        await asyncio.sleep(1)
        pos = await channel.position.get()
        print(f"  Position: {pos:.2f} µm")
        print("  (Compare response stability with filters off)\n")
        
        # Check filter status from status register
        print("[5] Checking filter status from hardware...")
        status = await channel.status_register.get()
        print(f"  Notch filter active: {status.notch_filter_active}")
        print(f"  Low-pass filter active: {status.low_pass_filter_active}")
        
    finally:
        await device.close()
        print("\n✓ Disconnected")
    
    print("\n" + "=" * 60)
    print("Filter Tuning Tips:")
    print("- Notch: Set to mechanical resonance frequency")
    print("- LPF: Lower cutoff = smoother but slower response")
    print("- Error LPF: Helps PID stability, start with 200-500 Hz")
    print("- Test with small position steps to verify stability")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
