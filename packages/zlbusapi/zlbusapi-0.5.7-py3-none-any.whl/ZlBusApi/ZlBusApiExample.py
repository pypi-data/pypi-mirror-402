#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ZLBus Python SDK 示例代码
========================

本示例展示了如何使用ZLBus Python SDK进行基本操作。
"""
import ZlBusApi as zlapi
import ctypes

def example_basic_usage():
    """基本使用示例"""
    print("=== ZLBus Python SDK 基本使用示例 ===")
    
    # 1. 使用校验和函数
    data = b'\x01\x02\x03\x04'
    # checksum = zlapi.zl_checkSum8_compute(data, len(data))
    # print(f"1 数据 {data.hex(' ').upper()} 的校验和: {hex(checksum).upper()}")

    checkXor = zlapi.zl_checkXor8_compute(data, len(data))
    print(f"1 数据 {data.hex(' ').upper()} 的校验和: {hex(checkXor).upper()}")
    
    # 2. 使用CRC函数
    crc = zlapi.zl_crc16_compute(data, len(data))
    print(f"2 数据 {data.hex(' ').upper()} 的CRC16: {hex(crc).upper()}")
    
    # 3. 使用数据格式修改函数
    # 注意：实际使用时需要提供正确的参数
    # 这里只是展示函数调用方式，实际使用时需要根据具体需求提供参数
    # 缺省参数(rf_id, dot_id)
    result = zlapi.ul_modifyDataFormat(zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_RPY)
    print(f"3 缺省参数(rf_id, dot_id)，修改数据格式结果: {len(result)} | {result.hex(' ').upper()}")

    # 4. 使用数据格式修改函数
    # 输入参数：rf_id = 0x21, dot_id = 0x01
    result = zlapi.ul_modifyDataFormat(zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_RPY, rf_id = 0x21, dot_id = 0x01)
    print(f"4 输入参数(rf_id, dot_id)，修改数据格式结果: {len(result)} | {result.hex(' ').upper()}")


def example_device_operations():
    """设备操作示例"""
    print("\n=== ZLBus Python SDK 设备操作示例 ===")
    
    # 1. 创建设备块列表
    print(f"1 创建DeviceBlock_t实例:")
    block = zlapi.DeviceBlock_t()

    # 赋0，初始化
    ctypes.memset(ctypes.addressof(block), 0, ctypes.sizeof(block))

    # 赋值
    block.devId = 0x01
    block.connState = 0x01
    block.mac[:] = (ctypes.c_uint8 * 6)(0x11, 0x22, 0x33, 0x44, 0x55, 0x66)
    device_name = b"ZL25-00000000-0000"
    ctypes.memmove(ctypes.addressof(block.name), device_name, len(device_name))

    # 打印
    print("  block.mac =", bytes(block.mac).hex(' '))
    print("  block.name =", bytes(block.name).split(b'\0', 1)[0].decode('utf-8', errors='ignore'))

    
    
    # 2. 使用RF功率相关函数
    # 注意：实际使用时需要提供正确的参数
    # 这里只是展示函数调用方式，实际使用时需要根据具体需求提供参数
    #  缺省参数(rf_id, dot_id)
    rf_power = -4
    result = zlapi.ul_modifyIcRfPower(rf_power)
    print(f"2 缺省参数(rf_id, dot_id)，修改RF功率结果: {result.hex(' ').upper()}")

    # 3. 使用RF功率相关函数
    # 输入参数：rf_id = 0x21, dot_id = 0x01
    result = zlapi.ul_modifyIcRfPower(rf_power, rf_id = 0x21, dot_id = 0x01)
    print(f"3 输入参数(rf_id, dot_id)，修改RF功率结果: {len(result)} | {result.hex(' ').upper()}")


def example_decode():
    """解码示例"""
    print("\n=== ZLBus Python SDK 解码示例 ===")

    # 创建数据解码器句柄
    ddb = zlapi.ul_dataDecodeBlockCreate(tracker_nums = 1, user_id = 0xFF, max_nums = 20)

    # 待解码的数据，数据格式为：NEW_UPLOAD_DATA_TIME | NEW_UPLOAD_DATA_QUATERNION | NEW_UPLOAD_DATA_GYRO | NEW_UPLOAD_DATA_LIN_ACC
    data = [0xAA, 0x10, 0x30, 0x00, 0x02, 0x20, 0x00, 0x38, 0x06, 0xB6, 0xF9, 0x46, 
            0xFE, 0x41, 0x4E, 0x3F, 0xB3, 0x6F, 0xC6, 0xBB, 0xF0, 0x4E, 0x46, 0x3D, 
            0x1B, 0x1F, 0x17, 0xBF, 0x90, 0x46, 0x0A, 0xBF, 0x80, 0x24, 0x62, 0x3A, 
            0x38, 0x3C, 0x59, 0xBD, 0x00, 0x00, 0x00, 0xB2, 0x00, 0x00, 0x00, 0x32, 
            0x00, 0x00, 0x00, 0x34, 0x07, 0xAA, 0x10, 0x30, 0x00, 0x02, 0x20, 0x00, 
            0x39, 0x84, 0xDD, 0xF9, 0x46, 0x53, 0x42, 0x4E, 0x3F, 0x2A, 0x08, 0xC4, 
            0xBB, 0x7E, 0x03, 0x46, 0x3D, 0x18, 0x1F, 0x17, 0xBF, 0x62, 0x90, 0x85, 
            0x3F, 0xBC, 0x83, 0x15, 0xBE, 0xEC, 0xED, 0xA2, 0x3C, 0x00, 0x00, 0x80, 
            0xB2, 0x00, 0x00, 0x00, 0xB2, 0x00, 0x00, 0xA0, 0x34, 0xE1, 0xAA, 0x10, 
            0x30, 0x00, 0x02, 0x20, 0x00, 0x3A, 0x98, 0x06, 0xFA, 0x46, 0x58, 0x42, 
            0x4E, 0x3F, 0x93, 0x7F, 0xC3, 0xBB, 0xC7, 0xFA, 0x45, 0x3D, 0x1D, 0x1F, 
            0x17, 0xBF, 0xA8, 0xF5, 0x1C, 0xBF, 0x2A, 0xF1, 0x95, 0x3D, 0x08, 0x3A, 
            0xA2, 0x3C, 0x00, 0x00, 0x00, 0xB2, 0x00, 0x00, 0x00, 0xB2, 0x00, 0x00, 
            0x00, 0x00, 0xD4, 0xAA, 0x10, 0x30, 0x00, 0x02, 0x20, 0x00, 0x3B, 0x15, 
            0x2E, 0xFA, 0x46, 0x5F, 0x42, 0x4E, 0x3F, 0xBD, 0xE2, 0xC3, 0xBB, 0xF9, 
            0x07, 0x46, 0x3D, 0x02, 0x1F, 0x17, 0xBF, 0xF3, 0xA2, 0xEF, 0x3E, 0x28, 
            0xF0, 0x14, 0xBE, 0xBB, 0x18, 0x5A, 0xBD, 0x00, 0x00, 0x00, 0xB2, 0x00, 
            0x00, 0x00, 0x32, 0x00, 0x00, 0x40, 0x34, 0x78]

    # 手动设置解码格式（data）
    """
    1、待解码的数据data为静态数据，数据格式需要使用zlapi.ul_manualModifyDataFormat手动设置 
    2、在实际的应用中，使用 zlapi.ul_getDataFormat 方法获取模块上传的数据，不需要
    zlapi.ul_manualModifyDataFormat手动进行设置数据解码格式
    3、zlapi.ul_getDataFormat返回值在使用ul_dataBlockDecode方法进行解码过程中，内部自动更
    新数据解码格式，所以不需要调用zlapi.ul_manualModifyDataFormat手动设置
    """
    zlapi.ul_manualModifyDataFormat(ddb, 0, zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_TIME | \
                                            zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_QUATERNION | \
                                            zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_GYRO | \
                                            zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_LIN_ACC)

    # 将收到的原始字节流送入解码器，解码后的数据节点追加到链表中。
    zlapi.ul_dataBlockDecode(ddb, bytes(data))

    # 有效节点个数
    note_size = zlapi.ul_dataBlockNoteSize(ddb)
    print('cur note_size =', note_size)

    # blockId
    blockId = zlapi.ul_dataBlockGetBlockID(ddb)
    print('blockId =', hex(blockId))

    blockId_map = {
        # e_BlockID
        zlapi.e_BlockID.BlockID_OK : (zlapi.ul_CtrlDataBaseBlock, ctypes.sizeof(zlapi.ul_CtrlDataBaseBlock)),
        zlapi.e_BlockID.BlockID_ERROR : (zlapi.ul_CtrlDataBaseBlock, ctypes.sizeof(zlapi.ul_CtrlDataBaseBlock)),

        # e_BlockID_DataExport
        zlapi.e_BlockID_DataExport.BlockID_00001000 : (zlapi.ul_ImuDataBlock, ctypes.sizeof(zlapi.ul_ImuDataBlock)),
        zlapi.e_BlockID_DataExport.BlockID_00001400 : (zlapi.ul_BatteryBlock, ctypes.sizeof(zlapi.ul_BatteryBlock)),
        zlapi.e_BlockID_DataExport.BlockID_00001500 : (zlapi.ul_AntValueBlock, ctypes.sizeof(zlapi.ul_AntValueBlock)),

        # e_BlockID_UL
        zlapi.e_BlockID_UL.BlockID_0000D501 : (zlapi.ul_UploadDataFormatBlock, ctypes.sizeof(zlapi.ul_UploadDataFormatBlock)),
        zlapi.e_BlockID_UL.BlockID_0000D503 : (zlapi.ul_SamplingHzBlock, ctypes.sizeof(zlapi.ul_SamplingHzBlock)),
        zlapi.e_BlockID_UL.BlockID_0000D505 : (zlapi.ul_UploadHzBlock, ctypes.sizeof(zlapi.ul_UploadHzBlock)),
        zlapi.e_BlockID_UL.BlockID_0000D50B : (zlapi.ul_FilterMapBlock, ctypes.sizeof(zlapi.ul_FilterMapBlock)),
        zlapi.e_BlockID_UL.BlockID_0000D50D : (zlapi.ul_IcDirBlock, ctypes.sizeof(zlapi.ul_IcDirBlock)),
        zlapi.e_BlockID_UL.BlockID_0000D50F : (zlapi.ul_DevieRfNameBlock, ctypes.sizeof(zlapi.ul_DevieRfNameBlock)),
        zlapi.e_BlockID_UL.BlockID_0000D511 : (zlapi.ul_RfPowerBlock, ctypes.sizeof(zlapi.ul_RfPowerBlock)),
        zlapi.e_BlockID_UL.BlockID_0000D563 : (zlapi.ul_RgbDataBlock, ctypes.sizeof(zlapi.ul_RgbDataBlock)),
        zlapi.e_BlockID_UL.BlockID_0000D565 : (zlapi.ul_UartBaudRateBlock, ctypes.sizeof(zlapi.ul_UartBaudRateBlock)),
        zlapi.e_BlockID_UL.BlockID_0000D567 : (zlapi.ul_BlockSizeBlock, ctypes.sizeof(zlapi.ul_BlockSizeBlock)),
        zlapi.e_BlockID_UL.BlockID_0000D577 : (zlapi.ul_DeviceMacBlock, ctypes.sizeof(zlapi.ul_DeviceMacBlock)),
        zlapi.e_BlockID_UL.BlockID_0000D579 : (zlapi.ul_DeviceSnFullStrBlock, ctypes.sizeof(zlapi.ul_DeviceSnFullStrBlock)),
        zlapi.e_BlockID_UL.BlockID_0000D57B : (zlapi.ul_DeviceBoardVersionBlock, ctypes.sizeof(zlapi.ul_DeviceBoardVersionBlock)),
        zlapi.e_BlockID_UL.BlockID_0000D57D : (zlapi.ul_DeviceFirmwareVersionBlock, ctypes.sizeof(zlapi.ul_DeviceFirmwareVersionBlock)),

        # e_BlockID_UHL
    }

    # block size 
    print('block size =', blockId_map[blockId][1])

    # 读取解码数据
    decode_data = zlapi.ul_dataBlockReadNote(ddb, blockId_map[blockId][1])
    block = blockId_map[blockId][0].from_buffer_copy(decode_data) # 关键：让 ctypes 做“类型转换”

    print('cmdId =', hex(block.pkId.cmdId))
    print('subCmdId =', hex(block.pkId.subCmdId))
    print('rfId =', hex(block.pkId.rfId))
    print('dotId =', hex(block.pkId.dotId))
    print('flowId =', hex(block.pkId.flowId))
    print('userId =', hex(block.pkId.userId))
    print('effectiveDataFormat =', hex(block.effectiveDataFormat))

    if block.effectiveDataFormat & (zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_TIME | zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_HL_TIME):
        print('timeStamp =', block.timeStamp)

    if block.effectiveDataFormat & zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_TEMP:
        print('temperature =', block.temperature)

    if block.effectiveDataFormat & zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_QUATERNION:
        print('quat =', block.quat.element.w, block.quat.element.x, block.quat.element.y, block.quat.element.z)

    if block.effectiveDataFormat & zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_RPY:
        print('euler =', block.euler.angle.roll, block.euler.angle.pitch, block.euler.angle.yaw)

    if block.effectiveDataFormat & zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_ACC:
        print('acc =', block.acc.axis.x, block.acc.axis.y, block.acc.axis.z)

    if block.effectiveDataFormat & zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_GYRO:
        print('gyro =', block.gyro.axis.x, block.gyro.axis.y, block.gyro.axis.z)

    if block.effectiveDataFormat & zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_MAG:
        print('mag =', block.mag.axis.x, block.mag.axis.y, block.mag.axis.z)

    if block.effectiveDataFormat & zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_LIN_ACC:
        print('lineAcc =', block.lineAcc.axis.x, block.lineAcc.axis.y, block.lineAcc.axis.z)

    print('\ncur note_size =', zlapi.ul_dataBlockNoteSize(ddb))

    zlapi.ul_dataBlockSkipNote(ddb) # 跳过数据
    print('cur note_size =', zlapi.ul_dataBlockNoteSize(ddb))

    zlapi.ul_dataBlockSkipNote(ddb) # 跳过数据
    print('cur note_size =', zlapi.ul_dataBlockNoteSize(ddb))

    zlapi.ul_dataBlockSkipNote(ddb) # 跳过数据
    print('cur note_size =', zlapi.ul_dataBlockNoteSize(ddb))

    # 销毁解码器句柄。
    zlapi.ul_dataDecodeBlockDelete(ddb)


def example():
    try:
        print()
        example_basic_usage()
        example_device_operations()
        print("\n所有示例执行完成。")
    except Exception as e:
        print(f"执行示例时出错: {e}")


if __name__ == "__main__":
    example()
    example_decode()

