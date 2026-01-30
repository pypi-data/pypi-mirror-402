# -*- coding: utf-8 -*-
"""
BlockID 枚举全集（与 C 代码 1:1 对应）
"""

from enum import IntEnum

from .zlbusConfig import *

# -------------------- 统一 BlockID 枚举 --------------------
class e_BlockID(IntEnum):
    """顶层通用 BlockID"""
    BlockID_OK       = 0x00110000  # /* ul_CtrlDataBaseBlock */
    BlockID_ERROR    = 0x00FF0000  # /* ul_CtrlDataBaseBlock */

# -------------------- 数据导出 BlockID --------------------
class e_BlockID_DataExport(IntEnum):
    BlockID_00001000 = 0x00001000  # /* ul_ImuDataBlock           */
    BlockID_00001100 = 0x00001100  # /* ul_DeviceStateBlock       */
    BlockID_00001400 = 0x00001400  # /* ul_BatteryBlock           */
    BlockID_00001500 = 0x00001500  # /* ul_AntValueBlock          */

# -------------------- 普通上传指令 BlockID --------------------
class e_BlockID_UL(IntEnum):
    BlockID_0000D501 = 0x0000D501  # /* ul_UploadDataFormatBlock      */
    BlockID_0000D503 = 0x0000D503  # /* ul_SamplingHzBlock            */
    BlockID_0000D505 = 0x0000D505  # /* ul_UploadHzBlock              */
    BlockID_0000D50B = 0x0000D50B  # /* ul_FilterMapBlock             */
    BlockID_0000D50D = 0x0000D50D  # /* ul_IcDirBlock                 */
    BlockID_0000D50F = 0x0000D50F  # /* ul_DevieRfNameBlock           */
    BlockID_0000D511 = 0x0000D511  # /* ul_RfPowerBlock               */
    BlockID_0000D563 = 0x0000D563  # /* ul_RgbDataBlock               */
    BlockID_0000D565 = 0x0000D565  # /* ul_UartBaudRateBlock          */
    BlockID_0000D567 = 0x0000D567  # /* ul_BlockSizeBlock             */
    BlockID_0000D577 = 0x0000D577  # /* ul_DeviceMacBlock             */
    BlockID_0000D579 = 0x0000D579  # /* ul_DeviceSnFullStrBlock       */
    BlockID_0000D57B = 0x0000D57B  # /* ul_DeviceBoardVersionBlock    */
    BlockID_0000D57D = 0x0000D57D  # /* ul_DeviceFirmwareVersionBlock */

# -------------------- UHL 指令 BlockID（可选） --------------------
if UHL_LEVEL_EN:
    class e_BlockID_UHL(IntEnum):
        BlockID_0000D603 = 0x0000D603  # /* hl_DotIdBlock                 */
        BlockID_0000D607 = 0x0000D607  # /* hl_BleConnIntervalBlock       */
        BlockID_0000D611 = 0x0000D611  # /* hl_AccRangeBlock              */
        BlockID_0000D613 = 0x0000D613  # /* hl_GyroRangeBlock             */
        BlockID_0000D61B = 0x0000D61B  # /* hl_MagEllipsoidCalParamBlock  */
        BlockID_0000D621 = 0x0000D621  # /* hl_FlowIdFormatBlock          */
        BlockID_0000D62B = 0x0000D62B  # /* hl_AhrsOffsetBlock            */
        BlockID_0000D631 = 0x0000D631  # /* hl_DataPortBlock              */
        BlockID_0000D633 = 0x0000D633  # /* hl_DataPortMapBlock           */
        BlockID_0000D635 = 0x0000D635  # /* hl_DeviceStateBlock           */
        BlockID_0000D641 = 0x0000D641  # /* hl_AntFilterParamBlock     */
        BlockID_0000D643 = 0x0000D643  # /* hl_FingerMapBlock             */

# -------------------- FHL 指令 BlockID（可选） --------------------

# -------------------- FL 指令 BlockID（可选） --------------------

# -------------------- Dongle 用户指令 BlockID（可选） --------------------
if UDG_LEVEL_EN:
    class e_BlockID_UDG(IntEnum):
        BlockID_0000C001 = 0x0000C001  # /* DL_DongleSnFullStrBlock           */
        BlockID_0000C007 = 0x0000C007  # /* DL_DeviceBoardVersionBlock        */
        BlockID_0000C008 = 0x0000C008  # /* DL_DeviceFirmwareVersionBlock     */
        BlockID_0000C011 = 0x0000C011  # /* DL_DeviceListBlock                */
        BlockID_0000C013 = 0x0000C013  # /* DL_DeviceConnNumsBlock            */
        BlockID_0000C021 = 0x0000C021  # /* DL_IdentifyWayBlock               */

# -------------------- Dongle 厂家指令 BlockID（可选） --------------------
if FDG_LEVEL_EN:
    class e_BlockID_FDG(IntEnum):
        BlockID_00000000 = 0x00000000  # /* DL_ScanBlock        */
        BlockID_0000000F = 0x0000000F  # /* DL_TimeStampSyncBlock */
