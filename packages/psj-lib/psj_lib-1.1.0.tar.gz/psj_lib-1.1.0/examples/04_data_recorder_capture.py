"""Example 6: Data Recorder Capture

This example demonstrates how to:
- Configure the two-channel data recorder
- Capture position and voltage simultaneously
- Save recorded data to CSV file
- Optionally plot data with matplotlib

The d-Drive data recorder can capture up to 500k samples per channel at 50 kHz.
"""

import asyncio
import csv
from psj_lib import DDriveDevice, TransportType, DataRecorderChannel, DDriveDataRecorderChannel


async def main():
    print("=" * 60)
    print("d-Drive Data Recorder Example")
    print("=" * 60)
    
    # Connect to device
    device = DDriveDevice(TransportType.SERIAL, 'COM1')
    await device.connect()
    print(f"✓ Connected to device\n")
    
    channel = device.channels[0]
    
    try:
        # Enable closed-loop control
        await channel.closed_loop_controller.set(True)
        
        # Configure data recorder
        print("[1] Configuring data recorder...")
        sample_rate = 10000  # 10 kHz
        duration_sec = 0.1
        num_samples = int(sample_rate * duration_sec)
        
        await channel.data_recorder.set(
            memory_length=num_samples,  # 1k samples = 0.1 seconds
            stride=channel.data_recorder.sample_rate // sample_rate
        )
        print(f"  ✓ Configured: {num_samples} samples at {sample_rate} Hz")
        print(f"  Duration: {duration_sec} seconds\n")
        
        # Perform a position step to capture transient response
        # This will trigger the data recorder automatically
        # Alternatively, you could start it manually with start()
        print("\n[2] Performing position step (30µm → 70µm)...")
        await channel.setpoint.set(30.0)
        await asyncio.sleep(1)
        await channel.setpoint.set(70.0)
        await asyncio.sleep(1)
        print("  ✓ Motion complete")
        
        # Retrieve recorded data
        def progress_cb(current: int, total: int) -> None:
            percent = (current / total) * 100

            # Only print every 10%
            if current % (total // 10) == 0 or current == total:
                print(f"\r    Retrieving data... {percent:.1f}%", end='', flush=True)


        print("\n[3] Retrieving recorded data...")
        print("    Retrieving position data...")
        position_data = await channel.data_recorder.get_all_data(
            DDriveDataRecorderChannel.POSITION,
            num_samples,
            progress_cb
        )
        print("\n    Retrieving voltage data...")
        voltage_data = await channel.data_recorder.get_all_data(
            DDriveDataRecorderChannel.VOLTAGE,
            num_samples,
            progress_cb
        )
        print(f"  ✓ Retrieved {len(position_data)} position samples")
        print(f"  ✓ Retrieved {len(voltage_data)} voltage samples")
        
        # Save to CSV file
        print("\n[4] Saving data to CSV...")
        filename = "recorder_data.csv"

        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Time (s)', 'Position (%)', 'Voltage (V)'])

            for i in range(len(position_data)):
                time = i / sample_rate
                writer.writerow([f"{time:.6f}", f"{position_data[i]:.3f}", f"{voltage_data[i]:.3f}"])
        
        print(f"  ✓ Saved to {filename}")
        
        # Display statistics
        print("\n[5] Data Statistics:")
        print(f"  Position: min={min(position_data):.2f}, "
              f"max={max(position_data):.2f}, "
              f"avg={sum(position_data)/len(position_data):.2f} %")
        print(f"  Voltage:  min={min(voltage_data):.2f}, "
              f"max={max(voltage_data):.2f}, "
              f"avg={sum(voltage_data)/len(voltage_data):.2f} V")
        
        # Optional: Plot if matplotlib is available
        try:
            import matplotlib.pyplot as plt
            
            print("\n[6] Generating plot...")
            time_axis = [i / sample_rate for i in range(len(position_data))]
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))
            
            ax1.plot(time_axis, position_data, 'b-', linewidth=0.5)
            ax1.set_ylabel('Position (%)')
            ax1.set_title('d-Drive Data Recorder Capture')
            ax1.grid(True)
            
            ax2.plot(time_axis, voltage_data, 'r-', linewidth=0.5)
            ax2.set_xlabel('Time (s)')
            ax2.set_ylabel('Voltage (V)')
            ax2.grid(True)
            
            plt.tight_layout()
            plt.savefig('recorder_data.png')
            print("  ✓ Plot saved to recorder_data.png")
            # plt.show()  # Uncomment to display plot
            
        except ImportError:
            print("\n[6] Matplotlib not available (skipping plot)")
        
    finally:
        await device.close()
        print("\n✓ Disconnected")
    
    print("\n" + "=" * 60)
    print("Data recorder tips:")
    print("- Maximum 500,000 samples per channel")
    print("- Both channels record simultaneously")
    print("- Use stride to reduce sample rate for longer captures")
    print("- Recording auto-starts on position changes")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
