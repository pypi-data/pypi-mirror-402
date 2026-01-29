# wx-ocr

一行代码识别图片文字，无需安装微信

## 安装

```bash
pip install wx-ocr
```

## 使用

### Python API

```python
from wx_ocr import ocr

# 识别图片
texts = ocr("image.png", return_text_only=True)
print(texts)  # ['文字1', '文字2', ...]

# 获取完整结果（包含位置信息）
result = ocr("image.png")
for item in result['ocrResult']:
    print(item['text'], item['location'])

# 批量识别
from wx_ocr import ocr_batch
results = ocr_batch(["1.png", "2.png", "3.png"], return_text_only=True)
```

### 命令行

```bash
# 识别图片
wx-ocr image.png

# JSON 格式输出
wx-ocr --format json image.png

# 批量处理
wx-ocr *.png

# 保存结果
wx-ocr --save --output results/ image.png
```

## 说明

- 仅支持 Windows
- 需要 Python 3.8+
- 无需安装微信（项目自带 OCR 文件）
- 基于 [wechat_ocr](https://github.com/kanadeblisst00/wechat_ocr) 开发

## License

MIT