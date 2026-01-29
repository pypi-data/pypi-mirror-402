from enum import IntEnum


# See Table B.9 – Coding of SystemCommand
# See IOL CommonProfile: Table B.2 – Conditional SystemCommand
# See Firmware Update Profile: Table 14 – Coding of FW-Update SystemCommands
class SystemCommand(IntEnum):
    ParamUploadStart = 0x01
    ParamUploadEnd = 0x02
    ParamDownloadStart = 0x03
    ParamDownloadEnd = 0x04
    ParamDownloadStore = 0x05
    ParamBreak = 0x06
    BM_UNLOCK_S = 0x50
    BM_UNLOCK_F = 0x51
    BM_UNLOCK_T = 0x52
    BM_ACTIVATE = 0x53
    LocatorStart = 0x7E
    LocatorStop = 0x7F
    DeviceReset = 0x80
    ApplicationReset = 0x81
    RestoreFactorySettings = 0x82
    BackToBox = 0x83
