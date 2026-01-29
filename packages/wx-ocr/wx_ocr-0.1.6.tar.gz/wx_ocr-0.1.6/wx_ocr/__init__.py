"""
WeChat OCR - Python wrapper for WeChat's local OCR model

This package provides a Python interface to call WeChat's local OCR model
for text recognition in images.
"""

from .ocr_manager import OcrManager, OCR_MAX_TASK_ID
from .utils import (
    find_wechat_install_path,
    find_wechat_ocr_path,
    auto_find_wechat,
    list_available_ocr_versions,
)
from .simple_api import ocr, ocr_batch

__version__ = "0.1.0"
__all__ = [
    "ocr",  # 最简单的接口
    "ocr_batch",  # 批量处理接口
    "OcrManager",
    "OCR_MAX_TASK_ID",
    "WeChatOCR",
    "find_wechat_install_path",
    "find_wechat_ocr_path",
    "auto_find_wechat",
    "list_available_ocr_versions",
]


class WeChatOCR:
    """
    Simplified interface for WeChat OCR.
    
    Example:
        >>> from wx_ocr import WeChatOCR
        >>> 
        >>> ocr = WeChatOCR(wechat_dir="D:\\WeChat\\3.9.6.32")
        >>> ocr.init_ocr(wechat_ocr_dir="C:\\...\\WeChatOCR.exe")
        >>> 
        >>> results = []
        >>> def callback(img_path, result):
        ...     results.append(result)
        >>> 
        >>> ocr.ocr("image.png", callback=callback)
        >>> ocr.wait_for_completion()
        >>> print(results)
    """
    
    def __init__(self, wechat_dir: str):
        """
        Initialize WeChat OCR.
        
        Args:
            wechat_dir: Path to WeChat installation directory (contains mmmojo.dll)
        """
        self._manager = OcrManager(wechat_dir)
        self._started = False
    
    def init_ocr(self, wechat_ocr_dir: str, wechat_dir: str = None) -> None:
        """
        Initialize OCR service.
        
        Args:
            wechat_ocr_dir: Path to WeChatOCR.exe or its directory
            wechat_dir: Path to directory containing mmmojo.dll (optional, uses __init__ value if not provided)
        """
        import os
        from pathlib import Path
        
        # 设置 WeChatOCR.exe 路径
        self._manager.SetExePath(wechat_ocr_dir)
        
        # 设置 user-lib-dir (包含 mmmojo.dll 的目录)
        if wechat_dir:
            usr_lib_dir = wechat_dir
        elif self._manager.m_usr_lib_dir:
            usr_lib_dir = self._manager.m_usr_lib_dir
        else:
            # 如果 wechat_ocr_dir 是文件，使用其父目录
            ocr_path = Path(wechat_ocr_dir)
            if ocr_path.is_file():
                usr_lib_dir = str(ocr_path.parent)
            else:
                usr_lib_dir = wechat_ocr_dir
        
        self._manager.SetUsrLibDir(usr_lib_dir)
    
    def start(self) -> None:
        """Start the OCR service."""
        if not self._started:
            self._manager.StartWeChatOCR()
            self._started = True
    
    def stop(self) -> None:
        """Stop the OCR service."""
        if self._started:
            self._manager.KillWeChatOCR()
            self._started = False
    
    def ocr(self, image_path: str, callback=None) -> None:
        """
        Perform OCR on an image.
        
        Args:
            image_path: Path to the image file
            callback: Optional callback function(img_path: str, result: dict)
        """
        if not self._started:
            self.start()
        
        if callback:
            self._manager.SetOcrResultCallback(callback)
        
        self._manager.DoOCRTask(image_path)
    
    def wait_for_completion(self, timeout: float = None) -> None:
        """
        Wait for all OCR tasks to complete.
        
        Args:
            timeout: Maximum time to wait in seconds (None for no timeout)
        """
        import time
        start_time = time.time()
        
        while self._manager.m_task_id.qsize() != OCR_MAX_TASK_ID:
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError("OCR tasks did not complete within timeout")
            time.sleep(0.1)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
