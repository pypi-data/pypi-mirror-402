import winreg

SUB_KEY_KEYBOARD_LAYOUT = "SYSTEM\CurrentControlSet\Control\Keyboard Layout"

type_dict = {
    winreg.REG_BINARY: "Binary",
    winreg.REG_SZ: "String",
    winreg.REG_EXPAND_SZ: "Expandable String",
    winreg.REG_DWORD: "DWORD (32-bit number)",
    winreg.REG_MULTI_SZ: "Multi-String",
    winreg.REG_QWORD: "QWORD (64-bit number)",
}


def read_key_for_current_user(sub_key: str, name: str):
    hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key, 0, winreg.KEY_READ)
    return winreg.QueryValueEx(hkey, name)


def get_keyboard_scancode_map():
    hkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, SUB_KEY_KEYBOARD_LAYOUT, 0, winreg.KEY_READ)
    value, type_id = winreg.QueryValueEx(hkey, "Scancode Map")
    print(type_id)
    print(value[0])
