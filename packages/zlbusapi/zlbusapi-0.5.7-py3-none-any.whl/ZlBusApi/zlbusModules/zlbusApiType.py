"""
ZLBus API Type Python Interface

This module provides Python encapsulations of the C structures defined in the zlbusApiType.h header file.
"""

import ctypes
from ctypes import c_uint8, c_uint16, c_uint32, c_uint64, c_int8, c_bool, c_float, c_double
from .zlbusBaseType import Axis3_I16, Axis3_Float, AhrsQuaternion, AhrsEuler

from enum import IntEnum

from .zlbusConfig import *

# ---------- 匿名 union ----------
class _xxxIdBlockU(ctypes.Union):
    _pack_   = 1          # 按 1 字节对齐，和 C 保持一致
    _fields_ = [
        ("rfId",     ctypes.c_uint8),          # 整个字节
        ("_bits",    ctypes.c_uint8, 8),       # 位段载体
    ]

    # 用 property 把位段再拆成 icId/dongleId
    @property
    def icId(self):
        return self._bits & 0x1F

    @icId.setter
    def icId(self, val):
        self._bits = (self._bits & 0xE0) | (val & 0x1F)

    @property
    def dongleId(self):
        return (self._bits >> 5) & 0x07

    @dongleId.setter
    def dongleId(self, val):
        self._bits = ((val & 0x07) << 5) | (self._bits & 0x1F)

class xxxIdBlock(ctypes.LittleEndianStructure):
    """基本ID结构"""
    _fields_ = [
        ("cmdId",    ctypes.c_uint8),
        ("subCmdId", ctypes.c_uint8),
        ("u",        _xxxIdBlockU),           # 对应 C 里的匿名 union
        ("dotId",    ctypes.c_uint8),
        ("flowId",   ctypes.c_uint32),
        ("userId",   ctypes.c_uint8),
    ]

    # 让外部可直接读写 rfId / icId / dongleId
    rfId     = property(lambda s: s.u.rfId,     lambda s, v: setattr(s.u, 'rfId', v))
    icId     = property(lambda s: s.u.icId,     lambda s, v: setattr(s.u, 'icId', v))
    dongleId = property(lambda s: s.u.dongleId, lambda s, v: setattr(s.u, 'dongleId', v))


# uBIT(n) => 1 << n
def uBIT(n: int) -> int:
    return 1 << n

class e_Upload_DataFormat(IntEnum):
    """数据格式位掩码枚举"""
    NEW_UPLOAD_DATA_QUATERNION = uBIT(0)   # /* 四元数           */
    NEW_UPLOAD_DATA_RPY        = uBIT(1)   # /* 欧拉角           */
    NEW_UPLOAD_DATA_ACC        = uBIT(2)   # /* 加速度 g         */
    NEW_UPLOAD_DATA_GYRO       = uBIT(3)   # /* 陀螺仪 °/s       */
    NEW_UPLOAD_DATA_MAG        = uBIT(4)   # /* 磁力计 uT        */
    NEW_UPLOAD_DATA_LIN_ACC    = uBIT(5)   # /* 线性加速度 g/s²  */

    NEW_UPLOAD_DATA_TEMP       = uBIT(14)  # /* IMU 传感器温度   */
    NEW_UPLOAD_DATA_ADCx       = uBIT(16)  # /* ADC(手指弯曲)    */
    NEW_UPLOAD_DATA_REDUCED    = uBIT(29)  # /* REDUCED(压缩数据)*/
    NEW_UPLOAD_DATA_HL_TIME    = uBIT(30)  # /* 时间戳 (double)  */
    NEW_UPLOAD_DATA_TIME       = uBIT(31)  # /* 时间戳 (float)   */


# IMU 数据
class ul_ImuDataBlock(ctypes.LittleEndianStructure):
    """IMU 数据 blockID: 0x1000"""
    _fields_ = [
        ("pkId", xxxIdBlock),
        ("effectiveDataFormat", c_uint32),  # enum e_UPLOAD_FORMAT
        ("timeStamp", c_double),            # 时间戳 [单位：ms]
        ("temperature", c_float),           # 温度 [单位：℃]
        ("quat", AhrsQuaternion),           # 四元数
        ("euler", AhrsEuler),               # 欧拉角 [单位：°]
        ("acc", Axis3_Float),               # 加速度计 [单位：g]
        ("gyro", Axis3_Float),              # 陀螺仪 [单位：°/s]
        ("mag", Axis3_Float),               # 磁力计 [单位：uT]
        ("lineAcc", Axis3_Float),           # 线性加速度 [单位：g]
    ]

    # ------- 可选字段 -------
    _fields_.extend([
        ("None0", Axis3_Float * 4),
        ("None1", Axis3_I16 * 3),
    ])


# 设备状态
class ul_DeviceStateBlock(ctypes.LittleEndianStructure):
    """设备状态 blockID: 0x1100"""
    _fields_ = [
        ("pkId", xxxIdBlock),
        ("deviceState", c_uint32),  # 模块(IC) 状态
    ]


# 电池
class ul_BatteryBlock(ctypes.LittleEndianStructure):
    """电池 blockID: 0x1400"""
    _fields_ = [
        ("pkId", xxxIdBlock),
        ("mvOk", c_bool),
        ("levelOk", c_bool),
        ("mv", c_uint16),
        ("level", c_uint8),
    ]


# ANT 弯曲传感器
UL_ANT_MAX_NUMS = 6

class ul_AntValueBlock(ctypes.LittleEndianStructure):
    """ANT 弯曲传感器 blockID: 0x1500"""
    _fields_ = [
        ("pkId", xxxIdBlock),
        ("antNums", c_uint32),
        ("effectiveDataFormat", c_uint32),
        ("timeStamp", c_double),            # 时间戳 [单位：ms]
        ("normalization", c_bool),
        ("antValue", c_uint16 * UL_ANT_MAX_NUMS),
    ]


# 基本指令
# blockID: 0x00FF0000, 0x00110000
class ul_CtrlDataBaseBlock(ctypes.LittleEndianStructure):
    _fields_ = [
        ("pkId", xxxIdBlock),
        ("error", c_bool),     # True状态下，errCode有效
        ("errCode", c_uint8),
    ]


# blockID: 0xD501
class ul_UploadDataFormatBlock(ctypes.LittleEndianStructure):
    _fields_ = [
        ("pkId", xxxIdBlock),
        ("uploadDataFormat", c_uint32),  # 上报数据格式 {e_UPLOAD_FORMAT}
    ]


class e_SampleHz(IntEnum):
    """采样频率"""
    TK_Sample_200HZ = 200  # 200 Hz
    TK_Sample_240HZ = 240  # 240 Hz
    TK_Sample_250HZ = 250  # 250 Hz


# blockID: 0xD503
class ul_SamplingHzBlock(ctypes.LittleEndianStructure):
    _fields_ = [
        ("pkId", xxxIdBlock),
        ("samplingHz", c_uint16),  # 采样频率 {e_SampleHz}
    ]


# 上传频率枚举
class e_UploadHz(IntEnum):
    TK_Sample_200HZ_DIVx_UPLOAD_1HZ = 0xC8
    TK_Sample_200HZ_DIVx_UPLOAD_5HZ = 0x28
    TK_Sample_200HZ_DIVx_UPLOAD_10HZ = 0x14
    TK_Sample_200HZ_DIVx_UPLOAD_20HZ = 0x0A
    TK_Sample_200HZ_DIVx_UPLOAD_25HZ = 0x08
    TK_Sample_200HZ_DIVx_UPLOAD_50HZ = 0x04
    TK_Sample_200HZ_DIVx_UPLOAD_100HZ = 0x02
    TK_Sample_200HZ_DIVx_UPLOAD_200HZ = 0x01

    TK_Sample_240HZ_DIVx_UPLOAD_1HZ = 0xF0
    TK_Sample_240HZ_DIVx_UPLOAD_5HZ = 0x30
    TK_Sample_240HZ_DIVx_UPLOAD_10HZ = 0x18
    TK_Sample_240HZ_DIVx_UPLOAD_20HZ = 0x0C
    TK_Sample_240HZ_DIVx_UPLOAD_25HZ = 0x09
    TK_Sample_240HZ_DIVx_UPLOAD_30HZ = 0x08
    TK_Sample_240HZ_DIVx_UPLOAD_60HZ = 0x04
    TK_Sample_240HZ_DIVx_UPLOAD_120HZ = 0x02
    TK_Sample_240HZ_DIVx_UPLOAD_240HZ = 0x01

    TK_Sample_250HZ_DIVx_UPLOAD_1HZ = 0xFA
    TK_Sample_250HZ_DIVx_UPLOAD_5HZ = 0x32
    TK_Sample_250HZ_DIVx_UPLOAD_10HZ = 0x19
    TK_Sample_250HZ_DIVx_UPLOAD_25HZ = 0x0A
    TK_Sample_250HZ_DIVx_UPLOAD_50HZ = 0x05
    TK_Sample_250HZ_DIVx_UPLOAD_250HZ = 0x01


# blockID: 0xD505
class ul_UploadHzBlock(ctypes.LittleEndianStructure):
    _fields_ = [
        ("pkId", xxxIdBlock),
        ("UploadHz", c_uint16),  # 上报频率 (采样分频表示上报频率) {e_UploadHz}
    ]


# 滤波参数枚举
class e_FiterParam(IntEnum):
    """滤波参数位掩码枚举"""
    TK_StaticFiter           = 1 << 0  # 静态滤波
    TK_SixAxisDataFiter      = 1 << 1  # 6轴模式
    TK_MagDataFixedFiter     = 1 << 4  # 抗磁干扰
    TK_TemperatureCompensate = 1 << 6  # 温度补偿
    TK_ZeroOffsetFiter       = 1 << 7  # 实时滤波(零点滤波)
    TK_ZeroReckonFiter       = 1 << 9  # 零点积分滤波


# blockID: 0xD50B
class ul_FilterMapBlock(ctypes.LittleEndianStructure):
    _fields_ = [
        ("pkId", xxxIdBlock),
        ("filterMap", c_uint16),  # 滤波参数 {e_FiterParam}
    ]


# IC安装方向枚举
class e_Convention(IntEnum):
    TK_NED_0 = 0x00  # default value
    TK_NED_1 = 0x01
    TK_NED_2 = 0x02
    TK_NED_3 = 0x03
    TK_ENU_0 = 0x04
    TK_ENU_1 = 0x05
    TK_ENU_2 = 0x06
    TK_ENU_3 = 0x07


# blockID: 0xD50D
class ul_IcDirBlock(ctypes.LittleEndianStructure):
    _fields_ = [
        ("pkId", xxxIdBlock),
        ("icDir", c_uint8),  # IC 安装方向 {e_Convention}
    ]


# blockID: 0xD50F
class ul_DevieRfNameBlock(ctypes.LittleEndianStructure):
    _fields_ = [
        ("pkId", xxxIdBlock),
        ("name", c_uint8 * 20),  # Rf 广播名称 {字符串}
    ]


# blockID: 0xD511
class ul_RfPowerBlock(ctypes.LittleEndianStructure):
    _fields_ = [
        ("pkId", xxxIdBlock),
        ("rssi", c_int8),  # dBm
    ]


# RGB Color枚举
class e_LedColor(IntEnum):
    TK_LED_RED = 0x01    # 红
    TK_LED_GREEN = 0x02  # 绿
    TK_LED_BLUE = 0x04   # 蓝
    TK_LED_YELLOW = 0x03 # 黄
    TK_LED_PUEPLE = 0x05 # 紫
    TK_LED_CYAN = 0x06   # 青
    TK_LED_WHITE = 0x07  # 白


# RGB 点灯模式枚举
class e_LedMode(IntEnum):
    TK_LED_MODE_LIGHT = 0      # 常亮
    TK_LED_MODE_BREATHE = 1    # 呼吸灯
    TK_LED_MODE_FLICKER_LOW = 1    # 低频闪烁
    TK_LED_MODE_FLICKER_MEDIUM = 2 # 中频闪烁
    TK_LED_MODE_FLICKER_HIGH = 3   # 高频闪烁


# blockID: 0xD563
class ul_RgbDataBlock(ctypes.LittleEndianStructure):
    _fields_ = [
        ("pkId", xxxIdBlock),
        ("color", c_uint8),  # LED 颜色 {e_LedColor}
        ("mode", c_uint8),   # LED 点亮模式 {e_LedMode}
    ]


# 波特率枚举
class e_BaudRate(IntEnum):
    TK_BaudRate_115200 = 0x1C200
    TK_BaudRate_128000 = 0x1F400
    TK_BaudRate_256000 = 0x3E800
    TK_BaudRate_460800 = 0x70800
    TK_BaudRate_512000 = 0x7D000
    TK_BaudRate_750000 = 0xB71B0
    TK_BaudRate_921600 = 0xE1000


# blockID: 0xD565
class ul_UartBaudRateBlock(ctypes.LittleEndianStructure):
    _fields_ = [
        ("pkId", xxxIdBlock),
        ("baudRate", c_uint32),  # 串口波特率
    ]


# blockID: 0xD567
class ul_BlockSizeBlock(ctypes.LittleEndianStructure):
    _fields_ = [
        ("pkId", xxxIdBlock),
        ("type", c_uint8),      # enum e_BlockSizeType
        ("blockSize", c_uint8),
    ]


# blockID: 0xD577
class ul_DeviceMacBlock(ctypes.LittleEndianStructure):
    _fields_ = [
        ("pkId", xxxIdBlock),
        ("macStr", c_uint8 * 18),  # MAC 地址
    ]


# blockID: 0xD579
class ul_DeviceSnFullStrBlock(ctypes.LittleEndianStructure):
    _fields_ = [
        ("pkId", xxxIdBlock),
        ("snFullStr", c_uint8 * 24),  # 完整设备SN编码
    ]


# blockID: 0xD57B
class ul_DeviceBoardVersionBlock(ctypes.LittleEndianStructure):
    _fields_ = [
        ("pkId", xxxIdBlock),
        ("boardVersion", c_uint8 * 64),  # 硬件版本号
    ]


# blockID: 0xD57D
class ul_DeviceFirmwareVersionBlock(ctypes.LittleEndianStructure):
    _fields_ = [
        ("pkId", xxxIdBlock),
        ("firmwareVersion", c_uint8 * 64),  # 固件版本号
    ]

#------------------------------------------------------------------------------------------------
# 高级指令
#------------------------------------------------------------------------------------------------

# blockID: 0xD601
# 给这个 ctypes 结构体起一个别名
hl_UploadDataFormatBlock = ul_UploadDataFormatBlock


if UHL_LEVEL_EN:
    # blockID: 0xD603
    class hl_DotIdBlock(ctypes.LittleEndianStructure):
        _fields_ = [
            ("pkId", xxxIdBlock),
            ("dotId", c_uint8),  # dotId
        ]

if UHL_LEVEL_EN:
    # blockID: 0xD607
    class hl_BleConnIntervalBlock(ctypes.LittleEndianStructure):
        _fields_ = [
            ("pkId", xxxIdBlock),
            ("bleConnInterval", c_float),  # 交互间隔
        ]

if UHL_LEVEL_EN:
    # 加速度计量程枚举
    class e_AccRange(IntEnum):
        TK_ACC_RANGE_2G = 0x00   # ±2G
        TK_ACC_RANGE_4G = 0x01   # ±4G
        TK_ACC_RANGE_8G = 0x02   # ±8G
        TK_ACC_RANGE_16G = 0x03  # ±16G


    # blockID: 0xD611
    class hl_AccRangeBlock(ctypes.LittleEndianStructure):
        _fields_ = [
            ("pkId", xxxIdBlock),
            ("accRange", c_uint8),  # 加速度计量程
        ]


    # 陀螺仪量程枚举
    class e_GyroRange(IntEnum):
        TK_GYRO_RANGE_250DPS = 0x00   # ±250DPS
        TK_GYRO_RANGE_500DPS = 0x01   # ±500DPS
        TK_GYRO_RANGE_1000DPS = 0x02  # ±1000DPS
        TK_GYRO_RANGE_2000DPS = 0x03  # ±2000DPS
        TK_GYRO_RANGE_4000DPS = 0x03  # ±4000DPS 仅限于高量程 支持


    # blockID: 0xD613
    class hl_GyroRangeBlock(ctypes.LittleEndianStructure):
        _fields_ = [
            ("pkId", xxxIdBlock),
            ("gyroRange", c_uint8),  # 陀螺仪量程
        ]

if UHL_LEVEL_EN:
    class MagEllipsoidCalParamBlock_t(ctypes.LittleEndianStructure):
        _fields_ = [
            ("kX", c_float), ("kY", c_float), ("kZ", c_float),
            ("Ox", c_float), ("Oy", c_float), ("Oz", c_float),
        ]


    # blockID: 0xD61B
    class hl_MagEllipsoidCalParamBlock(ctypes.LittleEndianStructure):
        _fields_ = [
            ("pkId", xxxIdBlock),
            ("kX", c_float), ("kY", c_float), ("kZ", c_float),
            ("Ox", c_float), ("Oy", c_float), ("Oz", c_float),
        ]


    # 流水号格式枚举
    class e_TK_FlowIdFormat(IntEnum):
        TK_FLOW_ID_FORMAT_8 = 0
        TK_FLOW_ID_FORMAT_16 = 1


    # blockID: 0xD621
    class hl_FlowIdFormatBlock(ctypes.LittleEndianStructure):
        _fields_ = [
            ("pkId", xxxIdBlock),
            ("flowIdFormat", c_uint8),  # 上传数据流水号格式
        ]

    # blockID: 0xD62B
    class hl_AhrsOffsetBlock(ctypes.LittleEndianStructure):
        _fields_ = [
            ("pkId", xxxIdBlock),
            ("quatOffset", AhrsQuaternion),  # 姿态offset
        ]

if UHL_LEVEL_EN:
    # 数据输出端口类型枚举
    class e_DataOutPort(IntEnum):
        TK_RF_PORT = 1 << 0
        TK_UART_PORT = 1 << 1
        TK_SPIM_PORT = 1 << 3


    # blockID: 0xD631
    class hl_DataPortBlock(ctypes.LittleEndianStructure):
        _fields_ = [
            ("pkId", xxxIdBlock),
            ("dataPort", c_uint16),  # 数据输出端口
        ]


    # blockID: 0xD633
    class hl_DataPortMapBlock(ctypes.LittleEndianStructure):
        _fields_ = [
            ("pkId", xxxIdBlock),
            ("dataPortMap", c_uint16),  # 可用输出端口
        ]


    # blockID: 0xD635
    class hl_DeviceStateBlock(ctypes.LittleEndianStructure):
        _fields_ = [
            ("pkId", xxxIdBlock),
            ("state", c_uint32),  # IC 状态
        ]


    # blockID: 0xD641
    class AntFilterParam_t(ctypes.LittleEndianStructure):
        _fields_ = [
            ("offset", c_uint16),
            ("kp", c_float),
        ]


    class hl_AntFilterParamBlock(ctypes.LittleEndianStructure):
        _fields_ = [
            ("pkId", xxxIdBlock),
            ("offset", c_uint16),
            ("kp", c_float),
        ]


    # blockID: 0xD643
    class hl_FingerMapBlock(ctypes.LittleEndianStructure):
        _fields_ = [
            ("pkId", xxxIdBlock),
            ("fingerMap", c_uint8),  # 手指Map
        ]

if UHL_LEVEL_EN:
    # antEnableMap枚举
    class e_AntEn(IntEnum):
        TK_ANT0_ENABLE = 1 << 0
        TK_ANT1_ENABLE = 1 << 1
        TK_ANT2_ENABLE = 1 << 2
        TK_ANT3_ENABLE = 1 << 3
        TK_ANT4_ENABLE = 1 << 4
        TK_ANT5_ENABLE = 1 << 5


    # BlockSizeType枚举
    class e_BlockSizeType(IntEnum):
        iic_blockSizeType = 0
        spim_blockSizeType = 1

#------------------------------------------------------------------------------------------------
# Dongle指令
#------------------------------------------------------------------------------------------------
if UDG_LEVEL_EN:
    class DeviceBlock_t(ctypes.LittleEndianStructure):
        """设备信息块"""
        _fields_ = [
            ("devId",     ctypes.c_uint8),      # uint8_t devId
            ("connState", ctypes.c_uint8),      # uint8_t connState
            ("mac",       ctypes.c_uint8 * 6),  # uint8_t mac[6]
            ("name",      ctypes.c_uint8 * 20), # uint8_t name[20]
        ]


    # blockID: 0xC001
    class DL_DongleSnFullStrBlock(ctypes.LittleEndianStructure):
        _fields_ = [
            ("pkId", xxxIdBlock),
            ("snFullStr", c_uint8 * 24),  # 完整设备SN编码
        ]


    # blockID: 0xC007
    class DL_DeviceBoardVersionBlock(ctypes.LittleEndianStructure):
        _fields_ = [
            ("pkId", xxxIdBlock),
            ("boardVersion", c_uint8 * 64),  # 硬件版本号
        ]


    # blockID: 0xC008
    class DL_DeviceFirmwareVersionBlock(ctypes.LittleEndianStructure):
        _fields_ = [
            ("pkId", xxxIdBlock),
            ("firmwareVersion", c_uint8 * 64),  # 固件版本号
        ]


    # blockID: 0xC011
    class DL_DeviceListBlock(ctypes.LittleEndianStructure):
        """设备列表"""
        _fields_ = [
            ("pkId", xxxIdBlock),
            ("list", DeviceBlock_t * 20),
            ("nums", c_uint8),
        ]


    # blockID: 0xC013
    class DL_DeviceConnNumsBlock(ctypes.LittleEndianStructure):
        """最大子设备数"""
        _fields_ = [
            ("pkId", xxxIdBlock),
            ("connNums", c_uint8),
        ]


    # blockID: 0xC021
    class DL_IdentifyWayBlock(ctypes.LittleEndianStructure):
        """匹配类型(地址匹配 or 名称匹配)"""
        _fields_ = [
            ("pkId", xxxIdBlock),
            ("isMacType", c_uint8),
        ]


    # blockID: 0xC000
    class DL_ScanBlock(ctypes.LittleEndianStructure):
        _fields_ = [
            ("pkId", xxxIdBlock),
            ("mac", c_uint8 * 6),
            ("name", c_uint8 * 20),
        ]


    # blockID: 0xC00F
    class DL_TimeStampSyncBlock(ctypes.LittleEndianStructure):
        _fields_ = [
            ("pkId", xxxIdBlock),
            ("timeStamp", c_double),
        ]
