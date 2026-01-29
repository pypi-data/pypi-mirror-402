from typing import Union

from iolink_utils.octetDecoder.octetDecoder import ProcessDataIn, ProcessDataOut
from iolink_utils.exceptions import InvalidLengthInProcessDataParameter


def calculateProcessDataLength(octet: Union[ProcessDataIn, ProcessDataOut]) -> int:
    """Calculate size of ProcessData (in bytes) from ProcessDataIn/Out octet

    See B.1.6 ProcessDataIn and B.1.7 ProcessDataOut

    :param octet: ProcessDataIn or ProcessDataOut (read from direct parameter page 1 for example)
    :return: size of process data in bytes
    """

    # See Table B.6 – Permitted combinations of BYTE and Length
    if octet.byte == 0:  # bits
        minLength, maxLength = 0, 16
        if minLength <= octet.length <= maxLength:
            return (octet.length + 7) // 8
    else:  # octets
        minLength, maxLength = 2, 31
        if minLength <= octet.length <= maxLength:
            return octet.length + 1

    octetName = octet.__class__.__name__
    raise InvalidLengthInProcessDataParameter(
        f"Invalid length in {octetName}: {octet.length} (allowed {minLength} - {maxLength})"
    )
