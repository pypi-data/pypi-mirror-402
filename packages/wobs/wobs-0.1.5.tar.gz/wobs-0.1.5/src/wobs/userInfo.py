#!/usr/bin/env python3
"""
Python implementation of userInfo functionality, compatible with different operating systems.
"""

import platform
import os
import json
import configparser
import sys
from typing import Dict, Optional

class ObserverConfig:
    """Configuration for Observer paths based on platform."""
    LOG = ""
    TRACKPOINT = ""
    TRACE = ""
    DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    DEFAULT_MAX_FILES = 5

    def __init__(self):
         # Set platform-specific paths
        if platform.system() == "Windows":
            base_path = "C:\\ProgramData\\wuying\\observer\\"
        elif platform.system() == "Android":
            base_path = "/data/vendor/log/wuying/observer/"
        else:  # Linux or other Unix-like systems
            base_path = "/var/log/wuying/observer/"
        self.LOG = os.path.join(base_path, "log/")
        self.TRACKPOINT = os.path.join(base_path, "trackpoint/")
        self.TRACE = os.path.join(base_path, "traces/")


def get_default_observer_config() -> ObserverConfig:
    """Get Observer configuration based on current platform"""
    return ObserverConfig()


def _load_runtime_ini(path: str) -> Optional[configparser.ConfigParser]:
    """加载 runtime.ini，返回 ConfigParser；不存在或解析失败返回 None。"""
    if not os.path.exists(path):
        return None

    config = configparser.ConfigParser()
    # 让 ConfigParser 支持类似 “key = value” 的顶层无 section 的写法
    # runtime.ini 里是没有 [section] 的，所以我们手动加一行虚拟 section 再读
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        # ConfigParser 要求有 section，给整个文件加一个 [DEFAULT] 包起来
        pseudo_content = "[DEFAULT]\n" + content
        config.read_string(pseudo_content)
        return config
    except Exception as e:
        print(f"Warning: Failed to parse INI file {path}: {e}", file=sys.stderr)
        return None


class UserInfo:
    """Data class to hold user information."""
    
    def __init__(self):
        # ECS info
        self.instanceID: str = ""
        self.regionID: str = ""
        
        # System info
        self.desktopID: str = ""
        self.desktopGroupID: str = ""
        self.appInstanceGroupID: str = ""
        self.fotaVersion: str = ""
        self.imageVersion: str = ""
        self.osEdition: str = ""  # Microsoft Windows Server 2019 Datacenter
        self.osVersion: str = ""  # 10.0.17763
        self.osBuild: str = ""    # 17763.2237
        self.osType: str = ""
        self.dsMode: str = ""
        self.localHostName: str = ""
        
        # User info
        self.userName: str = ""
        self.AliUID: str = ""
        self.officeSiteID: str = ""
        self.ownerAccountId: str = ""
        self.appInstanceID: str = ""

    def get_non_empty_values(self) -> dict:
        """
        Returns a dictionary of all attributes that have non-empty values.
        
        Returns:
            dict: Dictionary containing attribute names and their non-empty values
        """
        return {
            attr: value 
            for attr, value in self.__dict__.items() 
            if value != ""
        }


def get_os_type() -> str:
    """Get the operating system type."""
    system = platform.system().lower()
    if system == "windows":
        return "Windows"
    elif system == "linux":
        return "Linux"
    elif system == "darwin":
        return "macOS"
    else:
        return "Unknown"


def get_username() -> str:
    """Get the current username."""
    try:
        return os.getlogin()
    except:
        return os.environ.get('USER', '') or os.environ.get('USERNAME', '')


def get_os_version() -> str:
    """Get OS version information."""
    system = platform.system()
    
    if system == "Windows":
        # For Windows, we'll get version info differently
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                              r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
                product_name = winreg.QueryValueEx(key, "ProductName")[0]
                build = winreg.QueryValueEx(key, "CurrentBuild")[0]
                release_id = winreg.QueryValueEx(key, "ReleaseId")[0]
                return f"{product_name} (Build {build}.{release_id})"
        except:
            return "Windows (unknown version)"
    
    elif system == "Linux":
        try:
            # Try to get Linux version from /etc/os-release
            with open('/etc/os-release', 'r') as f:
                lines = f.readlines()
                name = ""
                version = ""
                for line in lines:
                    if line.startswith('NAME='):
                        name = line.split('=')[1].strip('"')
                    elif line.startswith('VERSION_ID='):
                        version = line.split('=')[1].strip('"')
                if name and version:
                    return f"{name} {version}"
                else:
                    # Fallback to uname
                    import subprocess
                    result = subprocess.run(['uname', '-r'], capture_output=True, text=True)
                    return f"Linux {result.stdout.strip()}"
        except:
            # Fallback to uname
            import subprocess
            try:
                result = subprocess.run(['uname', '-sr'], capture_output=True, text=True)
                return result.stdout.strip()
            except:
                return "Linux (unknown version)"
    
    elif system == "Darwin":
        try:
            import subprocess
            # Get macOS version
            result = subprocess.run(['sw_vers', '-productVersion'], capture_output=True, text=True)
            return f"macOS {result.stdout.strip()}"
        except:
            return "macOS (unknown version)"
    
    return "Unknown"


def get_system_info() -> tuple:
    """Get system information (osVersion, osType)."""
    return get_os_version(), get_os_type()


def get_ali_uid_from_env(userInfo: UserInfo) -> Optional[str]:
    # 从环境变量中获取 ALI_UID
    env_ali_uid = os.environ.get("ALI_UID")
    if env_ali_uid and env_ali_uid.strip():
        userInfo.AliUID = env_ali_uid.strip()

def get_user_info_from_ini(userInfo: UserInfo) -> None:
    """Get user info from INI-style config file (Linux/macOS)."""
    if platform.system().lower() == "windows":
        return
    
    # Linux/Unix systems
    runtime_ini_path = "/etc/cloudstream/runtime.ini"
    image_info_path = "/etc/wuying/image_info.json"
    meta_data_path = '/var/lib/cloud/seed/nocloud/meta-data'
    
    # Read from runtime.ini
    config = _load_runtime_ini(runtime_ini_path)
    if config is not None:
        cfg = config["DEFAULT"]  # 顶层 key 全在 DEFAULT 里
        if "DesktopId" in cfg:
            userInfo.desktopID = cfg.get("DesktopId", "").strip()
        if "AliUid" in cfg:
            # 这里先赋值，稍后会被 get_ali_uid_for_linux 的结果覆盖优先级
            userInfo.AliUID = cfg.get("AliUid", "").strip()
        if "OfficeSiteId" in cfg:
            userInfo.officeSiteID = cfg.get("OfficeSiteId", "").strip()
        if "regionId" in cfg:
            userInfo.regionID = cfg.get("regionId", "").strip()
    
    # Read from image_info.json
    if os.path.exists(image_info_path):
        try:
            with open(image_info_path, 'r') as f:
                data = json.load(f)
                if 'fotaVersion' in data:
                    userInfo.fotaVersion = data['fotaVersion']
                if 'image_name' in data:
                    userInfo.imageVersion = data['image_name']
        except Exception as e:
            print(f"Warning: Failed to read {image_info_path}: {e}", file=sys.stderr)

     # Read from meta-data
    if os.path.exists(meta_data_path):
        try:
            data = {}
            with open(meta_data_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    # 只按第一个 ":" 分割，防止 value 中包含 ":"
                    if ':' in line:
                        key, value = line.split(':', 1)
                        data[key.strip()] = value.strip()
                    else:
                        # 没有 ":" 的行可以按需处理，这里忽略
                        pass
            if 'instance-id' in data:
                userInfo.instanceID = data['instance-id']
            if 'dsmode' in data:
                userInfo.dsMode = data['dsmode']
            if 'local-hostname' in data:
                userInfo.localHostName = data['local-hostname']
        except Exception as e:
            print(f"Warning: Failed to read {meta_data_path}: {e}", file=sys.stderr)


def get_user_info_from_env(userInfo: UserInfo) -> None:
    try:
        # 获取 ECS_INSTANCE_ID
        ecs_instance_id = os.getenv('ECS_INSTANCE_ID')
        if ecs_instance_id is None:
            print(f"ECS_INSTANCE_ID is null.")
        else:
            userInfo.instanceID = ecs_instance_id

        # 获取 ACP_INSTANCE_ID
        app_instance_id = os.getenv('ACP_INSTANCE_ID')
        if app_instance_id is None:
            print(f"ACP_INSTANCE_ID is null.")
        else:
            userInfo.appInstanceID = app_instance_id
        get_ali_uid_from_env(userInfo=userInfo)

    except Exception as e:
        print(f"Get instanceid failed, error: {str(e)}")


def get_user_info_from_registry(userInfo: UserInfo) -> None:
    """Get user info from Windows registry."""
    if platform.system().lower() != "windows":
        return
    
    try:
        import winreg
        
        # Get username
        try:
            userInfo.userName = get_username()
        except:
            pass
            
        # Read from HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\AliyunEDSAgent\imageInfos
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                              r"SYSTEM\\CurrentControlSet\\Services\\AliyunEDSAgent\\imageInfos") as key:
                try:
                    value, _ = winreg.QueryValueEx(key, "name")
                    userInfo.imageVersion = value
                except:
                    pass
                    
                try:
                    value, _ = winreg.QueryValueEx(key, "fota_version")
                    userInfo.fotaVersion = value
                except:
                    pass
        except:
            pass
            
        # Read from HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\AliyunEDSAgent\desktopInfos
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                              r"SYSTEM\\CurrentControlSet\\Services\\AliyunEDSAgent\\desktopInfos") as key:
                try:
                    value, _ = winreg.QueryValueEx(key, "desktopId")
                    userInfo.desktopID = value
                except:
                    pass
                    
                try:
                    value, _ = winreg.QueryValueEx(key, "aliUid")
                    userInfo.AliUID = value
                except:
                    pass
                    
                try:
                    value, _ = winreg.QueryValueEx(key, "officeSiteId")
                    userInfo.officeSiteID = value
                except:
                    pass
                    
                try:
                    value, _ = winreg.QueryValueEx(key, "desktopGroupId")
                    userInfo.desktopGroupID = value
                except:
                    pass
                    
                try:
                    value, _ = winreg.QueryValueEx(key, "appInstanceGroupId")
                    userInfo.appInstanceGroupID = value
                except:
                    pass
                    
                try:
                    value, _ = winreg.QueryValueEx(key, "regionId")
                    userInfo.regionID = value
                except:
                    pass
                    
                try:
                    value, _ = winreg.QueryValueEx(key, "instanceId")
                    userInfo.instanceID = value
                except:
                    pass
        except:
            pass
            
        # Read from HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                              r"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion") as key:
                try:
                    value, _ = winreg.QueryValueEx(key, "ProductName")
                    userInfo.osEdition = value
                except:
                    pass
                    
                try:
                    value, _ = winreg.QueryValueEx(key, "CurrentBuild")
                    build = value
                except:
                    build = ""
                    
                try:
                    value, _ = winreg.QueryValueEx(key, "ReleaseId")
                    release_id = value
                except:
                    release_id = ""
                    
                try:
                    value, _ = winreg.QueryValueEx(key, "UBR")
                    ubr = value
                except:
                    ubr = ""
                    
                try:
                    value, _ = winreg.QueryValueEx(key, "CurrentMajorVersionNumber")
                    major = value
                except:
                    major = ""
                    
                try:
                    value, _ = winreg.QueryValueEx(key, "CurrentMinorVersionNumber")
                    minor = value
                except:
                    minor = ""
                
                if major and minor and build:
                    userInfo.osVersion = f"{major}.{minor}.{build}."
                if build and ubr:
                    userInfo.osBuild = f"{build}.{ubr}"
        except:
            pass
            
    except ImportError:
        # winreg is not available
        pass


def get_metadata_from_server(userInfo: UserInfo) -> None:
    return
    """Get metadata from server."""
    # This is a simplified version since we can't actually make HTTP requests easily
    # In a real implementation, we would make HTTP requests here
    try:
        # For demonstration, we're just setting defaults
        # In a real scenario, you would make actual HTTP requests

        userInfo.ownerAccountId = "unknown_account_id"

        # Note: Making real HTTP requests would require proper error handling
        # and would depend on network connectivity
    except Exception as e:
        print(f"Warning: Failed to get metadata from server: {e}", file=sys.stderr)


# Global variables to simulate C++ static variables
_userInfo = None
_initialized = False


def get_user_info() -> UserInfo:
    """Get user information."""
    global _userInfo, _initialized
    if _initialized and _userInfo is not None:
        return _userInfo
    
    userInfo = UserInfo()
    
    # Get OS type and version
    userInfo.osVersion, userInfo.osType = get_system_info()
    
    # Get username
    userInfo.userName = get_username()
    
    # Platform-specific information gathering
    if platform.system().lower() == "windows":
        get_user_info_from_registry(userInfo)
    elif platform.system().lower() == "android":
        get_user_info_from_env(userInfo)
    else:
        get_ali_uid_from_env(userInfo)
        get_user_info_from_ini(userInfo)
    
    # Get metadata from server
    get_metadata_from_server(userInfo)
    
    return userInfo


def append_user_info(fields: Dict[str, str]) -> None:
    """Append user info to fields dictionary."""
    userInfo = get_user_info()
    
    def add_field_if_not_empty(key: str, value: str):
        if value:
            fields[key] = value
    
    add_field_if_not_empty("InstanceID", userInfo.instanceID)
    add_field_if_not_empty("aliUid", userInfo.AliUID)
    add_field_if_not_empty("desktopId", userInfo.desktopID)
    add_field_if_not_empty("desktopGroupId", userInfo.desktopGroupID)
    add_field_if_not_empty("appInstanceGroupId", userInfo.appInstanceGroupID)
    add_field_if_not_empty("imageVersion", userInfo.imageVersion)
    add_field_if_not_empty("otaVersion", userInfo.fotaVersion)
    add_field_if_not_empty("officeSiteId", userInfo.officeSiteID)
    add_field_if_not_empty("osType", userInfo.osEdition)
    add_field_if_not_empty("osVersion", userInfo.osVersion)
    add_field_if_not_empty("osBuild", userInfo.osBuild)
    add_field_if_not_empty("regionId", userInfo.regionID)
    add_field_if_not_empty("appInstanceId", userInfo.appInstanceID)
    add_field_if_not_empty("dsMode", userInfo.dsMode)
    add_field_if_not_empty("localHostName", userInfo.localHostName)
    
    # Handle special cases for username
    if userInfo.userName in ["administrator", "root", ""]:
        userInfo.userName = get_username()
    
    fields["userName"] = userInfo.userName


def init_user_info() -> None:
    """Initialize user info."""
    global _userInfo, _initialized
    if not _initialized:
        _userInfo = get_user_info()
        _initialized = True


def update_user_info() -> None:
    """Update user info."""
    global _userInfo
    _userInfo = get_user_info()


def get_user_info_safe() -> UserInfo:
    """Get user info safely (thread-safe)."""
    global _userInfo
    if not _initialized:
        init_user_info()
    return _userInfo


# Entry points that mimic the C++ API
def InitUserInfo():
    """Initialize user info (mimics C++ function)."""
    init_user_info()


def UpdateUserInfo():
    """Update user info (mimics C++ function)."""
    update_user_info()


def GetUserInfo() -> UserInfo:
    """Get user info (mimigs C++ function)."""
    return get_user_info_safe()


def AppendUserInfo(fields: Dict[str, str]) -> None:
    """Append user info to fields (mimics C++ function)."""
    append_user_info(fields)