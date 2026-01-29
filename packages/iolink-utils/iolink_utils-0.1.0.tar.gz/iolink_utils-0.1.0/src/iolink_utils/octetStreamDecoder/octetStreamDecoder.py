from typing import Union, Optional
import copy
from datetime import datetime as dt, timedelta

from iolink_utils.definitions.timing import getMaxFrameTransmissionDelay_master, getMaxResponseTime, \
    getMaxFrameTransmissionDelay_device
from ._octetStreamDecoderInternal import DecodingState, MessageState, DeviceMessageDecoder, MasterMessageDecoder
from .octetStreamDecoderSettings import DecoderSettings
from .octetStreamDecoderMessages import DeviceMessage, MasterMessage


class OctetStreamDecoder:
    def __init__(self, settings: DecoderSettings):
        self._settings: DecoderSettings = copy.deepcopy(settings)

        self._state: DecodingState = DecodingState.Idle
        self._messageDecoder: Union[None, MasterMessageDecoder, DeviceMessageDecoder] = None
        self._lastMasterMessage: Optional[MasterMessage] = None
        self._lastDeviceMessage: Optional[DeviceMessage] = None

        self._lastProcessedOctetEndTime: dt = dt(1970, 1, 1)

        self._timingConstraints = {
            DecodingState.Idle: 0,
            DecodingState.MasterMessage: getMaxFrameTransmissionDelay_master(self._settings.transmissionRate),
            DecodingState.DeviceResponseDelay: getMaxResponseTime(self._settings.transmissionRate),
            DecodingState.DeviceMessage: getMaxFrameTransmissionDelay_device(self._settings.transmissionRate),
        }
        self._maxFrameTransmissionDelay: float = self._timingConstraints[DecodingState.Idle]

    @property
    def settings(self) -> DecoderSettings:
        return self._settings

    def setSettings(self, settings: DecoderSettings):
        self._settings = copy.deepcopy(settings)

    def _updateTimingConstraint(self, state: DecodingState):
        self._maxFrameTransmissionDelay = self._timingConstraints[state]

    def _isWithinTimingConstraints(self, octetStartTime: dt) -> bool:
        return (octetStartTime - self._lastProcessedOctetEndTime) < timedelta(
            microseconds=self._maxFrameTransmissionDelay)

    def _gotoState(self, state: DecodingState):
        self._state = state
        self._updateTimingConstraint(self._state)

    def reset(self):
        self._state: DecodingState = DecodingState.Idle

    def processOctet(self, octet, startTime: dt, endTime: dt) -> Union[None, MasterMessage, DeviceMessage]:
        if self._state == DecodingState.Idle or not self._isWithinTimingConstraints(startTime):
            self._messageDecoder = MasterMessageDecoder(self._settings)
            self._gotoState(DecodingState.MasterMessage)
            self._lastMasterMessage = None
            self._lastDeviceMessage = None
        self._lastProcessedOctetEndTime = endTime

        if self._state == DecodingState.MasterMessage:
            if self._messageDecoder.processOctet(octet, startTime, endTime) == MessageState.Finished:
                self._gotoState(DecodingState.DeviceResponseDelay)
                self._lastMasterMessage = self._messageDecoder.msg
                return self._lastMasterMessage

        if self._state == DecodingState.DeviceResponseDelay:
            self._lastMasterMessage: MasterMessage  # type hint
            self._messageDecoder = DeviceMessageDecoder(self._settings, self._lastMasterMessage.mc.read,
                                                        self._lastMasterMessage.ckt.mSeqType)
            self._gotoState(DecodingState.DeviceMessage)

        if self._state == DecodingState.DeviceMessage:
            if self._messageDecoder.processOctet(octet, startTime, endTime) == MessageState.Finished:
                self._gotoState(DecodingState.Idle)
                self._lastDeviceMessage = self._messageDecoder.msg
                return self._lastDeviceMessage

        return None
