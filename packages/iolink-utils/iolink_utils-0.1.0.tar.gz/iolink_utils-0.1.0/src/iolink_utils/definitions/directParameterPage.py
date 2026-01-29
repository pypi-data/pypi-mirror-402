from enum import IntEnum


# See Table B.1 – Direct Parameter page 1 and 2
class DirectParameterPage1Index(IntEnum):
    MasterCommand = 0,
    MasterCycleTime = 1,
    MinCycleTime = 2,
    MSequenceCapability = 3,
    RevisionId = 4,
    ProcessDataIn = 5,
    ProcessDataOut = 6,
    VendorId_MSB = 7,
    VendorId_LSB = 8,
    DeviceId_MSB = 9,
    DeviceId = 10,
    DeviceId_LSB = 11,
    FunctionId_MSB = 12,
    FunctionId_LSB = 13,
    Reserved = 14,
    SystemCommand = 15
