from typing import Optional
from iolink_utils.definitions.bitRate import BitRate
from iolink_utils.octetDecoder.octetDecoder import MSequenceCapability


class PhysicalLayer:
    def __init__(self):
        self.bitrate: BitRate = BitRate.Undefined
        self.minCycleTime = 0
        self.sioSupported = False
        self.mSequenceCapability: Optional[MSequenceCapability] = None

    def __str__(self):  # pragma: no cover
        return (
            f"PhysicalLayer("
            f"bitrate={self.bitrate.name} ({self.bitrate.value}), "
            f"minCycleTime={self.minCycleTime}, "
            f"sioSupported={self.sioSupported}, "
            f"mSequenceCapability={self.mSequenceCapability})"
        )
