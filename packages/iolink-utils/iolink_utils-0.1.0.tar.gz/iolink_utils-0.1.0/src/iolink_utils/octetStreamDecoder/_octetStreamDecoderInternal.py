from enum import IntEnum
from datetime import datetime as dt

from iolink_utils.octetDecoder.octetDecoder import MC, CKT, CKS
from .octetStreamDecoderSettings import DecoderSettings
from .octetStreamDecoderMessages import MasterMessage, DeviceMessage
from ._compressChecksum import lookup_8to6_compression


class MessageState(IntEnum):
    Incomplete = 0,
    Finished = 1


class DecodingState(IntEnum):
    Idle = 0,
    MasterMessage = 1,
    DeviceResponseDelay = 2,
    DeviceMessage = 3


class MasterMessageDecoder:
    def __init__(self, settings: DecoderSettings):
        self._settings: DecoderSettings = settings
        self._octetCount: int = 0
        self._pdOutLen: int = 0
        self._odLen: int = 0

        self._msg: MasterMessage = MasterMessage()

    @property
    def msg(self):
        return self._msg

    def processOctet(self, octet, startTime: dt, endTime: dt) -> MessageState:
        if not self._isComplete():
            if self._octetCount == 0:
                self._msg.startTime = startTime
                self._msg.mc = MC.from_buffer_copy(bytes([octet]), 0)
            elif self._octetCount == 1:
                self._msg.ckt = CKT.from_buffer_copy(bytes([octet]), 0)

                payloadLength = self._settings.getPayloadLength(self._msg.ckt.mSeqType)
                self._pdOutLen = payloadLength.pdOut
                self._odLen = payloadLength.od if self._msg.mc.read == 0 else 0
            elif len(self._msg.pdOut) < self._pdOutLen:
                self._msg.pdOut.append(octet)
            elif len(self._msg.od) < self._odLen:
                self._msg.od.append(octet)

            self._octetCount += 1
            self._msg.endTime = endTime

        if self._isComplete():
            self._msg.isValid = (self._msg.ckt.checksum == self._calculateChecksum())
            return MessageState.Finished
        else:
            return MessageState.Incomplete

    def _calculateChecksum(self):
        checksum = 0x52
        checksum ^= self._msg.mc.get()
        checksum ^= self._msg.ckt.getWithoutChecksum()
        for b in self._msg.pdOut:
            checksum ^= b
        for b in self._msg.od:
            checksum ^= b
        return lookup_8to6_compression[checksum]

    def _isComplete(self):
        return ((self._octetCount >= 2) and
                len(self._msg.pdOut) == self._pdOutLen and
                len(self._msg.od) == self._odLen)


class DeviceMessageDecoder:
    def __init__(self, settings: DecoderSettings, read: int, mSeqType: int):
        self._settings: DecoderSettings = settings
        self._octetCount: int = 0

        self._msg: DeviceMessage = DeviceMessage()

        payloadLength = self._settings.getPayloadLength(mSeqType)
        self._odLen: int = payloadLength.od if read == 1 else 0
        self._pdInLen: int = payloadLength.pdIn

    @property
    def msg(self):
        return self._msg

    def processOctet(self, octet, start_time: dt, end_time: dt) -> MessageState:
        if not self._isComplete():
            if self._octetCount == 0:
                self._msg.startTime = start_time

            if len(self._msg.od) < self._odLen:
                self._msg.od.append(octet)
            elif len(self._msg.pdIn) < self._pdInLen:
                self._msg.pdIn.append(octet)
            else:
                self._msg.cks = CKS.from_buffer_copy(bytes([octet]), 0)

            self._octetCount += 1
            self._msg.endTime = end_time

        if self._isComplete():
            self._msg.isValid = (self._msg.cks.checksum == self._calculateChecksum())
            return MessageState.Finished
        else:
            return MessageState.Incomplete

    def _calculateChecksum(self):
        checksum = 0x52
        for b in self._msg.od:
            checksum ^= b
        for b in self._msg.pdIn:
            checksum ^= b
        checksum ^= self._msg.cks.getWithoutChecksum()
        return lookup_8to6_compression[checksum]

    def _isComplete(self):
        return (self._octetCount == (self._pdInLen + self._odLen + 1) and
                len(self._msg.pdIn) == self._pdInLen and
                len(self._msg.od) == self._odLen)
