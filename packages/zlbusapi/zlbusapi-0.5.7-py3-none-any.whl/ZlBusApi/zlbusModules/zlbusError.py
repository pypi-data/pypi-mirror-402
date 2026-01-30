# -*- coding: utf-8 -*-
"""
TKxx 错误码常量（保持与原 C 宏及注释一一对应）
"""

TKxx_SUCCESS      = 0                   # /* 成功           success */
TKxx_ERR_FAILED   = TKxx_SUCCESS - 1    # /* 失败           failed */
TKxx_ERR_READY    = TKxx_SUCCESS - 2    # /* 未准备好        Not ready */
TKxx_ERR_MEM      = TKxx_SUCCESS - 3    # /* 内存不足        Out of memory */
TKxx_ERR_MAX_SIZE = TKxx_SUCCESS - 4    # /* 超限制 */
TKxx_ERR_INTERN   = TKxx_SUCCESS - 5    # /* 内部错误        Internal error */
TKxx_ERR_BUSY     = TKxx_SUCCESS - 6    # /* 设备或资源繁忙   Device or resource busy */
TKxx_ERR_ALREADY  = TKxx_SUCCESS - 7    # /* 操作已在进行中   Operation already in progress */
TKxx_ERR_VAL      = TKxx_SUCCESS - 8    # /* 无效的参数      Invalid argument */
TKxx_ERR_NULL     = TKxx_SUCCESS - 9    # /* 空指针 */
TKxx_ERR_TIMEOUT  = TKxx_SUCCESS - 10   # /* 超时 */
TKxx_ERR_NONE     = TKxx_SUCCESS - 11   # /* 无数据等 */

