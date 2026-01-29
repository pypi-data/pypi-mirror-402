class IOLinkUtilsException(Exception):
    """Basic exception for errors raised by iolink_utils"""


class IoddFileNotFound(IOLinkUtilsException):
    """Raised if IODD file does not exist"""


class InvalidIoddFile(IOLinkUtilsException):
    """Raised if IODD id not a valid IODD, e.g. could be a file containing only translations."""


class MSequenceCapabilityMissing(IOLinkUtilsException):
    """Raised if M-sequence capability is required, but not specified."""


class InvalidProcessDataSize(IOLinkUtilsException):
    """Raised if size of ProcessData is not as expected"""


class InvalidProcessDataDefinition(IOLinkUtilsException):
    """Raised if data format of ProcessData is not as expected/invalid"""


class InvalidMSeqCodePDSizeCombination(IOLinkUtilsException):
    """Raised if no on-request data size could be found for the provided combination of MSeqCode and ProcessData octet count"""


class InvalidMSeqCode(IOLinkUtilsException):
    """Raised if m-sequence code cannot be handled/is unknown"""


class InvalidCycleTime(IOLinkUtilsException):
    """Raised if cycle time cannot be converted to CycleTime octet"""


class InvalidOctetValue(IOLinkUtilsException):
    """Raised if an octet can not be initialized with the provided value"""


class InvalidOctetCount(IOLinkUtilsException):
    """Raised if the number of octets is invalid"""


class InvalidBitRate(IOLinkUtilsException):
    """Raised if bitrate is invalid / unsupported"""


class InvalidEventMemoryAddress(IOLinkUtilsException):
    """Raised if address of event memory byte is invalid"""


class InvalidEventStatusCode(IOLinkUtilsException):
    """Legacy event status code is not supported"""


class InvalidFlowControlValue(IOLinkUtilsException):
    """Raised if value is not a valid flow control value (Start, Idle, Count, ...)"""


class InvalidVersionStringFormat(IOLinkUtilsException):
    """Raised if format of version string is not supported"""


class EnumConversionError(IOLinkUtilsException):
    """Raised if a value cannot be converted into an enum value"""


class UnsupportedComplexDataType(IOLinkUtilsException):
    """Raised if an unsupported complex data type (IODD) was found"""


class UnsupportedSimpleDataType(IOLinkUtilsException):
    """Raised if an unsupported simple data type (IODD) was found"""


class InvalidISDUService(IOLinkUtilsException):
    """Raised if an invalid ISDU service was detected"""


class InvalidBitCount(IOLinkUtilsException):
    """Raised if the number of bits is not as expected"""


class UnexpectedMasterMessageReceived(IOLinkUtilsException):
    """Raised if an unexpected/invalid master message was received"""


class UnknownISDUError(IOLinkUtilsException):
    """Raised if an unknown ISDU error was detected"""


class ISDULengthUnknown(IOLinkUtilsException):
    """Raised if an unknown ISDU error was detected"""


class InvalidISDUMessage(IOLinkUtilsException):
    """Raised if an invalid (master/device) message was detected"""


class InvalidLengthInProcessDataParameter(IOLinkUtilsException):
    """Raised if value of length (ProcessDataIn / ProcessDataOut) is invalid"""
