# WX OCR (微信 OCR)

超级简单的微信 OCR - 一行代码识别图片文字

Python wrapper for WeChat's local OCR model - 使用 Python 调用微信本地 OCR 模型

本项目基于 [wechat_ocr](https://github.com/kanadeblisst00/wechat_ocr) 开发，主要改进：
- ✅ 超级简单的 API（一行代码）
- ✅ 自动管理服务和资源
- ✅ 批量处理支持
- ✅ 完善的中文文档

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 📚 文档导航

### 使用文档
- [无需微信-完全独立运行.md](无需微信-完全独立运行.md) - 🎉 重要！无需安装微信
- [快速开始指南](快速开始.md) - 新手必读
- [CLI命令行使用指南](CLI命令行使用指南.md) - 命令行工具详解
- [最简使用指南](最简使用指南.md) - 超简单 API（一行代码）
- [一分钟上手](一分钟上手.md) - 快速入门
- [详细使用说明](使用说明.md) - 完整使用教程

### 开发文档
- [开发文档](开发指南.md) - 开发者指南
- [更新日志](更新日志.md) - 版本历史
- [项目总结](项目总结.md) - 项目概览
- [成功总结](成功总结.md) - 测试结果
- [文档索引](文档索引.md) - 所有文档列表

## ⚠️ 温馨提示

该项目仅供学习交流使用，请勿用于商业用途。

## ✨ 特性

- 🚀 **完全独立运行** - 无需安装微信，项目自带所有必要文件
- 📦 **开箱即用** - 一行代码识别图片文字
- 🎯 **超简单 API** - 纯 Python 实现，无需编译
- 🔄 **支持批量处理** - 高效处理多张图片
- 💾 **自动保存结果** - 可选保存识别结果
- 🎯 **高精度识别** - 使用微信 OCR 模型
- 📊 **位置信息** - 支持提取文字位置坐标
- 🖥️ **命令行工具** - 无需编程，直接使用

## 📋 依赖条件

1. **Windows 操作系统** - 能运行 Windows 程序
2. **Python 3.8+** - Python 3.8 或更高版本
3. **无需安装微信** - 项目自带所有必要文件 ✨

**注意：** 项目包含约 35 MB 的 OCR 模型和程序文件，但这意味着你可以在任何 Windows 环境下使用，无需额外依赖！

## 🔧 安装

### 使用 pip 安装

```bash
pip install wx-ocr
```

### 使用 uv 安装（推荐）

```bash
uv pip install wx-ocr
```

### 从源码安装

```bash
git clone https://github.com/yourusername/wx-ocr.git
cd wx-ocr
uv pip install -e .
```

## 🚀 快速开始

### 安装

```bash
pip install wx-ocr
```

### 使用（超简单！）

```python
from wx_ocr import ocr

# 一行代码识别图片（无需任何配置）
texts = ocr("image.png", return_text_only=True)
print(texts)
```

**就这么简单！** 不需要：
- ❌ 安装微信
- ❌ 查找路径
- ❌ 配置参数

项目自带所有必要文件，开箱即用！

### 命令行使用

安装后可以直接使用命令行工具，无需编写代码：

```bash
# 识别图片，输出文字到命令行（默认）
wx-ocr image.png

# 输出 JSON 格式
wx-ocr --format json image.png

# 处理多张图片
wx-ocr image1.png image2.png image3.png

# 批量处理（使用通配符）
wx-ocr images/*.png

# 保存结果到文件
wx-ocr --save image.png
wx-ocr --save --output results/ image.png

# 查找 WeChat 路径
wx-ocr --find-paths

# 静默模式（只显示结果）
wx-ocr --quiet image.png

# 查看帮助
wx-ocr --help
```

**核心特性：**
- ✅ 默认输出到命令行（不保存文件）
- ✅ 支持纯文字和 JSON 格式
- ✅ 可选保存到文件（使用 `--save`）
- ✅ 支持管道和重定向

**详细的命令行使用说明请查看**: [CLI命令行使用指南.md](CLI命令行使用指南.md)

### 简单示例

```python
from wx_ocr import ocr

# 配置路径
WECHAT_OCR_DIR = r"C:\Users\Administrator\AppData\Roaming\Tencent\WeChat\XPlugin\Plugins\WeChatOCR\7057\extracted\WeChatOCR.exe"
WECHAT_DIR = r"D:\GreenSoftware\WeChat\3.9.6.32"

# 使用上下文管理器（推荐）
with WeChatOCR(wechat_dir=WECHAT_DIR) as ocr:
    ocr.init_ocr(wechat_ocr_dir=WECHAT_OCR_DIR)
    
    # 定义回调函数
    def callback(img_path, result):
        print(f"识别完成: {img_path}")
        for item in result.get("ocrResult", []):
            print(f"  文字: {item['text']}")
    
    # 识别图片
    ocr.ocr("test.png", callback=callback)
    ocr.wait_for_completion()
```

### 原始 API 示例

```python
import os
import json
import time
from wx_ocr import OcrManager, OCR_MAX_TASK_ID


wechat_ocr_dir = "C:\\Users\\Administrator\\AppData\\Roaming\\Tencent\\WeChat\\XPlugin\\Plugins\\WeChatOCR\\7057\\extracted\\WeChatOCR.exe"
wechat_dir = "D:\\GreenSoftware\\WeChat\\3.9.6.32"

def ocr_result_callback(img_path:str, results:dict):
    result_file = os.path.basename(img_path) + ".json"
    print(f"识别成功，img_path: {img_path}, result_file: {result_file}")
    with open(result_file, 'w', encoding='utf-8') as f:
       f.write(json.dumps(results, ensure_ascii=False, indent=2))

def main():
    ocr_manager = OcrManager(wechat_dir)
    # 设置WeChatOcr目录
    ocr_manager.SetExePath(wechat_ocr_dir)
    # 设置微信所在路径
    ocr_manager.SetUsrLibDir(wechat_dir)
    # 设置ocr识别结果的回调函数
    ocr_manager.SetOcrResultCallback(ocr_result_callback)
    # 启动ocr服务
    ocr_manager.StartWeChatOCR()
    # 开始识别图片
    ocr_manager.DoOCRTask(r"T:\Code\WeChat\OCR\Python\img\1.png")
    ocr_manager.DoOCRTask(r"T:\Code\WeChat\OCR\Python\img\2.png")
    ocr_manager.DoOCRTask(r"T:\Code\WeChat\OCR\Python\img\3.png")
    time.sleep(1)
    while ocr_manager.m_task_id.qsize() != OCR_MAX_TASK_ID:
        pass
    # 识别输出结果
    ocr_manager.KillWeChatOCR()
    

if __name__ == "__main__":
    main()
```

### 批量处理示例

查看 `example/batch_example.py` 获取完整的批量处理示例。

## 📖 API 文档

### WeChatOCR 类

简化的 OCR 接口，推荐使用。

#### 初始化

```python
ocr = WeChatOCR(wechat_dir="微信安装目录")
```

#### 方法

- `init_ocr(wechat_ocr_dir)` - 初始化 OCR 服务
- `start()` - 启动 OCR 服务
- `stop()` - 停止 OCR 服务
- `ocr(image_path, callback)` - 识别图片
- `wait_for_completion(timeout)` - 等待所有任务完成

### OcrManager 类

原始的 OCR 管理器，提供更多控制选项。

```python
from wechat_ocr import OcrManager

ocr_manager = OcrManager(wechat_dir)
ocr_manager.SetExePath(wechat_ocr_dir)
ocr_manager.SetUsrLibDir(wechat_dir)
ocr_manager.SetOcrResultCallback(callback)
ocr_manager.StartWeChatOCR()
ocr_manager.DoOCRTask(image_path)
# ... 等待完成
ocr_manager.KillWeChatOCR()
```

## 📁 项目结构

```
wechat-ocr/
├── wechat_ocr/           # 核心包
│   ├── __init__.py       # 简化的 API
│   ├── ocr_manager.py    # OCR 管理器
│   ├── xplugin_manager.py
│   ├── mmmojo_dll.py
│   ├── winapi.py
│   └── ...
├── example/              # 示例代码
│   ├── simple_example.py # 简单示例
│   ├── batch_example.py  # 批量处理示例
│   └── ocr.py           # 原始示例
├── wco_data/            # WeChat OCR 数据文件
├── test_img/            # 测试图片
├── pyproject.toml       # 项目配置
└── README.md
```

## 🔍 识别结果格式

```json
{
  "taskId": 1,
  "ocrResult": [
    {
      "text": "识别的文字",
      "location": {
        "left": 100,
        "top": 200,
        "right": 300,
        "bottom": 250
      },
      "pos": {...}
    }
  ]
}
```

## 🛠️ 开发

### 安装开发依赖

```bash
uv pip install -e ".[dev]"
```

### 运行示例

```bash
# 简单示例
python example/simple_example.py

# 批量处理示例
python example/batch_example.py
```

## ❓ 常见问题

### 如何找到 WeChatOCR.exe 路径？

通常在以下位置：
```
C:\Users\{用户名}\AppData\Roaming\Tencent\WeChat\XPlugin\Plugins\WeChatOCR\{版本号}\extracted\WeChatOCR.exe
```

### 如何找到微信安装目录？

右键微信快捷方式 -> 属性 -> 打开文件所在位置

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [kanadeblisst00/wechat_ocr](https://github.com/kanadeblisst00/wechat_ocr) - 原始项目
- [QQImpl](https://github.com/EEEEhex/QQImpl) - 原始 C++ 实现
- WeChat - OCR 模型提供

## ⚠️ 免责声明

本项目仅供学习交流使用，不得用于商业用途。使用本项目所产生的一切后果由使用者自行承担。

---

## 运行结果示例

![result](./result.png)

---

## 感谢

https://github.com/EEEEhex/QQImpl