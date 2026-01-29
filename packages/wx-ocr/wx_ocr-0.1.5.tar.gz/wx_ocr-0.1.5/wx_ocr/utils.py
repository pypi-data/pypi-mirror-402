"""
Utility functions for WeChat OCR.
"""
import os
import winreg
from pathlib import Path
from typing import Optional, List


def find_wechat_install_path() -> Optional[str]:
    """
    Try to find WeChat installation path from Windows registry.
    
    Returns:
        WeChat installation path or None if not found
    """
    try:
        # Try to read from registry
        key_paths = [
            r"SOFTWARE\WOW6432Node\Tencent\WeChat",
            r"SOFTWARE\Tencent\WeChat",
        ]
        
        for key_path in key_paths:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                    install_path, _ = winreg.QueryValueEx(key, "InstallPath")
                    if install_path and os.path.exists(install_path):
                        return install_path
            except (FileNotFoundError, OSError):
                continue
                
    except Exception as e:
        print(f"Error finding WeChat path: {e}")
    
    return None


def find_wechat_ocr_path() -> Optional[str]:
    """
    Try to find WeChatOCR.exe path.
    
    Returns:
        WeChatOCR.exe path or None if not found
    """
    # Common locations
    appdata = os.getenv("APPDATA")
    if not appdata:
        return None
    
    wechat_plugin_base = Path(appdata) / "Tencent" / "WeChat" / "XPlugin" / "Plugins" / "WeChatOCR"
    
    if not wechat_plugin_base.exists():
        return None
    
    # Find all version directories
    version_dirs = [d for d in wechat_plugin_base.iterdir() if d.is_dir()]
    
    for version_dir in sorted(version_dirs, reverse=True):  # Try newest first
        ocr_exe = version_dir / "extracted" / "WeChatOCR.exe"
        if ocr_exe.exists():
            return str(ocr_exe)
    
    return None


def find_mmmojo_dll(wechat_path: str) -> Optional[str]:
    """
    Find mmmojo.dll or mmmojo_64.dll in WeChat installation directory.
    
    Args:
        wechat_path: WeChat installation directory
        
    Returns:
        Path to mmmojo dll or None if not found
    """
    import platform
    
    wechat_dir = Path(wechat_path)
    
    # Determine which dll to look for based on Python architecture
    python_bit = platform.architecture()[0]
    dll_name = "mmmojo_64.dll" if python_bit == "64bit" else "mmmojo.dll"
    
    dll_path = wechat_dir / dll_name
    if dll_path.exists():
        return str(dll_path)
    
    return None


def auto_find_wechat() -> dict:
    """
    Automatically find WeChat and WeChatOCR paths.
    
    Returns:
        Dictionary with 'wechat_dir' and 'wechat_ocr_dir' keys
    """
    result = {
        "wechat_dir": None,
        "wechat_ocr_dir": None,
    }
    
    # Find WeChat installation
    wechat_dir = find_wechat_install_path()
    if wechat_dir:
        result["wechat_dir"] = wechat_dir
        print(f"✓ Found WeChat: {wechat_dir}")
    else:
        print("✗ WeChat installation not found")
    
    # Find WeChatOCR
    wechat_ocr_dir = find_wechat_ocr_path()
    if wechat_ocr_dir:
        result["wechat_ocr_dir"] = wechat_ocr_dir
        print(f"✓ Found WeChatOCR: {wechat_ocr_dir}")
    else:
        print("✗ WeChatOCR not found")
    
    return result


def list_available_ocr_versions() -> List[str]:
    """
    List all available WeChatOCR versions.
    
    Returns:
        List of WeChatOCR.exe paths
    """
    appdata = os.getenv("APPDATA")
    if not appdata:
        return []
    
    wechat_plugin_base = Path(appdata) / "Tencent" / "WeChat" / "XPlugin" / "Plugins" / "WeChatOCR"
    
    if not wechat_plugin_base.exists():
        return []
    
    ocr_paths = []
    for version_dir in wechat_plugin_base.iterdir():
        if version_dir.is_dir():
            ocr_exe = version_dir / "extracted" / "WeChatOCR.exe"
            if ocr_exe.exists():
                ocr_paths.append(str(ocr_exe))
    
    return sorted(ocr_paths, reverse=True)


if __name__ == "__main__":
    # Test the utility functions
    print("Searching for WeChat and WeChatOCR...\n")
    
    paths = auto_find_wechat()
    
    print("\nAvailable WeChatOCR versions:")
    versions = list_available_ocr_versions()
    if versions:
        for i, version in enumerate(versions, 1):
            print(f"  {i}. {version}")
    else:
        print("  None found")
