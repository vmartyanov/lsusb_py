from ctypes import *

#64-bit only
DWORD     = c_ulong
ULONG_PTR = POINTER(c_ulong)

#taken from https://github.com/jleben/python-serial/blob/master/examples/scanwin32.py

class GUID(Structure):
    _fields_ = [
        ('Data1', c_ulong),
        ('Data2', c_ushort),
        ('Data3', c_ushort),
        ('Data4', c_ubyte*8),
    ]
    
class SP_DEVICE_INTERFACE_DATA(Structure):
    _fields_ = [
        ('cbSize', DWORD),
        ('InterfaceClassGuid', GUID),
        ('Flags', DWORD),
        ('Reserved', ULONG_PTR),
    ]

class SP_DEVINFO_DATA(Structure):
    _fields_ = [
        ('cbSize', DWORD),
        ('ClassGuid', GUID),
        ('DevInst', DWORD),
        ('Reserved', ULONG_PTR),
    ]