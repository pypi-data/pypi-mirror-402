from enum import IntEnum
from typing import Optional, Callable
from datetime import datetime as dt

from iolink_utils.octetStreamDecoder.octetStreamDecoderMessages import (
    DeviceMessage,
    MasterMessage,
)
from iolink_utils.exceptions import InvalidISDUMessage
from iolink_utils.octetDecoder.octetDecoder import IService
from iolink_utils.definitions.transmissionDirection import TransmissionDirection
from iolink_utils.definitions.iServiceNibble import IServiceNibble
from iolink_utils.messageInterpreter.isdu.ISDUflowControl import FlowControl
from iolink_utils.messageInterpreter.isdu.ISDU import ISDU
from iolink_utils.messageInterpreter.isdu.ISDUrequests import createISDURequest
from iolink_utils.messageInterpreter.isdu.ISDUresponses import createISDUResponse


class CommChannelISDU:
    class State(IntEnum):
        Idle = 0
        Request = 1
        RequestFinished = 2
        WaitForResponse = 3
        Response = 4

    def __init__(self) -> None:
        self._state: CommChannelISDU.State = CommChannelISDU.State.Idle
        self._direction: TransmissionDirection = TransmissionDirection.Read
        self._flowControl: FlowControl = FlowControl()
        self._previousFlowControl: FlowControl = FlowControl()

        self._isduRequest: Optional[ISDU] = None
        self._isduResponse: Optional[ISDU] = None
        self._responseStartTime: Optional[dt] = None

    def reset(self) -> None:
        self._state = CommChannelISDU.State.Idle
        self._flowControl = FlowControl()
        self._previousFlowControl = FlowControl()

    def handleMasterMessage(self, message: MasterMessage) -> None:
        self._direction = TransmissionDirection(message.mc.read)
        flowControl = FlowControl(message.mc.address)

        if flowControl.state == FlowControl.State.Abort:
            self.reset()
            return

        MasterHandler = Callable[[MasterMessage, FlowControl], None]
        handler: Optional[MasterHandler] = {
            self.State.Idle: self.handleMasterMsgInStateIdle,
            self.State.Request: self.handleMasterMsgInStateRequest,
            self.State.WaitForResponse: self.handleMasterMsgInStateWaitForResponse,
        }.get(self._state)

        if handler:
            handler(message, flowControl)

        self._flowControl = flowControl

    def handleDeviceMessage(self, message: DeviceMessage) -> Optional[ISDU]:
        DeviceHandler = Callable[[DeviceMessage], Optional[ISDU]]
        handler: Optional[DeviceHandler] = {
            self.State.RequestFinished: self.handleDeviceMsgInStateRequestFinished,
            self.State.WaitForResponse: self.handleDeviceMsgInStateWaitForResponse,
            self.State.Response: self.handleDeviceMsgInStateResponse,
        }.get(self._state)

        if handler:
            isdu = handler(message)
            self._previousFlowControl = self._flowControl.copy()
            return isdu

        return None

    #
    # MasterMessage state handler
    #
    def handleMasterMsgInStateIdle(self, message: MasterMessage, flow: FlowControl) -> None:
        if flow.state != FlowControl.State.Start:
            return

        if self._direction != TransmissionDirection.Write:
            return

        self.raiseIfOnRequestDataIsMissing(message)

        self._isduRequest = createISDURequest(self.getService(message))
        self._isduRequest.setTime(message.startTime, message.endTime)
        self._isduRequest.appendOctets(message.od)

        self._state = (
            self.State.RequestFinished
            if self._isduRequest.isComplete
            else self.State.Request
        )

    def handleMasterMsgInStateRequest(self, message: MasterMessage, flow: FlowControl) -> None:
        if flow.state != FlowControl.State.Count:
            return

        if self._direction == TransmissionDirection.Write:
            self.raiseIfOnRequestDataIsMissing(message)

        if not self.appendOnRequestData(self._isduRequest, flow, self._flowControl, message.od):
            self.reset()
            return

        if self._isduRequest.isComplete:
            self._isduRequest.setEndTime(message.endTime)
            self._state = self.State.RequestFinished

    def handleMasterMsgInStateWaitForResponse(self, message: MasterMessage, flow: FlowControl) -> None:
        if flow.state != FlowControl.State.Start:
            return
        if self._direction != TransmissionDirection.Read:
            return

        self._responseStartTime = message.startTime

    #
    # DeviceMessage state handler
    #

    def handleDeviceMsgInStateRequestFinished(self, message: DeviceMessage) -> Optional[ISDU]:
        self._isduRequest.setEndTime(message.endTime)
        self._state = self.State.WaitForResponse
        return self._isduRequest

    def handleDeviceMsgInStateWaitForResponse(self, message: DeviceMessage) -> Optional[ISDU]:
        if self._flowControl.state != FlowControl.State.Start:
            return None
        if self._direction != TransmissionDirection.Read:
            return None

        self.raiseIfOnRequestDataIsMissing(message)

        service = self.getService(message)
        if service.service == IServiceNibble.NoService:
            return None

        self._isduResponse = createISDUResponse(service)
        self._isduResponse.setTime(self._responseStartTime, message.endTime)
        self._isduResponse.appendOctets(message.od)

        if self._isduResponse.isComplete:
            self._state = self.State.Idle
            return self._isduResponse

        self._state = self.State.Response
        return None

    def handleDeviceMsgInStateResponse(self, message: DeviceMessage) -> Optional[ISDU]:
        if self._flowControl.state != FlowControl.State.Count:
            return None

        self.raiseIfOnRequestDataIsMissing(message)

        if not self.appendOnRequestData(self._isduResponse, self._flowControl, self._previousFlowControl, message.od):
            self.reset()
            return None

        if self._isduResponse.isComplete:
            self._isduResponse.setEndTime(message.endTime)
            self._state = self.State.Idle
            return self._isduResponse

        return None

    #
    # helpers
    #
    @staticmethod
    def raiseIfOnRequestDataIsMissing(message) -> None:
        if not message.od:
            raise InvalidISDUMessage("OnRequest data missing")

    @staticmethod
    def getService(message) -> IService:
        return IService(message.od[0])

    @staticmethod
    def appendOnRequestData(isdu: ISDU, current: FlowControl, previous: FlowControl, od: bytearray) -> bool:
        if current.value == previous.value:
            isdu.replaceTrailingOctets(od)
        elif current.value == previous.nextCountValue():
            isdu.appendOctets(od)
        else:
            return False
        return True
