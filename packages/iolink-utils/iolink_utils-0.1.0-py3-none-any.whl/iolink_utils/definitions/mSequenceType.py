from enum import IntEnum


# See Table A.3 – Values of M-sequence types
class MSeqType(IntEnum):
    Type_0_STARTUP = 0
    Type_1_PREOPERATE = 1
    Type_2_OPERATE = 2
