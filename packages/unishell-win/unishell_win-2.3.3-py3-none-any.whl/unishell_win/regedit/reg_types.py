import winreg
STRING = winreg.REG_SZ
STRINGS = winreg.REG_MULTI_SZ
PATH = winreg.REG_EXPAND_SZ
INTEGER = winreg.REG_DWORD
LONG_INT = winreg.REG_QWORD
BINARY = winreg.REG_BINARY
NONE = winreg.REG_NONE
INTEGER_BIG_ENDIAN = winreg.REG_DWORD_BIG_ENDIAN
LINK = winreg.REG_LINK
RESOURCES = winreg.REG_RESOURCE_LIST
FULL_RESOURCE_DESCRIPTOR = winreg.REG_FULL_RESOURCE_DESCRIPTOR
RESOURCE_REQUIREMENTS_LIST = winreg.REG_RESOURCE_REQUIREMENTS_LIST

_REG_TYPE_INT = {
    "STRING": STRING,
    "STRINGS": STRINGS,
    "PATH": PATH,
    "INTEGER": INTEGER, 
    "LONG_INT": LONG_INT, 
    "BINARY": BINARY, 
    "NONE": NONE,
    "INTEGER_BIG_ENDIAN": INTEGER_BIG_ENDIAN,
    "LINK": LINK,
    "RESOURCES": RESOURCES,
    "FULL_RESOURCE_DESCRIPTOR": FULL_RESOURCE_DESCRIPTOR,
    "RESOURCE_REQUIREMENTS_LIST": RESOURCE_REQUIREMENTS_LIST
}

_REG_TYPE_STR = {v: k for k, v in _REG_TYPE_INT.items()}


    
def _REG_TYPE_AUTO(value) -> int:
    """Detects registry type based on Python value"""
    if isinstance(value, int):
        if -2147483648 <= value <= 2147483647:
            return INTEGER
        else:
            return LONG_INT
    elif isinstance(value, bytes):
        return BINARY
    elif isinstance(value, list) and all(isinstance(x, str) for x in value):
        return STRINGS
    else:
        value = str(value)
        if "%" in value:
            return PATH
        else:
            return STRING  
_HKEY_INT = {
	"HKCU": winreg.HKEY_CURRENT_USER,
	"HKU":  winreg.HKEY_USERS,
	"HKLM": winreg.HKEY_LOCAL_MACHINE,
	"HKCC": winreg.HKEY_CURRENT_CONFIG,
	"HKCR": winreg.HKEY_CLASSES_ROOT,
	"HKDD": winreg.HKEY_DYN_DATA,
	"HKPD": winreg.HKEY_PERFORMANCE_DATA
}

_HKEY_STR = {v: k for k, v in _HKEY_INT.items()}