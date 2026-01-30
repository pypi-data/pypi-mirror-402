# -*- coding: utf-8 -*-
"""
把 C 代码中的宏、枚举全部平移到 Python，保持原注释不变。
"""

# -------------------- 宏定义 --------------------
DEFAULT_RF_DISCONN = 0xFFFF   #  蓝牙断开默认值
DEFAULT_RFID       = 0x3F     #  默认 RF ID
DEFAULT_DOTID      = 0xFF     #  默认 DOT ID
DEFAULT_DONGLEID   = 0xE0     #  默认 Dongle ID

# -------------------- 错误码枚举 --------------------
from enum import IntEnum

from .zlbusConfig import *

class e_ERROR_CMU(IntEnum):
    """包/功能错误码"""
    ERROR_PK_NONE                     = 0x00  # 无错误
    ERROR_PK_LEN                      = 0x01  # 包长度错误
    ERROR_PK_CMDID                    = 0x02  # 未知指令类型
    ERROR_PK_FORMAT                   = 0x03  # 未知包格式
    ERROR_PK_CHECK                    = 0x04  # 校验错误

    ERROR_PK_SUBCMDID                 = 0x05  # 子指令ID错误
    ERROR_PK_DOT                      = 0x06  # DOT ID不匹配
    ERROR_PK_DATA                     = 0x07  # 错误数据(or 数据格式)
    ERROR_PK_TRACKID                  = 0x08  # 设备ID不匹配 (Dongle 端)
    ERROR_PK_DONGLEID                 = 0x09  # Dongle ID不匹配 (Dongle 端)
    ERROR_PK_RFID                     = 0x0A  # 蓝牙ID不匹配

    FUC_ERROR_RF_DISCONN              = 0x0B  # 蓝牙未连接/设备不存在
    FUC_ERROR_FACTORY_SET             = 0x0C  # 厂家设置未打开
    FUC_ERROR_RFMAC                   = 0x0D  # RF MAC 格式错误
    FUC_ERROR_IO                      = 0x0E  # I/O error

    FUNC_ERROR_NOT_INIT               = 0x10  # 功能未初始化
    FUNC_ERROR_NOT_CONFIG             = 0x11  # 功能未配置
    FUNC_ERROR_NOT_OPEN               = 0x12  # 功能未开启

    ERROR_NOKNOW                      = 0xFE  # 未知错误
    ERROR_NULL                        = 0xFF  # 传入空指针

# -------------------- 流水号格式枚举 --------------------
# class e_FLOW_FORMAT(IntEnum):
#     """流水号格式"""
#     FLOW_ID_FORMAT_8  = 0  # 流水号格式 0x00 ~ 0xFF
#     FLOW_ID_FORMAT_16 = 1  # 流水号格式 0x0000 ~ 0xFFFF
