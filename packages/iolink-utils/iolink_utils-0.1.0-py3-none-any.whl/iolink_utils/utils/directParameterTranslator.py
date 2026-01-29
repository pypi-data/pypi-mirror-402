from typing import NamedTuple, Type, Callable, Dict
from enum import IntEnum
from functools import partial

from iolink_utils.exceptions import InvalidOctetValue

from iolink_utils.definitions.directParameterPage import DirectParameterPage1Index
from iolink_utils.definitions.masterCommand import MasterCommand
from iolink_utils.definitions.systemCommand import SystemCommand
from iolink_utils.octetDecoder.octetDecoder import (
    OctetDecoderBase,
    CycleTimeOctet,
    MSequenceCapability,
    RevisionId,
    ProcessDataIn,
    ProcessDataOut,
)
from iolink_utils.utils.cycleTime import CycleTime
from iolink_utils.definitions.transmissionDirection import TransmissionDirection


class Translation(NamedTuple):
    name: str = ''
    value: str = ''
    error: str = ''


def translateDirectParameter(index: int, value: int, direction: TransmissionDirection) -> Translation:
    try:
        dppIndex = DirectParameterPage1Index(index)
    except ValueError:
        return _translateUnknownIndex(index, value)

    handler = _HANDLER_PAGE1.get(dppIndex)
    if handler is None:  # pragma: no cover
        return _translateUnknownIndex(index, value)

    return handler(value, direction)


# -------- helpers --------

def _translateUnknownIndex(index: int, value: int) -> Translation:
    return Translation(name=f'DirectParameter {index}', value=f'0x{value:02X}', error=f'Index {index} unknown')


def _translateCycleTime(name: str, value: int):
    cto = CycleTimeOctet.from_buffer_copy(bytes([value]), 0)
    try:
        return Translation(name=name, value=f"{CycleTime.decodeToTimeInMs(cto)}ms")
    except InvalidOctetValue:
        return Translation(name=name, value=f'0x{value:02X}', error='Invalid cycle time')


def _translateOctet(octetDecoderClass: Type[OctetDecoderBase], value: int):
    octetDecoder = octetDecoderClass.from_buffer_copy(bytes([value]), 0)
    return Translation(name=octetDecoderClass.__name__, value=octetDecoder.valuesAsString())


def _translateCommand(commandEnum: Type[IntEnum], value: int, direction: TransmissionDirection):
    errors = []
    if direction == TransmissionDirection.Read:
        errors.append(f'Invalid direction (Read)')

    try:
        return Translation(name=commandEnum.__name__, value=commandEnum(value).name, error=', '.join(errors))
    except ValueError:
        errors.append(f'Unknown {commandEnum.__name__}')
        return Translation(name=commandEnum.__name__, value=f'0x{value:02X}', error=', '.join(errors))


def _handleMasterCommand(value: int, direction: TransmissionDirection):
    return _translateCommand(MasterCommand, value, direction)


def _handleMasterCycleTime(value: int, direction: TransmissionDirection):
    return _translateCycleTime("MasterCycleTime", value)


def _handleMinCycleTime(value: int, direction: TransmissionDirection):
    return _translateCycleTime("MinCycleTime", value)


def _handleMSeqCapability(value: int, direction: TransmissionDirection):
    return _translateOctet(MSequenceCapability, value)


def _handleRevisionId(value: int, direction: TransmissionDirection):
    return _translateOctet(RevisionId, value)


def _handlePDIn(value: int, direction: TransmissionDirection):
    return _translateOctet(ProcessDataIn, value)


def _handlePDOut(value: int, direction: TransmissionDirection):
    return _translateOctet(ProcessDataOut, value)


def _handleHexValue(label: str, value: int, direction: TransmissionDirection):
    return Translation(name=label, value=f'0x{value:02X}')


def _handleSystemCommand(value: int, direction: TransmissionDirection):
    return _translateCommand(SystemCommand, value, direction)


_Handler = Callable[[int, TransmissionDirection], Translation]

_HANDLER_PAGE1: Dict[DirectParameterPage1Index, _Handler] = {
    DirectParameterPage1Index.MasterCommand: _handleMasterCommand,
    DirectParameterPage1Index.MasterCycleTime: _handleMasterCycleTime,
    DirectParameterPage1Index.MinCycleTime: _handleMinCycleTime,
    DirectParameterPage1Index.MSequenceCapability: _handleMSeqCapability,
    DirectParameterPage1Index.RevisionId: _handleRevisionId,
    DirectParameterPage1Index.ProcessDataIn: _handlePDIn,
    DirectParameterPage1Index.ProcessDataOut: _handlePDOut,
    DirectParameterPage1Index.VendorId_MSB: partial(_handleHexValue, "VendorID_MSB"),
    DirectParameterPage1Index.VendorId_LSB: partial(_handleHexValue, "VendorID_LSB"),
    DirectParameterPage1Index.DeviceId_MSB: partial(_handleHexValue, "DeviceID_MSB"),
    DirectParameterPage1Index.DeviceId: partial(_handleHexValue, "DeviceID"),
    DirectParameterPage1Index.DeviceId_LSB: partial(_handleHexValue, "DeviceID_LSB"),
    DirectParameterPage1Index.FunctionId_MSB: partial(_handleHexValue, "FunctionID_MSB"),
    DirectParameterPage1Index.FunctionId_LSB: partial(_handleHexValue, "FunctionID_LSB"),
    DirectParameterPage1Index.SystemCommand: _handleSystemCommand,
}
