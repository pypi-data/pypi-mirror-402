"""
ZLBus Base Type Python Interface

This module provides Python encapsulations of the C structures defined in the zlbusBaseType.h header file.
"""

import ctypes
from ctypes import c_int16, c_float


class Axis3_I16(ctypes.Union):
    """3-axis int16 data structure"""
    class axis(ctypes.LittleEndianStructure):
        _fields_ = [
            ("x", c_int16),
            ("y", c_int16),
            ("z", c_int16),
        ]
    _fields_ = [
        ("array", c_int16 * 3),
        ("axis", axis),
    ]


class Axis3_Float(ctypes.Union):
    """3-axis float data structure"""
    class axis(ctypes.LittleEndianStructure):
        _fields_ = [
            ("x", c_float),
            ("y", c_float),
            ("z", c_float),
        ]
    _fields_ = [
        ("array", c_float * 3),
        ("axis", axis),
    ]


class AhrsQuaternion(ctypes.Union):
    """Quaternion data structure"""
    class element(ctypes.LittleEndianStructure):
        _fields_ = [
            ("w", c_float),
            ("x", c_float),
            ("y", c_float),
            ("z", c_float),
        ]
    _fields_ = [
        ("array", c_float * 4),
        ("element", element),
    ]


class AhrsEuler(ctypes.Union):
    """Euler angles data structure"""
    class angle(ctypes.LittleEndianStructure):
        _fields_ = [
            ("roll", c_float),
            ("pitch", c_float),
            ("yaw", c_float),
        ]
    _fields_ = [
        ("array", c_float * 3),
        ("angle", angle),
    ]

class AntValue_I16(ctypes.LittleEndianStructure):
    """Antenna value int16 data structure"""
    class ant(ctypes.LittleEndianStructure):
        _fields_ = [
            ("thumbFinger", c_int16),
            ("indexFinger", c_int16),
            ("middleFinger", c_int16),
            ("ringFinger", c_int16),
            ("pinkyFinger", c_int16),
            ("otherFinger", c_int16),
        ]
    _fields_ = [
        ("array", c_int16 * 6),
        ("ant", ant),
    ]


class Axis3_ScaleDpsBlock(ctypes.LittleEndianStructure):
    """3-axis scale dps block data structure"""
    _fields_ = [
        ("Kxyz", Axis3_Float),
        ("Bxyz", Axis3_Float),
        ("Txyz", Axis3_Float),
    ]


class CalImuTempeCheckBlockNoRule(ctypes.LittleEndianStructure):
    """Cal IMU temperature check block no rule data structure"""
    _fields_ = [
        ("kk", Axis3_ScaleDpsBlock * 6),
    ]
