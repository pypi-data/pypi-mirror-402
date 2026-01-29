from typing import Union
from dataclasses import dataclass, field

from iolink_utils.exceptions import InvalidMSeqCode
from iolink_utils.definitions.bitRate import BitRate
from iolink_utils.definitions.mSequenceType import MSeqType
from iolink_utils.iodd.iodd import Iodd


@dataclass(frozen=True)
class MSeqPayloadLength:
    pdOut: int = 0
    od: int = 0
    pdIn: int = 0


@dataclass
class DecoderSettings:
    transmissionRate: BitRate = field(default_factory=lambda: BitRate('Undefined'))
    startup: MSeqPayloadLength = field(default_factory=MSeqPayloadLength)
    preoperate: MSeqPayloadLength = field(default_factory=MSeqPayloadLength)
    operate: MSeqPayloadLength = field(default_factory=MSeqPayloadLength)

    def getPayloadLength(self, mSeqType: Union[int, MSeqType]) -> MSeqPayloadLength:
        try:
            mst = MSeqType(mSeqType)
        except ValueError:
            raise InvalidMSeqCode(f"Invalid M-Sequence type: '{mSeqType}'") from None

        return {
            MSeqType.Type_0_STARTUP: self.startup,
            MSeqType.Type_1_PREOPERATE: self.preoperate,
            MSeqType.Type_2_OPERATE: self.operate,
        }[mst]

    @staticmethod
    def fromIODD(iodd: Iodd) -> "DecoderSettings":
        return DecoderSettings(
            transmissionRate=iodd.physicalLayer.bitrate,
            startup=MSeqPayloadLength(pdOut=0, od=1, pdIn=0),
            preoperate=MSeqPayloadLength(
                pdOut=0,
                od=iodd.size_OnRequestData[0],
                pdIn=0,
            ),
            operate=MSeqPayloadLength(
                pdOut=iodd.size_PDout,
                od=iodd.size_OnRequestData[1],
                pdIn=iodd.size_PDin,
            ),
        )
