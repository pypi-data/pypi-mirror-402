"""PSJ 30DV channel implementation (single-channel d-Drive family)."""

from ..d_drive_family_channel import DDriveFamilyChannel


class PSJ30DVChannel(DDriveFamilyChannel):
    """Channel class for PSJ 30DV devices.
    
    Inherits all d-Drive family capabilities and behavior. The PSJ 30DV exposes
    a single channel (ID 0) with the same capability set as d-Drive channels.
    """

    pass