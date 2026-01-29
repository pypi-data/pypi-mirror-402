"""30DV device implementation (single-channel d-Drive family device)."""

from ..d_drive_family_device import DDriveFamilyDevice
from .psj_30dv_channel import PSJ30DVChannel


class PSJ30DVDevice(DDriveFamilyDevice):
    """Piezosystem Jena PSJ 30DV50/300 piezo amplifier device.
    
    The PSJ 30DV50/300 is a standalone, single-channel amplifier that is protocol
    compatible with the d-Drive family. It exposes one channel (ID 0) with
    the same capability set as a d-Drive channel.
    
    Attributes:
        DEVICE_ID: Device type identifier string
        D_DRIVE_IDENTIFIER: Internal identifier string used for discovery
    
    Example:
        >>> from psj_lib import PSJ30DVDevice, TransportType
        >>> device = PSJ30DVDevice(TransportType.SERIAL, 'COM3')
        >>> await device.connect()
        >>> channel = device.channels[0]
        >>> await channel.setpoint.set(10.0)
    """

    DEVICE_ID = "30DV50/300"
    """Device type identifier used for device discovery and type checking."""

    D_DRIVE_IDENTIFIER = "AP"
    """Internal identifier string used to recognize different d-Drive family devices."""

    async def _discover_channels(self):
        """Initialize the single channel for PSJ 30DV devices."""
        self._channels = {}
        self._channels[0] = PSJ30DVChannel(0, self._write_channel)
    
    async def _write_channel(self, channel_id, cmd, params=None):
        """Write a channel command without explicit channel ID.
        
        The PSJ 30DV uses the same command set as d-Drive, but does not require
        a channel index in the command frame. This override strips the channel
        ID from commands before delegating to the base implementation.
        """
        return await super()._write_channel(None, cmd, params)

    # Override to provide typed channels
    @property
    def channels(self) -> dict[int, PSJ30DVChannel]:
        """Typed channel mapping for PSJ 30DV (single channel at ID 0)."""
        return self._channels