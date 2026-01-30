"""
ZLBus API Modules Package

This package contains all the ZLBus API modules.
"""

from .zlbusConfig import *
from .zlbusBaseType import *
from .zlbusApiType import *
from .zlbusError import *
from .zlbusStackConfig import (
    DEFAULT_RF_DISCONN,
    DEFAULT_RFID,
    DEFAULT_DOTID,
    DEFAULT_DONGLEID,
    e_ERROR_CMU,
)
from .zlbusApi_eBlockId import *

__all__ = [
    #-------------------------
    'zlbusConfig', 
    'zlbusBaseType', 
    'zlbusApiType', 
    'zlbusError', 
    'zlbusStackConfig',
    'zlbusApi_eBlockId', 
    #-------------------------
    # e_BlockID
    "e_BlockID",
    "e_BlockID_DataExport",
    "e_BlockID_UL",
    "e_BlockID_UHL",
    "e_BlockID_UDG",
    "e_BlockID_FDG",

    # zlbusBaseType
    "Axis3_I16",
    "Axis3_Float",
    "AhrsQuaternion",
    "AhrsEuler",
    "AntValue_I16",
    "Axis3_ScaleDpsBlock",

    # zlbusApiType | 基础
    "xxxIdBlock",
    "e_Upload_DataFormat",
    "ul_ImuDataBlock",
    "ul_DeviceStateBlock",
    "ul_BatteryBlock",
    "ul_AntValueBlock",
    "ul_CtrlDataBaseBlock",
    "ul_UploadDataFormatBlock",
    "e_SampleHz",
    "ul_SamplingHzBlock",
    "e_UploadHz",
    "ul_UploadHzBlock",
    "e_FiterParam",
    "ul_FilterMapBlock",
    "e_Convention",
    "ul_IcDirBlock",
    "ul_DevieRfNameBlock",
    "ul_RfPowerBlock",
    "e_LedColor",
    "e_LedMode",
    "ul_RgbDataBlock",
    "e_BaudRate",
    "ul_UartBaudRateBlock",
    "ul_BlockSizeBlock",
    "ul_DeviceMacBlock",
    "ul_DeviceSnFullStrBlock",
    "ul_DeviceBoardVersionBlock",
    "ul_DeviceFirmwareVersionBlock",

    # zlbusApiType | 高级 | UHL
    "hl_UploadDataFormatBlock",
    "hl_DotIdBlock",
    "hl_BleConnIntervalBlock",
    "e_AccRange",
    "hl_AccRangeBlock",
    "e_GyroRange",
    "hl_GyroRangeBlock",
    "MagEllipsoidCalParamBlock_t",
    "hl_MagEllipsoidCalParamBlock",
    "e_TK_FlowIdFormat",
    "hl_FlowIdFormatBlock",
    "hl_AhrsOffsetBlock",
    "e_DataOutPort",
    "hl_DataPortBlock",
    "hl_DataPortMapBlock",
    "hl_DeviceStateBlock",
    "AntFilterParam_t",
    "hl_AntFilterParamBlock",
    "hl_FingerMapBlock",
    "e_AntEn",
    "e_BlockSizeType",

    # zlbusApiType | Dongle | UDG
    "DeviceBlock_t",
    "DL_DongleSnFullStrBlock",
    "DL_DeviceBoardVersionBlock",
    "DL_DeviceFirmwareVersionBlock",
    "DL_DeviceListBlock",
    "DL_DeviceConnNumsBlock",
    "DL_IdentifyWayBlock",
    "DL_ScanBlock",
    "DL_TimeStampSyncBlock",

    # zlbusError
    'TKxx_SUCCESS',
    'TKxx_ERR_FAILED',
    'TKxx_ERR_READY',
    'TKxx_ERR_MEM',
    'TKxx_ERR_MAX_SIZE',
    'TKxx_ERR_INTERN',
    'TKxx_ERR_BUSY',
    'TKxx_ERR_ALREADY',
    'TKxx_ERR_VAL',
    'TKxx_ERR_NULL',
    'TKxx_ERR_TIMEOUT',
    'TKxx_ERR_NONE',

    # zlbusStackConfig
    "DEFAULT_RF_DISCONN",
    "DEFAULT_RFID",
    "DEFAULT_DOTID",
    "DEFAULT_DONGLEID",
    "e_ERROR_CMU",
]