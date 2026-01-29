"""Example 13: Backup and Restore Configuration

This example demonstrates how to:
- Backup current device/channel configuration
- Modify settings for an experiment
- Restore original configuration
- Save/load configuration to/from files

Configuration management is useful for reproducible experiments and quick setting changes.
"""
import logging
import asyncio
import json
from psj_lib import DDriveDevice, TransportType

logging.basicConfig(level=logging.DEBUG)

async def main():
    print("=" * 60)
    print("d-Drive Backup and Restore Configuration Example")
    print("=" * 60)
    
    # Connect to device
    device = DDriveDevice(TransportType.SERIAL, 'COM1')
    await device.connect()
    print(f"✓ Connected to device\n")
    
    channel = device.channels[0]
    
    try:
        # Enable closed-loop control
        await channel.closed_loop_controller.set(True)
        
        # Step 1: Read and display current configuration
        print("[1] Current Configuration:")
        p = await channel.pid_controller.get_p()
        i = await channel.pid_controller.get_i()
        d = await channel.pid_controller.get_d()
        sr = await channel.slew_rate.get()
        notch_enabled = await channel.notch.get_enabled()
        print(f"  PID: P={p:.2f}, I={i:.2f}, D={d:.2f}")
        print(f"  Slew Rate: {sr:.2f} V/ms")
        print(f"  Notch Filter: {'Enabled' if notch_enabled else 'Disabled'}\n")
        
        # Step 2: Backup current configuration
        print("[2] Backing up configuration...")
        backup = await device.backup()
        print(f"  ✓ Backed up {len(backup)} settings")
        
        # Optionally save backup to file
        backup_file = "ddrive_config_backup.json"
        with open(backup_file, 'w') as f:
            json.dump(backup, f, indent=2)
        print(f"  ✓ Saved backup to {backup_file}\n")
        
        # Step 3: Modify settings for an experiment
        print("[3] Modifying settings for experiment...")
        await channel.pid_controller.set(p=0, i=0, d=0)
        await channel.slew_rate.set(5.0)
        await channel.notch.set(enabled=True, frequency=500.0, bandwidth=50.0)
        print("  ✓ Applied experimental settings:")
        print("    PID: P=0, I=0, D=0")
        print("    Slew Rate: 5.0 V/ms")
        print("    Notch Filter: Enabled at 500 Hz\n")
        
        # Verify changes
        p_new = await channel.pid_controller.get_p()
        i_new = await channel.pid_controller.get_i()
        print(f"  Verified: P={p_new:.2f}, I={i_new:.2f}\n")
        
        # Step 4: Simulate experiment
        print("[4] Running simulated experiment...")
        await channel.setpoint.set(40.0)
        await asyncio.sleep(0.5)
        await channel.setpoint.set(60.0)
        await asyncio.sleep(0.5)
        print("  ✓ Experiment complete\n")
        
        # Step 5: Restore original configuration
        print("[5] Restoring original configuration...")
        await device.restore(backup)
        print("  ✓ Configuration restored")
        
        # Verify restoration
        p_restored = await channel.pid_controller.get_p()
        i_restored = await channel.pid_controller.get_i()
        sr_restored = await channel.slew_rate.get()
        notch_restored = await channel.notch.get_enabled()
        print(f"  Restored: PID P={p_restored:.2f}, I={i_restored:.2f}")
        print(f"  Restored: Slew Rate={sr_restored:.2f} V/ms")
        print(f"  Restored: Notch Filter={'Enabled' if notch_restored else 'Disabled'}\n")
        
        # Step 6: Demonstrate loading from file
        print("[6] Loading configuration from file...")
        with open(backup_file, 'r') as f:
            loaded_config = json.load(f)
        await device.restore(loaded_config)
        print(f"  ✓ Loaded and applied configuration from {backup_file}")
        
    finally:
        await device.close()
        print("\n✓ Disconnected")
    
    print("\n" + "=" * 60)
    print("Configuration Management Tips:")
    print("- Backup before experiments to ensure reproducibility")
    print("- Save backups to files for different use cases")
    print("- Use meaningful filenames (e.g., 'scanning_config.json')")
    print("- Backup includes PID, filters, waveforms, triggers, etc.")
    print("- Dynamic values (position, setpoint) are NOT backed up")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
