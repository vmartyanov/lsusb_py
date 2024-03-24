"""Script to list USB devices and track list modifications."""
import sys
import time

from ctypes import *

from defines import *

SetupAPI = WinDLL('SetupAPI', use_last_error=True)

def usage() -> None:
    """Print usage information."""
    print("Usage: lsusb.py [track]")

def print_devices(vidpids: list[tuple[int, int]]) -> None:
    """PPrint devices list"""
    for vid, pid in vidpids:
        print (f"{vid:04x}:{pid:04x}")

def print_diff(old: list[tuple[int, int]], new: list[tuple[int, int]]) -> None:
    """Print diff between device lists"""
    added = []
    removed = []

    for dev in old:
        if not dev in new:
            removed.append(dev)

    for dev in new:
        if not dev in old:
            added.append(dev)

    if added:
        print ("Added devices:")
        print_devices(added)
    if removed:
        print ("Removed devices:")
        print_devices(removed)

def extract_ids(path: str) -> tuple[int, int]:
    """Extract VID and PID from device path."""
    vid_pos = path.find("vid_")
    pid_pos = path.find("pid_")

    if vid_pos == -1 or pid_pos == -1:
        return (0, 0)
    vid = int(path[vid_pos + 4 : vid_pos + 8], 0x10)
    pid = int(path[pid_pos + 4 : pid_pos + 8], 0x10)
    return (vid, pid)

def get_dev_list() -> list[tuple[int, int]]:
    """Get device VID:PID list"""
    ret: list[tuple[int, int]] = []
    guid = GUID(0xA5DCBF10, 0x6530, 0x11D2, (c_ubyte * 8)(0x90, 0x1F, 0x00, 0xC0, 0x4F, 0xB9, 0x51, 0xED))
    index = 0
    size = DWORD(0)
    intf_data = SP_DEVICE_INTERFACE_DATA()
    intf_data.cbSize = sizeof(SP_DEVICE_INTERFACE_DATA)

    dev_info = SP_DEVINFO_DATA()
    dev_info.cbSize = sizeof(SP_DEVINFO_DATA)

    SetupAPI.SetupDiGetClassDevsW.restype = c_void_p
    SetupAPI.SetupDiGetClassDevsW.argtypes = [POINTER(GUID), c_void_p, c_void_p, DWORD]
    h_devs = SetupAPI.SetupDiGetClassDevsW(byref(guid), None, None, 0x12)   #DIGCF_DEVICEINTERFACE | DIGCF_PRESENT
    if not h_devs:
        print (f"Error in SetupDiGetClassDevsW, error code 0x{get_last_error():x}")
        return ret

    while True:
        SetupAPI.SetupDiEnumDeviceInterfaces.argtypes = [
            c_void_p,
            POINTER(SP_DEVINFO_DATA),
            POINTER(GUID),
            DWORD,
            POINTER(SP_DEVICE_INTERFACE_DATA)
        ]
        status = SetupAPI.SetupDiEnumDeviceInterfaces(h_devs, None, byref(guid), index, byref(intf_data))
        if not status:
            error_code = get_last_error()
            if error_code != 0x103:     #ERROR_NO_MORE_ITEMS
                print (f"Error in SetupDiEnumDeviceInterfaces, error code 0x{error_code:x}")
            break

        SetupAPI.SetupDiGetDeviceInterfaceDetailW.argtypes = [
            c_void_p,
            POINTER(SP_DEVICE_INTERFACE_DATA),
            c_void_p,
            DWORD,
            POINTER(DWORD),
            POINTER(SP_DEVINFO_DATA)
        ]

        SetupAPI.SetupDiGetDeviceInterfaceDetailW(h_devs, byref(intf_data), None, 0, byref(size), None)
        class INTF_DETAIL(Structure):
            """Inline class for storing device details. Size is defined in runtime"""
            _fields_ = [
                ('cbSize', DWORD),
                ('DevicePath', c_wchar * size.value),
            ]

        details = INTF_DETAIL()
        details.cbSize = 8      #size of DWORD and 1-char buffer
        if not SetupAPI.SetupDiGetDeviceInterfaceDetailW(h_devs, byref(intf_data), byref(details), sizeof(details), byref(size), None):
            print (f"Error in SetupDiGetDeviceInterfaceDetailW_2, error code 0x{get_last_error():x}")
            break

        ret.append(extract_ids(details.DevicePath))

        index += 1

    SetupAPI.SetupDiDestroyDeviceInfoList.argtypes = [c_void_p]
    SetupAPI.SetupDiDestroyDeviceInfoList(h_devs)
    return ret

def main() -> None:
    """Main function."""
    mode = "list"
    if len(sys.argv) > 2:
        usage()
        return
    if len(sys.argv) == 2:
        if sys.argv[1] == "track":
            mode = "track"
        else:
            usage()
            return

    prev_list = get_dev_list()

    print ("Installed devices:")
    print_devices(prev_list)

    if mode == "track":
        print ("")
        while True:
            new_list = get_dev_list()
            if new_list != prev_list:
                print_diff(prev_list, new_list)
                print ("")
                prev_list = new_list
            time.sleep(0.1)

if __name__ == "__main__":
    main()
