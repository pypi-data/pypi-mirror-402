"""
ZLBus API Python Interface

This module provides a Python interface to the ZLBus API library.
"""

import os
import platform
import ctypes
from ctypes import CDLL
from ctypes import c_uint8, c_uint16, c_uint32, c_int8, c_int16, c_int32, c_bool, c_float   
from ctypes import c_void_p, c_char_p, POINTER, byref, cast, memmove, create_string_buffer

# from .zlbus_modules import *
from .zlbusModules import (
    MagEllipsoidCalParamBlock_t,
    AntFilterParam_t,
    DeviceBlock_t
)
from .zlbusModules import AhrsQuaternion
from .zlbusModules import DEFAULT_RFID, DEFAULT_DOTID, DEFAULT_DONGLEID

def _get_dll_name():
    """根据操作系统和架构获取合适的DLL文件名"""
    system = platform.system()
    architecture = platform.architecture()[0]
    machine = platform.machine().lower()
    
    if system == 'Windows':
        # Windows下只考虑64位版本
        return 'zlbus_x64.dll'
    elif system == 'Linux':
        # Linux下根据架构选择不同的库文件
        if 'arm' in machine or 'aarch' in machine:
            return 'libzlbus_arm64.so'
        else:
            return 'libzlbus_x64.so'
    else:
        # 其他系统默认使用Linux x64版本
        return 'libzlbus_x64.so'

_dll_name = _get_dll_name()

def _find_dll_path():
    """查找DLL文件的路径，支持多种可能的位置和新的目录结构"""
    system = platform.system()
    
    # 根据系统确定子目录
    system_subdir = 'linux' if system == 'Linux' else 'win'
    
    # 首先尝试在包目录的bin/[system]子目录中查找
    package_bin_path = os.path.join(os.path.dirname(__file__), 'bin', system_subdir, _dll_name)
    if os.path.exists(package_bin_path):
        return package_bin_path
    
    # 如果在包目录中找不到，尝试在site-packages的bin/[system]目录中查找
    try:
        import site
        site_packages = site.getsitepackages()
        for site_package in site_packages:
            site_bin_path = os.path.join(site_package, 'bin', system_subdir, _dll_name)
            if os.path.exists(site_bin_path):
                return site_bin_path
    except:
        pass
    
    # 如果还是找不到，尝试在sys.prefix的bin/[system]目录中查找
    try:
        import sys
        prefix_bin_path = os.path.join(sys.prefix, 'bin', system_subdir, _dll_name)
        if os.path.exists(prefix_bin_path):
            return prefix_bin_path
    except:
        pass
    
    # 尝试在包目录的上一级目录的bin/[system]目录中查找（处理pip安装的情况）
    parent_bin_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bin', system_subdir, _dll_name)
    if os.path.exists(parent_bin_path):
        return parent_bin_path
    
    # 如果所有位置都找不到，返回包目录中的路径（用于显示错误信息）
    return package_bin_path

_bin_path = _find_dll_path()

class SafeDLL:
    def __init__(self, dll):
        self._dll = dll

    def __getattr__(self, name):
        try:
            return getattr(self._dll, name)
        except AttributeError:
            # Return a dummy function that does nothing and returns 0
            def dummy_func(*args, **kwargs):
                return 0
            return dummy_func

try:
    _lib = SafeDLL(CDLL(_bin_path))
except OSError as e:
    print(f"Warning: Could not load {_dll_name} from {_bin_path}. Some functions may not be available.")
    _lib = SafeDLL(None)

# Define types
uint8_t = c_uint8
uint16_t = c_uint16
uint32_t = c_uint32
int16_t = c_int16
int32_t = c_int32
bool_t = c_bool

# -------------------------------------------------------------
# 工具：申请/释放帧缓存的快捷函数
# -------------------------------------------------------------
_MAX_FRAME = 256          # 内部统一缓存大小
_MAX_MAX_FRAME = 1024     # 内部统一缓存大小
_M_ID = 2
_S_ID = 1
_S_ID_MAX = 0x11

def _make_buffer(max_size: int = 256):
    """创建默认 256 字节的帧缓存并返回 (buffer, c_uint16(max_size))"""
    buf = create_string_buffer(max_size)
    return cast(buf, POINTER(c_uint8)), c_uint16(max_size)

# 统一包装
def _call_cmd(cmdType, func, rf_id, dot_id, *args) -> bytes:
    """
    统一调用函数
    :param func: 底层 C 函数，要求拥有属性 cmdType = _S_ID 或 _M_ID
                 _S_ID -> int func(rf_id,        buf, buf_len)
                 _M_ID -> int func(rf_id, dot_id, buf, buf_len)
    :param rf_id: 必传
    :param dot_id: 当 cmdType == _S_ID 时，设置None即可
    :param args:  额外位置参数，放在固定参数之前
    :return:      bytes
    """
    if cmdType == _S_ID_MAX:
        max_frame = _MAX_MAX_FRAME
    else:
        max_frame = _MAX_FRAME
    # 统一缓冲区
    buf, buf_len = _make_buffer(max_frame)
    # print('buf_len:', type(buf_len), buf_len)
    if cmdType == _M_ID:
        c_args = args + (rf_id, dot_id, buf, buf_len)
    elif cmdType == _S_ID or cmdType == _S_ID_MAX:
        c_args = args + (rf_id, buf, buf_len)
    else:
        raise ValueError('cmdType must be _S_ID or _M_ID')

    # print('\n', type(buf))
    # print(hex(rf_id), hex(dot_id))
    buf_size = func(*c_args)
    # print(buf_size)
    if buf_size < 0:
        raise RuntimeError(f'_call_cmd failed, ret={buf_size}')
    return ctypes.string_at(buf, buf_size)
"""
    result = (ctypes.c_byte * buf_size)()
    ctypes.memmove(result, buf, buf_size)
    return bytes(result)
"""

# -------------------------------------------------------------
# -------------------------------------------------------------


# Function prototypes
# ---------- zl_checkXor8_compute ----------
_lib.zl_checkXor8_compute.argtypes = [POINTER(uint8_t), uint32_t]
_lib.zl_checkXor8_compute.restype = uint8_t

def zl_checkXor8_compute(data, size):
    """
    Compute XOR checksum for given data.
    
    Args:
        data: bytes or bytearray containing the data
        size: size of the data
    
    Returns:
        uint8_t: XOR checksum
    """
    data_array = (uint8_t * size).from_buffer_copy(data)
    return _lib.zl_checkXor8_compute(data_array, size)

# ---------- zl_checkSum8_compute ----------
_lib.zl_checkSum8_compute.argtypes = [POINTER(uint8_t), uint32_t]
_lib.zl_checkSum8_compute.restype = uint8_t

def zl_checkSum8_compute(data: bytes, size: int) -> int:
    """
    8-bit additive checksum.

    Args:
        data: bytes/bytearray
        size: data length

    Returns:
        uint8_t: additive checksum
    """
    data_array = (uint8_t * size).from_buffer_copy(data)
    return _lib.zl_checkSum8_compute(data_array, size)

# ---------- zl_crc16_compute ----------
_lib.zl_crc16_compute.argtypes = [POINTER(uint8_t), uint32_t, POINTER(uint16_t)]
_lib.zl_crc16_compute.restype = uint16_t

def zl_crc16_compute(data: bytes, size: int, crc_init: int = 0xFFFF) -> int:
    """
    16-bit CRC (CCITT/Fletcher-like).

    Args:
        data: bytes/bytearray
        size: data length
        crc_init: initial CRC value (default 0xFFFF)

    Returns:
        uint16_t: computed CRC16
    """
    data_array = (uint8_t * size).from_buffer_copy(data)
    crc_in = uint16_t(crc_init)
    return _lib.zl_crc16_compute(data_array, size, ctypes.byref(crc_in))

# ---------- ota_firmware_crc32_compute ----------
_lib.ota_firmware_crc32_compute.argtypes = [POINTER(uint8_t), uint32_t, POINTER(uint32_t)]
_lib.ota_firmware_crc32_compute.restype = uint32_t

def ota_firmware_crc32_compute(data: bytes, size: int, crc_init: int = 0xFFFFFFFF) -> int:
    """
    32-bit CRC for OTA firmware image.

    Args:
        data: bytes/bytearray
        size: data length
        crc_init: initial CRC32 value (default 0xFFFFFFFF)

    Returns:
        uint32_t: computed CRC32
    """
    data_array = (uint8_t * size).from_buffer_copy(data)
    crc_in = uint32_t(crc_init)
    return _lib.ota_firmware_crc32_compute(data_array, size, ctypes.byref(crc_in))

#------------------------------------------------------------------------------------------------------
# 数据解码
#------------------------------------------------------------------------------------------------------

# ---------- 创建/销毁解码器 ----------
_lib.ul_dataDecodeBlockCreate.argtypes = [uint8_t, uint8_t, uint16_t]
_lib.ul_dataDecodeBlockCreate.restype  = c_void_p           # 返回 uint32_t* 作为句柄

_lib.ul_dataDecodeBlockDelete.argtypes = [c_void_p]
_lib.ul_dataDecodeBlockDelete.restype  = None

def ul_dataDecodeBlockCreate(tracker_nums: int, user_id: int, max_nums: int) -> int:
    """
    创建数据解码器句柄（内部 uint32_t*）。

    :param tracker_nums: 同时接入的 tracker 数量
    :param user_id:      用户 ID
    :param max_nums:     最大缓存节点数
    :return: 句柄（int，实际为 c_void_p）
    """
    handle = _lib.ul_dataDecodeBlockCreate(uint8_t(tracker_nums), uint8_t(user_id), uint16_t(max_nums))
    if not handle:
        raise RuntimeError("ul_dataDecodeBlockCreate failed")
    return handle

def ul_dataDecodeBlockDelete(handle: int) -> None:
    """
    销毁解码器句柄。
    """
    _lib.ul_dataDecodeBlockDelete(c_void_p(handle))

# ---------- 链表状态查询 ----------
_lib.ul_dataBlockNoteSize.argtypes = [c_void_p]
_lib.ul_dataBlockNoteSize.restype  = c_int32

_lib.ul_dataBlockGetBlockID.argtypes = [c_void_p]
_lib.ul_dataBlockGetBlockID.restype  = uint32_t

def ul_dataBlockNoteSize(handle: int) -> int:
    """
    当前数据链表中的有效节点个数。
    """
    return _lib.ul_dataBlockNoteSize(c_void_p(handle))

def ul_dataBlockGetBlockID(handle: int) -> int:
    """
    获取链表头节点的 blockId，用于后续读取 / 跳过。
    """
    return _lib.ul_dataBlockGetBlockID(c_void_p(handle))

# ---------- 链表节点操作 ----------
_lib.ul_dataBlockSkipNote.argtypes = [c_void_p]
_lib.ul_dataBlockSkipNote.restype  = None

_lib.ul_dataBlockReadNote.argtypes = [c_void_p, c_void_p, uint16_t]
_lib.ul_dataBlockReadNote.restype  = c_int32

def ul_dataBlockSkipNote(handle: int) -> None:
    """
    直接丢弃链表头节点。
    """
    _lib.ul_dataBlockSkipNote(c_void_p(handle))

def ul_dataBlockReadNote(handle: int, block_size: int) -> bytes:
    """
    读取并删除链表头节点。

    :param handle:     解码器句柄
    :param block_size: 期望读取的字节数（通常由 ul_dataBlockGetBlockID 决定）
    :return:           bytes 对象
    """
    buf = create_string_buffer(block_size)
    ret = _lib.ul_dataBlockReadNote(c_void_p(handle), buf, uint16_t(block_size))
    if ret < 0:
        raise RuntimeError(f"ul_dataBlockReadNote failed, ret={ret}")
    return ctypes.string_at(buf, block_size)

_lib.ul_dataBlockNoteClear.argtypes = [c_void_p]
_lib.ul_dataBlockNoteClear.restype  = c_int32

def ul_dataBlockNoteClear(handle: int) -> int:
    """
    ul_dataBlockNoteClear
    """
    return _lib.ul_dataBlockNoteClear(c_void_p(handle))

# ---------- 流数据解码 ----------
_lib.ul_dataBlockDecode.argtypes = [c_void_p, POINTER(uint8_t), uint16_t]
_lib.ul_dataBlockDecode.restype  = None

def ul_dataBlockDecode(handle: int, data: bytes) -> None:
    """
    将收到的原始字节流送入解码器，解码后的数据节点追加到链表中。

    :param handle: 解码器句柄
    :param data:   原始流数据 bytes/bytearray
    """
    data_len = len(data)
    data_array = (uint8_t * data_len).from_buffer_copy(data)
    _lib.ul_dataBlockDecode(c_void_p(handle), data_array, uint16_t(data_len))

# ---------- 手动设置参数 ----------
_lib.ul_manualModifyDataFormat.argtypes = [c_void_p, uint8_t, uint32_t]
_lib.ul_manualModifyDataFormat.restype  = c_int32

def ul_manualModifyDataFormat(handle: int, tracker_index: int, data_format: int) -> int:
    """
    手动修改指定 tracker 的上传数据格式（e_UPLOAD_FORMAT 位图）。
    返回值：0 成功，<0 失败。
    """
    return _lib.ul_manualModifyDataFormat(c_void_p(handle), uint8_t(tracker_index), uint32_t(data_format))

_lib.ul_manualModifyDataFlowIdFormat.argtypes = [c_void_p, uint8_t]
_lib.ul_manualModifyDataFlowIdFormat.restype  = c_int32

def ul_manualModifyDataFlowIdFormat(handle: int, flow_id_format: int) -> int:
    """
    手动设置流水号格式：
        0 -> FLOW_ID_FORMAT_8
        1 -> FLOW_ID_FORMAT_16
    返回值：0 成功，<0 失败。
    """
    return _lib.ul_manualModifyDataFlowIdFormat(c_void_p(handle), uint8_t(flow_id_format))

_lib.ul_getDataFlowIdFormat.argtypes = [c_void_p]
_lib.ul_getDataFlowIdFormat.restype  = c_uint32

def ul_getDataFlowIdFormat(handle: int) -> int:
    """
    返回流水号格式：
        0 -> FLOW_ID_FORMAT_8
        1 -> FLOW_ID_FORMAT_16
    """
    return _lib.ul_getDataFlowIdFormat(c_void_p(handle))

#------------------------------------------------------------------------------------------------
# 用户指令
#------------------------------------------------------------------------------------------------

# -------------------------------------------------------------
# 1. 修改/获取输出数据格式
# -------------------------------------------------------------
_lib.ul_modifyDataFormat_id.argtypes = [c_uint32, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_modifyDataFormat_id.restype = c_int16

_lib.ul_modifyDataFormatNotSave_id.argtypes = [c_uint32, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_modifyDataFormatNotSave_id.restype = c_int16

_lib.ul_getDataFormat_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_getDataFormat_id.restype = c_int16

ul_modifyDataFormat = \
    lambda fmt, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_modifyDataFormat_id, rf_id, dot_id, fmt)

ul_modifyDataFormatNotSave = \
    lambda fmt, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_modifyDataFormatNotSave_id, rf_id, dot_id, fmt)

ul_getDataFormat = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_getDataFormat_id, rf_id, dot_id)

# -------------------------------------------------------------
# 2. 采样频率
# -------------------------------------------------------------
_lib.ul_modifySampleHz_id.argtypes = [c_uint16, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_modifySampleHz_id.restype = c_int16

_lib.ul_getSampleHz_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_getSampleHz_id.restype = c_int16

ul_modifySampleHz = \
    lambda fmt, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_modifySampleHz_id, rf_id, dot_id, fmt)

ul_getSampleHz = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_getSampleHz_id, rf_id, dot_id)

# -------------------------------------------------------------
# 3. 上传频率
# -------------------------------------------------------------
_lib.ul_modifyUploadHz_id.argtypes = [c_uint16, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_modifyUploadHz_id.restype = c_int16

_lib.ul_getUploadHz_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_getUploadHz_id.restype = c_int16

ul_modifyUploadHz = \
    lambda fmt, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_modifyUploadHz_id, rf_id, dot_id, fmt)

ul_getUploadHz = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_getUploadHz_id, rf_id, dot_id)

# -------------------------------------------------------------
# 4. 磁力计校准
# -------------------------------------------------------------
_lib.ul_startMagnetometerCalibration_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_startMagnetometerCalibration_id.restype = c_int16

ul_startMagnetometerCalibration = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_startMagnetometerCalibration_id, rf_id, dot_id)

# -------------------------------------------------------------
# 5. 滤波配置
# -------------------------------------------------------------
_lib.ul_configDataFilter_id.argtypes = [c_uint16, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_configDataFilter_id.restype = c_int16

_lib.ul_clearDataFilter_id.argtypes = [c_uint16, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_clearDataFilter_id.restype = c_int16

_lib.ul_getDataFilter_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_getDataFilter_id.restype = c_int16

ul_configDataFilter = \
    lambda fmt, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_configDataFilter_id, rf_id, dot_id, fmt)

ul_clearDataFilter = \
    lambda fmt, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_clearDataFilter_id, rf_id, dot_id, fmt)

ul_getDataFilter = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_getDataFilter_id, rf_id, dot_id)

# -------------------------------------------------------------
# 6. IC 安装方向
# -------------------------------------------------------------
_lib.ul_modifyIcConvention_id.argtypes = [c_uint8, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_modifyIcConvention_id.restype = c_int16

_lib.ul_getIcConvention_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_getIcConvention_id.restype = c_int16

ul_modifyIcConvention = \
    lambda fmt, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_modifyIcConvention_id, rf_id, dot_id, fmt)

ul_getIcConvention = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_getIcConvention_id, rf_id, dot_id)

# -------------------------------------------------------------
# 7. RF 广播名称
# -------------------------------------------------------------
_lib.ul_modifyIcAdvName_id.argtypes = [c_char_p, c_char_p, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_modifyIcAdvName_id.restype = c_int16

_lib.ul_getIcAdvName_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_getIcAdvName_id.restype = c_int16

ul_modifyIcAdvName = \
    lambda fmt, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_modifyIcAdvName_id, rf_id, dot_id, fmt)

ul_getIcAdvName = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_getIcAdvName_id, rf_id, dot_id)

# -------------------------------------------------------------
# 8. RF 功率
# -------------------------------------------------------------
_lib.ul_modifyIcRfPower_id.argtypes = [c_int8, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_modifyIcRfPower_id.restype = c_int16

_lib.ul_getIcRfPower_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_getIcRfPower_id.restype = c_int16

ul_modifyIcRfPower = \
    lambda rssi, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_modifyIcRfPower_id, rf_id, dot_id, rssi)

ul_getIcRfPower = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_getIcRfPower_id, rf_id, dot_id)

# -------------------------------------------------------------
# 9. 断开 RF / 数据输出使能 / Yaw 归零 / ANT 归 1000 化校准
# -------------------------------------------------------------
_lib.ul_disconnectIcRf_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_disconnectIcRf_id.restype = c_int16

_lib.ul_enableDataOutPut_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_enableDataOutPut_id.restype = c_int16

_lib.ul_disEnableDataOutPut_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_disEnableDataOutPut_id.restype = c_int16

_lib.ul_resetYaw2zero_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_resetYaw2zero_id.restype = c_int16

_lib.ul_enableSimulateCalibration_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_enableSimulateCalibration_id.restype = c_int16

_lib.ul_disableSimulateCalibration_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_disableSimulateCalibration_id.restype = c_int16

_lib.ul_configSimulateCalibrationMode_id.argtypes = [c_uint8, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_configSimulateCalibrationMode_id.restype = c_int16

ul_disconnectIcRf          = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_disconnectIcRf_id, rf_id, dot_id)

ul_enableDataOutPut        = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_enableDataOutPut_id, rf_id, dot_id)

ul_disEnableDataOutPut     = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_disEnableDataOutPut_id, rf_id, dot_id)

ul_resetYaw2zero           = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_resetYaw2zero_id, rf_id, dot_id)

ul_enableSimulateCalibration   = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_enableSimulateCalibration_id, rf_id, dot_id)

ul_disableSimulateCalibration  = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_disableSimulateCalibration_id, rf_id, dot_id)

ul_configSimulateCalibrationMode = \
    lambda fmt, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_configSimulateCalibrationMode_id, rf_id, dot_id, fmt)

# -------------------------------------------------------------
# 通用工具：申请默认帧缓存
# -------------------------------------------------------------

# ---------- 1. LED 交互 ----------
_lib.ul_enterLedInteraction_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_enterLedInteraction_id.restype = c_int16

_lib.ul_exitLedInteraction_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_exitLedInteraction_id.restype = c_int16

_lib.ul_modifyLedInteractionColor_id.argtypes = [c_uint8, c_uint8, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_modifyLedInteractionColor_id.restype = c_int16

_lib.ul_getLedInteractionColor_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_getLedInteractionColor_id.restype = c_int16

ul_enterLedInteraction = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_enterLedInteraction_id, rf_id, dot_id)

ul_exitLedInteraction = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_exitLedInteraction_id, rf_id, dot_id)

ul_modifyLedInteractionColor = \
    lambda color, mode, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_modifyLedInteractionColor_id, rf_id, dot_id, color, mode)

ul_getLedInteractionColor = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_getLedInteractionColor_id, rf_id, dot_id)

# ---------- 2. 串口波特率 ----------
_lib.ul_modifyUartBaudRate_id.argtypes = [c_uint32, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_modifyUartBaudRate_id.restype = c_int16

_lib.ul_getUartBaudRate_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_getUartBaudRate_id.restype = c_int16

ul_modifyUartBaudRate = \
    lambda baud, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_modifyUartBaudRate_id, rf_id, dot_id, baud)

ul_getUartBaudRate = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_getUartBaudRate_id, rf_id, dot_id)

# ---------- 3. BlockSize ----------
_lib.ul_modifyBlockSize_id.argtypes = [c_uint8, c_uint8, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_modifyBlockSize_id.restype = c_int16

_lib.ul_getBlockSize_id.argtypes = [c_uint8, c_int8, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]  # C 原型为 int8_t
_lib.ul_getBlockSize_id.restype = c_int16

ul_modifyBlockSize = \
    lambda type_, size, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_modifyBlockSize_id, rf_id, dot_id, type_, size)

ul_getBlockSize = \
    lambda type_, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_getBlockSize_id, rf_id, dot_id, type_)

# ---------- 4. IMU 六面静态校准 ----------
_lib.ul_imuStaticCalibrationInit_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_imuStaticCalibrationInit_id.restype = c_int16

_lib.ul_imuStaticCalibration_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_imuStaticCalibration_id.restype = c_int16

_lib.ul_imuStaticCalibrationExit_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_imuStaticCalibrationExit_id.restype = c_int16

_lib.ul_clearStaticCalibrationParam_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_clearStaticCalibrationParam_id.restype = c_int16

ul_imuStaticCalibrationInit = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_imuStaticCalibrationInit_id, rf_id, dot_id)

ul_imuStaticCalibration = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_imuStaticCalibration_id, rf_id, dot_id)

ul_imuStaticCalibrationExit = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_imuStaticCalibrationExit_id, rf_id, dot_id)

ul_clearStaticCalibrationParam = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_clearStaticCalibrationParam_id, rf_id, dot_id)

# ---------- 5. 设备信息 & 控制 ----------
_lib.ul_getMacAddressStr_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_getMacAddressStr_id.restype = c_int16

_lib.ul_getDeviceSnStr_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_getDeviceSnStr_id.restype = c_int16

_lib.ul_getBoardVesionStr_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_getBoardVesionStr_id.restype = c_int16

_lib.ul_getFirmwareVesionStr_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_getFirmwareVesionStr_id.restype = c_int16

_lib.ul_deviceShutdown_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_deviceShutdown_id.restype = c_int16

_lib.ul_restoreFactorySettings_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.ul_restoreFactorySettings_id.restype = c_int16

ul_getMacAddressStr        = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_getMacAddressStr_id, rf_id, dot_id)

ul_getDeviceSnStr          = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_getDeviceSnStr_id, rf_id, dot_id)

ul_getBoardVesionStr       = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_getBoardVesionStr_id, rf_id, dot_id)

ul_getFirmwareVesionStr    = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_getFirmwareVesionStr_id, rf_id, dot_id)

ul_deviceShutdown          = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_deviceShutdown_id, rf_id, dot_id)

ul_restoreFactorySettings  = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.ul_restoreFactorySettings_id, rf_id, dot_id)

#------------------------------------------------------------------------------------------------
# UHL 高级指令
#------------------------------------------------------------------------------------------------
# -------------------------------------------------------------
# 高级设置：hl_ 系列接口
# -------------------------------------------------------------
_lib.hl_modifyDataFormat_id.argtypes = [c_uint32, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_modifyDataFormat_id.restype = c_int16

_lib.hl_modifyDataFormatNotSave_id.argtypes = [c_uint32, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_modifyDataFormatNotSave_id.restype = c_int16

_lib.hl_getDataFormat_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_getDataFormat_id.restype = c_int16

_lib.hl_modifyDotId_id.argtypes = [c_uint8, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_modifyDotId_id.restype = c_int16

_lib.hl_getDotId_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_getDotId_id.restype = c_int16

# ---------- 对外函数 ----------
hl_modifyDataFormat = \
    lambda fmt, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_modifyDataFormat_id, rf_id, dot_id, fmt)

hl_modifyDataFormatNotSave = \
    lambda fmt, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_modifyDataFormatNotSave_id, rf_id, dot_id, fmt)

hl_getDataFormat = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_getDataFormat_id, rf_id, dot_id)

hl_modifyDotId = \
    lambda dot_id_cfg, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_modifyDotId_id, rf_id, dot_id, dot_id_cfg)

hl_getDotId = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_getDotId_id, rf_id, dot_id)

# -------------------------------------------------------------
# 高级设置：RF 连接间隔 / ACC 量程 / Gyro 量程
# -------------------------------------------------------------
# ---------- 1. Rf ConnInterval ----------
_lib.hl_modifyRfConnInterval_id.argtypes = [c_float, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_modifyRfConnInterval_id.restype = c_int16

_lib.hl_getRfConnInterval_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_getRfConnInterval_id.restype = c_int16

# ---------- 对外函数 ----------
hl_modifyRfConnInterval = \
    lambda interval, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_modifyRfConnInterval_id, rf_id, dot_id, interval)

hl_getRfConnInterval = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_getRfConnInterval_id, rf_id, dot_id)

# ---------- 2. ACC Range ----------
_lib.hl_modifyAccRange_id.argtypes = [c_uint8, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_modifyAccRange_id.restype = c_int16

_lib.hl_getAccRange_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_getAccRange_id.restype = c_int16

# ---------- 对外函数 ----------
hl_modifyAccRange = \
    lambda acc_range, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_modifyAccRange_id, rf_id, dot_id, acc_range)

hl_getAccRange = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_getAccRange_id, rf_id, dot_id)

# ---------- 3. Gyro Range ----------
_lib.hl_modifyGyroRange_id.argtypes = [c_uint8, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_modifyGyroRange_id.restype = c_int16

_lib.hl_getGyroRange_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_getGyroRange_id.restype = c_int16

# ---------- 对外函数 ----------
hl_modifyGyroRange = \
    lambda gyro_range, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_modifyGyroRange_id, rf_id, dot_id, gyro_range)

hl_getGyroRange = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_getGyroRange_id, rf_id, dot_id)

# -------------------------------------------------------------
# 高级设置：剩余全部接口一次性封装
# -------------------------------------------------------------
# 1. 磁力计椭球拟合校准
_lib.hl_modifyMagCalParam_Ex_id.argtypes = [POINTER(MagEllipsoidCalParamBlock_t),c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_modifyMagCalParam_Ex_id.restype = c_int16

_lib.hl_getMagCalParam_Ex_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_getMagCalParam_Ex_id.restype = c_int16

# ---------- 对外函数 ----------
hl_modifyMagCalParam_Ex = \
    lambda cal, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_modifyMagCalParam_Ex_id, rf_id, dot_id, cal)

hl_getMagCalParam_Ex = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_getMagCalParam_Ex_id, rf_id, dot_id)

# 2. 清除/配置/读取 VQF Gyro Bias
_lib.hl_clearGyroBias_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_clearGyroBias_id.restype = c_int16

# ---------- 对外函数 ----------
hl_clearGyroBias = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_clearGyroBias_id, rf_id, dot_id)

# 3. 流水号格式 / 重置流水号
_lib.hl_configFlowFormat_id.argtypes = [c_uint8, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_configFlowFormat_id.restype = c_int16

_lib.hl_getFlowFormat_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_getFlowFormat_id.restype = c_int16

_lib.hl_resetFlowNums_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_resetFlowNums_id.restype = c_int16

# ---------- 对外函数 ----------
hl_configFlowFormat = \
    lambda fmt, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_configFlowFormat_id, rf_id, dot_id, fmt)

hl_getFlowFormat = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_getFlowFormat_id, rf_id, dot_id)

hl_resetFlowNums = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_resetFlowNums_id, rf_id, dot_id)

# 4. 姿态纠正
_lib.hl_disable_ahrs_offset_cal_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_disable_ahrs_offset_cal_id.restype = c_int16

_lib.hl_set_ahrs_offset_param_id.argtypes = [POINTER(AhrsQuaternion), c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_set_ahrs_offset_param_id.restype = c_int16

_lib.hl_get_ahrs_offset_param_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_get_ahrs_offset_param_id.restype = c_int16

# ---------- 对外函数 ----------
hl_disable_ahrs_offset_cal = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_disable_ahrs_offset_cal_id, rf_id, dot_id)

hl_set_ahrs_offset_param = \
    lambda quat, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_set_ahrs_offset_param_id, rf_id, dot_id, quat)

hl_get_ahrs_offset_param = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_get_ahrs_offset_param_id, rf_id, dot_id)

# 5. 数据输出端口
_lib.hl_configOutDataPort_id.argtypes = [c_uint16, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_configOutDataPort_id.restype = c_int16

_lib.hl_getOutDataPort_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_getOutDataPort_id.restype = c_int16

_lib.hl_checkOutDataPort_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_checkOutDataPort_id.restype = c_int16

# ---------- 对外函数 ----------
hl_configOutDataPort = \
    lambda port, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_configOutDataPort_id, rf_id, dot_id, port)

hl_getOutDataPort = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_getOutDataPort_id, rf_id, dot_id)

hl_checkOutDataPort = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_checkOutDataPort_id, rf_id, dot_id)

# ---------- 6. 机器状态码 ----------
_lib.hl_getMachineStatus_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_getMachineStatus_id.restype = c_int16

# ---------- 对外函数 ----------
hl_getMachineStatus = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_getMachineStatus_id, rf_id, dot_id)

# ---------- 7. 手指 ANT 滤波参数 ----------
_lib.hl_configFingerFilterParam_id.argtypes = [POINTER(AntFilterParam_t), c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_configFingerFilterParam_id.restype = c_int16

_lib.hl_getFilterParam_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_getFilterParam_id.restype = c_int16

# ---------- 对外函数 ----------
hl_configFingerFilterParam = \
    lambda param, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_configFingerFilterParam_id, rf_id, dot_id, byref(param))

hl_getFilterParam = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_getFilterParam_id, rf_id, dot_id)

# ---------- 8. 手指 Map ----------
_lib.hl_setFingerMap_id.argtypes = [c_uint8, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_setFingerMap_id.restype = c_int16

_lib.hl_getFingerMap_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_getFingerMap_id.restype = c_int16

# ---------- 对外函数 ----------
hl_setFingerMap = \
    lambda map_, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_setFingerMap_id, rf_id, dot_id, map_)

hl_getFingerMap = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_getFingerMap_id, rf_id, dot_id)

# ---------- 9. 通用开关封装 ----------
_lib.hl_swapUserUartTrxPin_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_swapUserUartTrxPin_id.restype = c_int16

hl_swapUserUartTrxPin = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_swapUserUartTrxPin_id, rf_id, dot_id)

_lib.hl_enableUserSpim_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_enableUserSpim_id.restype = c_int16

hl_enableUserSpim = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_enableUserSpim_id, rf_id, dot_id)

_lib.hl_disableUserSpim_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_disableUserSpim_id.restype = c_int16

hl_disableUserSpim = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_disableUserSpim_id, rf_id, dot_id)

_lib.hl_enableUserSpis_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_enableUserSpis_id.restype = c_int16

hl_enableUserSpis = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_enableUserSpis_id, rf_id, dot_id)

_lib.hl_disableUserSpis_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_disableUserSpis_id.restype = c_int16

hl_disableUserSpis = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_disableUserSpis_id, rf_id, dot_id)

_lib.hl_configUserAnt_id.argtypes = [c_uint8, c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_configUserAnt_id.restype = c_int16

hl_configUserAnt = \
    lambda mask, rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_configUserAnt_id, rf_id, dot_id, mask)

_lib.hl_enableUserBattery_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_enableUserBattery_id.restype = c_int16

hl_enableUserBattery = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_enableUserBattery_id, rf_id, dot_id)

_lib.hl_disableUserBattery_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_disableUserBattery_id.restype = c_int16

hl_disableUserBattery = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_disableUserBattery_id, rf_id, dot_id)

_lib.hl_enableUserRgbLed_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_enableUserRgbLed_id.restype = c_int16

hl_enableUserRgbLed = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_enableUserRgbLed_id, rf_id, dot_id)

_lib.hl_disableUserRgbLed_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_disableUserRgbLed_id.restype = c_int16

hl_disableUserRgbLed = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_disableUserRgbLed_id, rf_id, dot_id)

_lib.hl_enableUserBtn_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_enableUserBtn_id.restype = c_int16

hl_enableUserBtn = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_enableUserBtn_id, rf_id, dot_id)

_lib.hl_disableUserBtn_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_disableUserBtn_id.restype = c_int16

hl_disableUserBtn = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_disableUserBtn_id, rf_id, dot_id)

_lib.hl_enableUserPowerEn_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_enableUserPowerEn_id.restype = c_int16

hl_enableUserPowerEn = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_enableUserPowerEn_id, rf_id, dot_id)

_lib.hl_disableUserPowerEn_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_disableUserPowerEn_id.restype = c_int16

hl_disableUserPowerEn = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_disableUserPowerEn_id, rf_id, dot_id)

_lib.hl_enableUserRf_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_enableUserRf_id.restype = c_int16

hl_enableUserRf = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_enableUserRf_id, rf_id, dot_id)

_lib.hl_enableUserRfPa_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_enableUserRfPa_id.restype = c_int16

hl_enableUserRfPa = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_enableUserRfPa_id, rf_id, dot_id)

_lib.hl_disableUserRfPa_id.argtypes = [c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.hl_disableUserRfPa_id.restype = c_int16

hl_disableUserRfPa = \
    lambda rf_id = DEFAULT_RFID, dot_id = DEFAULT_DOTID: _call_cmd(_M_ID, _lib.hl_disableUserRfPa_id, rf_id, dot_id)

#------------------------------------------------------------------------------------------------
# FHL 高级指令
#------------------------------------------------------------------------------------------------

#------------------------------------------------------------------------------------------------
# OTA 升级接口
#------------------------------------------------------------------------------------------------

#------------------------------------------------------------------------------------------------
# Dongle 系列接口 UDG_LEVEL_EN
#------------------------------------------------------------------------------------------------
_lib.dl_getDeviceFullSnId_id.argtypes = [c_uint8, POINTER(c_uint8), c_uint16]
_lib.dl_getDeviceFullSnId_id.restype = c_int16

dl_getDeviceFullSnId = \
    lambda rf_id = DEFAULT_DONGLEID: _call_cmd(_S_ID, _lib.dl_getDeviceFullSnId_id, rf_id, None)

# 4. DeviceList（结构体数组）
_lib.dl_modifyDeviceList_id2.argtypes = [POINTER(DeviceBlock_t), c_uint8, c_uint8, POINTER(c_uint8), c_uint16]
_lib.dl_modifyDeviceList_id2.restype = c_int16

dl_modifyDeviceList = \
    lambda blocks, nums, rf_id = DEFAULT_DONGLEID: _call_cmd(_S_ID_MAX, _lib.dl_modifyDeviceList_id2, rf_id, None, cast(blocks, POINTER(DeviceBlock_t)), nums)

_lib.dl_getBoardVesionStr_id.argtypes = [c_uint8, POINTER(c_uint8), c_uint16]
_lib.dl_getBoardVesionStr_id.restype = c_int16

dl_getBoardVesionStr = \
    lambda rf_id = DEFAULT_DONGLEID: _call_cmd(_S_ID, _lib.dl_getBoardVesionStr_id, rf_id, None)

_lib.dl_getFirmwareVesionStr_id.argtypes = [c_uint8, POINTER(c_uint8), c_uint16]
_lib.dl_getFirmwareVesionStr_id.restype = c_int16

dl_getFirmwareVesionStr = \
    lambda rf_id = DEFAULT_DONGLEID: _call_cmd(_S_ID, _lib.dl_getFirmwareVesionStr_id, rf_id, None)

_lib.dl_getDeviceList_id.argtypes = [c_uint8, POINTER(c_uint8), c_uint16]
_lib.dl_getDeviceList_id.restype = c_int16

dl_getDeviceList = \
    lambda rf_id = DEFAULT_DONGLEID: _call_cmd(_S_ID, _lib.dl_getDeviceList_id, rf_id, None)

_lib.dl_clearDeviceList_id.argtypes = [c_uint8, POINTER(c_uint8), c_uint16]
_lib.dl_clearDeviceList_id.restype = c_int16

dl_clearDeviceList = \
    lambda rf_id = DEFAULT_DONGLEID: _call_cmd(_S_ID, _lib.dl_clearDeviceList_id, rf_id, None)

_lib.dl_getDeviceConnList_id.argtypes = [c_uint8, POINTER(c_uint8), c_uint16]
_lib.dl_getDeviceConnList_id.restype = c_int16

dl_getDeviceConnList = \
    lambda rf_id = DEFAULT_DONGLEID: _call_cmd(_S_ID, _lib.dl_getDeviceConnList_id, rf_id, None)

_lib.dl_keepDeviceConnList_id.argtypes = [c_uint8, POINTER(c_uint8), c_uint16]
_lib.dl_keepDeviceConnList_id.restype = c_int16

dl_keepDeviceConnList = \
    lambda rf_id = DEFAULT_DONGLEID: _call_cmd(_S_ID, _lib.dl_keepDeviceConnList_id, rf_id, None)

_lib.dl_enableScan_id.argtypes = [c_uint8, POINTER(c_uint8), c_uint16]
_lib.dl_enableScan_id.restype = c_int16

dl_enableScan = \
    lambda rf_id = DEFAULT_DONGLEID: _call_cmd(_S_ID, _lib.dl_enableScan_id, rf_id, None)

_lib.dl_disEnableScan_id.argtypes = [c_uint8, POINTER(c_uint8), c_uint16]
_lib.dl_disEnableScan_id.restype = c_int16

dl_disEnableScan = \
    lambda rf_id = DEFAULT_DONGLEID: _call_cmd(_S_ID, _lib.dl_disEnableScan_id, rf_id, None)

_lib.dl_disConnectAll_id.argtypes = [c_uint8, POINTER(c_uint8), c_uint16]
_lib.dl_disConnectAll_id.restype = c_int16

dl_disConnectAll = \
    lambda rf_id = DEFAULT_DONGLEID: _call_cmd(_S_ID, _lib.dl_disConnectAll_id, rf_id, None)

_lib.dl_configIdentifyWay_id.argtypes = [c_bool, c_uint8, POINTER(c_uint8), c_uint16]
_lib.dl_configIdentifyWay_id.restype = c_int16

dl_configIdentifyWay = \
    lambda isMac, rf_id = DEFAULT_DONGLEID: _call_cmd(_S_ID, _lib.dl_configIdentifyWay_id, rf_id, None, c_bool(isMac))

_lib.dl_getIdentifyWay_id.argtypes = [c_uint8, POINTER(c_uint8), c_uint16]
_lib.dl_getIdentifyWay_id.restype = c_int16

dl_getIdentifyWay = \
    lambda rf_id = DEFAULT_DONGLEID: _call_cmd(_S_ID, _lib.dl_getIdentifyWay_id, rf_id, None)

_lib.dl_outputToXXX_id.argtypes = [c_bool, c_uint8, POINTER(c_uint8), c_uint16]
_lib.dl_outputToXXX_id.restype = c_int16

dl_outputToXXX = \
    lambda isUsb, rf_id = DEFAULT_DONGLEID: _call_cmd(_S_ID, _lib.dl_outputToXXX_id, rf_id, None, c_bool(isUsb))

_lib.dl_restoreFactorySettings_id.argtypes = [c_uint8, POINTER(c_uint8), c_uint16]
_lib.dl_restoreFactorySettings_id.restype = c_int16

dl_restoreFactorySettings = \
    lambda rf_id = DEFAULT_DONGLEID: _call_cmd(_S_ID, _lib.dl_restoreFactorySettings_id, rf_id, None)

_lib.dl_deviceShutdown_id.argtypes = [c_uint8, POINTER(c_uint8), c_uint16]
_lib.dl_deviceShutdown_id.restype = c_int16

dl_deviceShutdown = \
    lambda rf_id = DEFAULT_DONGLEID: _call_cmd(_S_ID, _lib.dl_deviceShutdown_id, rf_id, None)

#------------------------------------------------------------------------------------------------
# Dongle 系列接口 FDG_LEVEL_EN
#------------------------------------------------------------------------------------------------

#------------------------------------------------------------------------------------------------------------
