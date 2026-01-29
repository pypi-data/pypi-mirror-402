from enum import IntEnum


# See Table A.12 – Definition of the nibble "I-Service"
class IServiceNibble(IntEnum):
    NoService = 0b0000,
    M_WriteReq_8bitIdx = 0b0001,
    M_WriteReq_8bitIdxSub = 0b0010,
    M_WriteReq_16bitIdxSub = 0b0011,
    D_WriteResp_M = 0b0100,
    D_WriteResp_P = 0b0101,
    M_ReadReq_8bitIdx = 0b1001,
    M_ReadReq_8bitIdxSub = 0b1010,
    M_ReadReq_16bitIdxSub = 0b1011,
    D_ReadResp_M = 0b1100,
    D_ReadResp_P = 0b1101
