from datetime import datetime as dt
from enum import IntEnum
from typing import Union

from iolink_utils.exceptions import UnexpectedMasterMessageReceived
from iolink_utils.octetStreamDecoder.octetStreamDecoderMessages import DeviceMessage, MasterMessage
from iolink_utils.definitions.transmissionDirection import TransmissionDirection
from iolink_utils.definitions.eventMemory import EventMemory

from .transactionDiagnosis import TransactionDiagEventMemory, TransactionDiagEventReset


class CommChannelDiagnosis:
    class State(IntEnum):
        Idle = 0,
        ReadEventMemory = 1,
        ResetEventFlag = 2

    def __init__(self):
        self._state: CommChannelDiagnosis.State = CommChannelDiagnosis.State.Idle

        self._startTime: dt = dt(1970, 1, 1)
        self._endTime: dt = dt(1970, 1, 1)

        self._eventMemory: EventMemory = EventMemory()
        self._eventMemoryIndex: int = 0

    def reset(self) -> None:
        self._state = CommChannelDiagnosis.State.Idle

    def handleMasterMessage(self, message: MasterMessage):
        self._eventMemoryIndex = message.mc.address

        if self._state == CommChannelDiagnosis.State.Idle:
            self._startTime = message.startTime
            direction = TransmissionDirection(message.mc.read)

            # read event memory
            if direction == TransmissionDirection.Read:
                self._eventMemory.clear()
                self._state = CommChannelDiagnosis.State.ReadEventMemory
            # reset event flag
            elif direction == TransmissionDirection.Write and self._eventMemoryIndex == 0:
                self._state = CommChannelDiagnosis.State.ResetEventFlag
            else:
                # we stay in idle -> device message will be discarded
                raise UnexpectedMasterMessageReceived(
                    f"Diagnosis: in Idle: {direction.name} address {self._eventMemoryIndex}")

    def handleDeviceMessage(self, message: DeviceMessage) \
            -> Union[None, TransactionDiagEventMemory, TransactionDiagEventReset]:

        if self._state == CommChannelDiagnosis.State.ReadEventMemory:
            self._endTime = message.endTime
            self._eventMemory.setMemory(self._eventMemoryIndex, message.od[0])

            if self._eventMemory.isComplete():
                self._state = CommChannelDiagnosis.State.Idle
                return TransactionDiagEventMemory(self._startTime, self._endTime, self._eventMemory)

        elif self._state == CommChannelDiagnosis.State.ResetEventFlag:
            self._endTime = message.endTime
            self._state = CommChannelDiagnosis.State.Idle
            return TransactionDiagEventReset(self._startTime, self._endTime)
        # else we didn't expect anything -> discard
