import os
import sys
import ctypes

# 获取当前文件（ethernet_scanner_ctypes.py）所在目录的上一级目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dll_path = os.path.join(PROJECT_ROOT, "dll", "EthernetScanner.dll")

dll = ctypes.WinDLL(dll_path) if sys.platform == "win32" else ctypes.CDLL(dll_path)

# ====== 需要用到的宏定义 ======
ETHERNETSCANNER_SCANXMAX = 2048
ETHERNETSCANNER_PEAKSPERCMOSSCANLINEMAX = 4
BUFFLEN = ETHERNETSCANNER_SCANXMAX * ETHERNETSCANNER_PEAKSPERCMOSSCANLINEMAX  # 8192

# EthernetScanner_Connect
dll.EthernetScanner_Connect.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
dll.EthernetScanner_Connect.restype = ctypes.c_void_p

# EthernetScanner_ConnectEx
dll.EthernetScanner_ConnectEx.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
dll.EthernetScanner_ConnectEx.restype = None

# EthernetScanner_Disconnect
dll.EthernetScanner_Disconnect.argtypes = [ctypes.c_void_p]
dll.EthernetScanner_Disconnect.restype = ctypes.c_void_p

# EthernetScanner_GetConnectStatus
dll.EthernetScanner_GetConnectStatus.argtypes = [
    ctypes.c_void_p, ctypes.POINTER(ctypes.c_int),
]
dll.EthernetScanner_GetConnectStatus.restype = None

# EthernetScanner_GetXZIExtended
dll.EthernetScanner_GetXZIExtended.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_double),
    ctypes.POINTER(ctypes.c_double),
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int),
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_uint),
    ctypes.POINTER(ctypes.c_ubyte),
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_int),
]
dll.EthernetScanner_GetXZIExtended.restype = ctypes.c_int

# EthernetScanner_GetInfo
dll.EthernetScanner_GetInfo.argtypes = [
    ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
]
dll.EthernetScanner_GetInfo.restype = ctypes.c_int

# EthernetScanner_ResetDllFiFo
dll.EthernetScanner_ResetDllFiFo.argtypes = [ctypes.c_void_p]
dll.EthernetScanner_ResetDllFiFo.restype = ctypes.c_int

# EthernetScanner_GetDllFiFoState
dll.EthernetScanner_GetDllFiFoState.argtypes = [ctypes.c_void_p]
dll.EthernetScanner_GetDllFiFoState.restype = ctypes.c_int

# EthernetScanner_ReadData
dll.EthernetScanner_ReadData.argtypes = [
    ctypes.c_void_p,
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.c_int,
    ctypes.c_int,
]
dll.EthernetScanner_ReadData.restype = ctypes.c_int

# EthernetScanner_WriteData
dll.EthernetScanner_WriteData.argtypes = [
    ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int,
]
dll.EthernetScanner_WriteData.restype = ctypes.c_int

# EthernetScanner_GetVersion
dll.EthernetScanner_GetVersion.argtypes = [ctypes.c_char_p, ctypes.c_int]
dll.EthernetScanner_GetVersion.restype = ctypes.c_int

# EthernetScanner_GetImage
dll.EthernetScanner_GetImage.argtypes = [
    ctypes.c_void_p,              # 设备句柄
    ctypes.c_char_p,              # 图像buffer
    ctypes.c_int,                 # buffer长度
    ctypes.POINTER(ctypes.c_uint),# width
    ctypes.POINTER(ctypes.c_uint),# height
    ctypes.POINTER(ctypes.c_uint),# offsetX
    ctypes.POINTER(ctypes.c_uint),# offsetZ
    ctypes.POINTER(ctypes.c_uint),# stepX
    ctypes.POINTER(ctypes.c_uint),# stepZ
    ctypes.c_uint                 # timeout
]
dll.EthernetScanner_GetImage.restype = ctypes.c_int

# EthernetScanner_SetReadDataCallback
dll.EthernetScanner_SetReadDataCallback.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
dll.EthernetScanner_SetReadDataCallback.restype = None

# EthernetScanner_ConvertMmToPix
dll.EthernetScanner_ConvertMmToPix.argtypes = [
    ctypes.c_void_p,
    ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double,
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)
]
dll.EthernetScanner_ConvertMmToPix.restype = ctypes.c_int

# EthernetScanner_ConnectUDP
dll.EthernetScanner_ConnectUDP.argtypes = [
    ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
]
dll.EthernetScanner_ConnectUDP.restype = ctypes.c_void_p

# EthernetScanner_GetRangeImage
dll.EthernetScanner_GetRangeImage.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_ushort),
    ctypes.c_int,
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_bool),
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_uint)
]
dll.EthernetScanner_GetRangeImage.restype = ctypes.c_int