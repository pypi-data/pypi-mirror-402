"""
超级简单的 OCR API - 只需要传入图片路径，返回识别结果
"""
import os
import time
from pathlib import Path
from typing import List, Dict, Union, Optional
from .ocr_manager import OcrManager, OCR_MAX_TASK_ID


# 全局 OCR 管理器（单例模式）
_global_ocr_manager = None
_global_wco_data_dir = None


def _get_wco_data_dir():
    """获取 wco_data 目录路径."""
    global _global_wco_data_dir
    
    if _global_wco_data_dir is None:
        # 尝试多个可能的位置
        possible_paths = [
            Path(__file__).parent / "wco_data",  # 包内部（pip 安装后）
            Path(__file__).parent.parent / "wco_data",  # 开发环境：项目根目录
            Path.cwd() / "wco_data",  # 当前工作目录
        ]
        
        # 如果是通过 pip 安装的，检查 site-packages 中的位置
        try:
            import site
            for site_dir in site.getsitepackages():
                site_wco_data = Path(site_dir) / "wechat_ocr" / "wco_data"
                if site_wco_data.exists():
                    possible_paths.insert(0, site_wco_data)
        except:
            pass
        
        for path in possible_paths:
            if path.exists() and (path / "WeChatOCR.exe").exists():
                _global_wco_data_dir = str(path)
                break
        
        if _global_wco_data_dir is None:
            raise FileNotFoundError(
                "找不到 wco_data 目录！\n"
                "请确保 wco_data 目录存在，并包含 WeChatOCR.exe 文件。\n"
                "可能的位置：\n"
                "1. wechat_ocr/wco_data (包内部)\n"
                "2. 项目根目录/wco_data\n"
                "3. 当前工作目录/wco_data"
            )
    
    return _global_wco_data_dir


def _get_ocr_manager():
    """获取全局 OCR 管理器（单例）."""
    global _global_ocr_manager
    
    if _global_ocr_manager is None:
        wco_data_dir = _get_wco_data_dir()
        wechat_ocr_exe = os.path.join(wco_data_dir, "WeChatOCR.exe")
        
        # 创建管理器
        _global_ocr_manager = OcrManager(wco_data_dir)
        _global_ocr_manager.SetExePath(wechat_ocr_exe)
        _global_ocr_manager.SetUsrLibDir(wco_data_dir)
        
        # 启动服务
        _global_ocr_manager.StartWeChatOCR()
        
        # 等待连接
        max_wait = 10
        waited = 0
        while not _global_ocr_manager.m_connect_state.value and waited < max_wait:
            time.sleep(0.5)
            waited += 0.5
        
        if not _global_ocr_manager.m_connect_state.value:
            _global_ocr_manager = None
            raise RuntimeError(
                "OCR 服务连接失败！\n"
                "可能的原因：\n"
                "1. WeChatOCR.exe 无法启动\n"
                "2. mmmojo.dll 版本不兼容\n"
                "3. 缺少依赖文件"
            )
    
    return _global_ocr_manager


def _format_text_with_lines(ocr_result: List[Dict], line_threshold: int = 15) -> str:
    """
    将 OCR 结果格式化为带换行的文本
    
    Args:
        ocr_result: OCR 识别结果列表（保持原始顺序）
        line_threshold: 判断是否为新行的垂直距离阈值（像素）
    
    Returns:
        格式化后的文本，包含换行
    """
    if not ocr_result:
        return ""
    
    # 不重新排序，保持 OCR 返回的原始顺序
    lines = []
    current_line = []
    last_top = None
    
    for item in ocr_result:
        top = item['location']['top']
        
        # 如果是第一个元素，或者 top 位置差距较大，说明是新的一行
        if last_top is not None and abs(top - last_top) > line_threshold:
            lines.append(' '.join([i['text'] for i in current_line]))
            current_line = []
        
        current_line.append(item)
        last_top = top
    
    # 添加最后一行
    if current_line:
        lines.append(' '.join([i['text'] for i in current_line]))
    
    return '\n'.join(lines)


def ocr(image_path: str, return_text_only: bool = False, format_text: bool = False) -> Union[List[str], str, Dict]:
    """
    识别单张图片（最简单的接口）
    
    Args:
        image_path: 图片路径
        return_text_only: 是否只返回文字列表（默认 False，返回完整结果）
        format_text: 是否格式化为带换行的文本（仅当 return_text_only=True 时有效）
    
    Returns:
        如果 return_text_only=False: 返回完整结果字典
        如果 return_text_only=True 且 format_text=False: 返回文字列表 ["文字1", "文字2", ...]
        如果 return_text_only=True 且 format_text=True: 返回带换行的文本字符串
    
    Examples:
        >>> # 只获取文字列表
        >>> texts = ocr("image.png", return_text_only=True)
        >>> print(texts)
        ['文字1', '文字2', '文字3']
        
        >>> # 获取格式化的文本（带换行）
        >>> text = ocr("image.png", return_text_only=True, format_text=True)
        >>> print(text)
        文字1 文字2
        文字3 文字4
        
        >>> # 获取完整结果（包含位置信息）
        >>> result = ocr("image.png")
        >>> for item in result['ocrResult']:
        ...     print(item['text'], item['location'])
    """
    # 检查图片是否存在
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片不存在: {image_path}")
    
    # 获取 OCR 管理器
    manager = _get_ocr_manager()
    
    # 存储结果
    result_container = []
    
    def callback(img_path, result):
        result_container.append(result)
    
    # 设置回调
    manager.SetOcrResultCallback(callback)
    
    # 执行 OCR
    manager.DoOCRTask(os.path.abspath(image_path))
    
    # 等待结果（最多 10 秒）
    max_wait = 10
    waited = 0
    while len(result_container) == 0 and waited < max_wait:
        time.sleep(0.1)
        waited += 0.1
    
    if len(result_container) == 0:
        raise TimeoutError(f"识别超时: {image_path}")
    
    result = result_container[0]
    
    # 根据参数返回不同格式
    if return_text_only:
        ocr_result = result.get('ocrResult', [])
        if format_text:
            return _format_text_with_lines(ocr_result)
        else:
            return [item['text'] for item in ocr_result]
    else:
        # 直接返回 ocrResult，不包含 taskId
        return result.get('ocrResult', [])


def ocr_batch(image_paths: List[str], return_text_only: bool = False, format_text: bool = False) -> List[Union[List[str], str, Dict]]:
    """
    批量识别多张图片
    
    Args:
        image_paths: 图片路径列表
        return_text_only: 是否只返回文字列表
        format_text: 是否格式化为带换行的文本（仅当 return_text_only=True 时有效）
    
    Returns:
        结果列表，每个元素对应一张图片的识别结果
    
    Examples:
        >>> # 批量识别，只获取文字
        >>> results = ocr_batch(["1.png", "2.png", "3.png"], return_text_only=True)
        >>> for texts in results:
        ...     print(texts)
        
        >>> # 批量识别，获取格式化的文本（带换行）
        >>> results = ocr_batch(["1.png", "2.png"], return_text_only=True, format_text=True)
        >>> for text in results:
        ...     print(text)
        ...     print("---")
        
        >>> # 批量识别，获取完整结果
        >>> results = ocr_batch(["1.png", "2.png", "3.png"])
        >>> for result in results:
        ...     for item in result['ocrResult']:
        ...         print(item['text'])
    """
    # 检查所有图片是否存在
    for img_path in image_paths:
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"图片不存在: {img_path}")
    
    # 获取 OCR 管理器
    manager = _get_ocr_manager()
    
    # 存储结果
    results = {}
    
    def callback(img_path, result):
        results[img_path] = result
    
    # 设置回调
    manager.SetOcrResultCallback(callback)
    
    # 提交所有任务
    for img_path in image_paths:
        manager.DoOCRTask(os.path.abspath(img_path))
    
    # 等待所有结果（最多 30 秒）
    max_wait = 30
    waited = 0
    while len(results) < len(image_paths) and waited < max_wait:
        time.sleep(0.1)
        waited += 0.1
    
    if len(results) < len(image_paths):
        raise TimeoutError(f"部分图片识别超时，完成 {len(results)}/{len(image_paths)}")
    
    # 按照输入顺序返回结果
    ordered_results = []
    for img_path in image_paths:
        abs_path = os.path.abspath(img_path)
        result = results.get(abs_path)
        
        if result:
            if return_text_only:
                ocr_result = result.get('ocrResult', [])
                if format_text:
                    ordered_results.append(_format_text_with_lines(ocr_result))
                else:
                    ordered_results.append([item['text'] for item in ocr_result])
            else:
                # 直接返回 ocrResult，不包含 taskId
                ordered_results.append(result.get('ocrResult', []))
    
    return ordered_results


def cleanup():
    """
    清理 OCR 服务（可选）
    
    通常不需要手动调用，程序退出时会自动清理。
    如果需要释放资源，可以手动调用此函数。
    """
    global _global_ocr_manager
    
    if _global_ocr_manager is not None:
        try:
            _global_ocr_manager.KillWeChatOCR()
        except:
            pass
        _global_ocr_manager = None


# 程序退出时自动清理
import atexit
atexit.register(cleanup)
