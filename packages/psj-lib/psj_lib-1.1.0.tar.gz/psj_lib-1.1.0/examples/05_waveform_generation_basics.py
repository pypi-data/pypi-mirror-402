"""Example 5: Waveform Generation Basics

This example demonstrates how to:
- Generate different waveform types (sine, triangle, sweep)
- Configure waveform parameters
- Switch between waveforms
- Monitor waveform status

The d-Drive includes a built-in waveform generator for scanning applications.
"""

import asyncio
from psj_lib import DDriveDevice, TransportType, DDriveWaveformType


async def main():
    print("=" * 60)
    print("d-Drive Waveform Generation Example")
    print("=" * 60)
    
    # Connect to device
    device = DDriveDevice(TransportType.SERIAL, 'COM1')
    await device.connect()
    print(f"✓ Connected to device\n")
    
    channel = device.channels[0]
    wfg = channel.waveform_generator
    
    try:
        # Ensure closed-loop is enabled
        await channel.closed_loop_controller.set(True)
        
        # Test 1: Sine wave
        print("[1] Generating Sine Wave...")
        await wfg.sine.set(
            amplitude=20.0,  # 20 µm amplitude
            offset=20.0,     # Centered at 20 µm
            frequency=5.0    # 5 Hz
        )
        await wfg.set_waveform_type(DDriveWaveformType.SINE)
        print("  ✓ Sine: 20µm amplitude, 20µm offset, 5Hz")
        
        # Let it run briefly
        await asyncio.sleep(20)
        
        # Test 2: Triangle wave
        print("[2] Generating Triangle Wave...")
        await wfg.triangle.set(
            amplitude=30.0,
            offset=20.0,
            frequency=2.0,
            duty_cycle=50.0  # Symmetric triangle
        )
        await wfg.set_waveform_type(DDriveWaveformType.TRIANGLE)
        print("  ✓ Triangle: 30µm amplitude, 20µm offset, 2Hz, 50% duty")
        
        await asyncio.sleep(2)
        
        # Test 3: Sweep (ramp)
        print("[3] Generating Sweep...")
        await wfg.sweep.set(
            amplitude=40.0,
            offset=30.0,
            frequency=3.0  # Actually sweep time in seconds
        )
        await wfg.set_waveform_type(DDriveWaveformType.SWEEP)
        print("  ✓ Sweep: 40µm range, 30µm start, 3s duration")
        
        await asyncio.sleep(3.5)
        
        # Stop waveform generation
        print("\n[4] Stopping waveform generation...")
        await wfg.set_waveform_type(DDriveWaveformType.NONE)
        print("  ✓ Waveform stopped")
        
        # Return to fixed position
        await channel.setpoint.set(50.0)
        print("  ✓ Returned to 50µm")
        
    finally:
        await device.close()
        print("\n✓ Disconnected")
    
    print("\n" + "=" * 60)
    print("D-Drive Waveform Types Available:")
    print("- SINE: Smooth periodic motion")
    print("- TRIANGLE: Linear ramps with adjustable duty cycle")
    print("- RECTANGLE: Square wave positioning")
    print("- NOISE: Random dithering")
    print("- SWEEP: Single linear ramp")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
