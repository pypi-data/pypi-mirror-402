"""
Command-line interface for WeChat OCR.
"""
import sys
import json
import argparse
from pathlib import Path
from typing import List

from . import WeChatOCR, auto_find_wechat


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="WeChat OCR - Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process an image and output text to console
  wx-ocr image.png
  
  # Output as JSON
  wx-ocr --format json image.png
  
  # Process multiple images
  wx-ocr image1.png image2.png image3.png
  
  # Save results to files
  wx-ocr --save image.png
  wx-ocr --save --output results/ image.png
  
  # Find WeChat paths
  wx-ocr --find-paths
  
  # Specify WeChat paths manually
  wx-ocr --wechat-dir "D:\\WeChat" --ocr-dir "C:\\...\\WeChatOCR.exe" image.png
        """
    )
    
    parser.add_argument(
        "images",
        nargs="*",
        help="Image files to process"
    )
    
    parser.add_argument(
        "--wechat-dir",
        help="WeChat installation directory"
    )
    
    parser.add_argument(
        "--ocr-dir",
        help="WeChatOCR.exe path or directory"
    )
    
    parser.add_argument(
        "--format", "-f",
        choices=["text", "json"],
        default="text",
        help="Output format: text (default) or json"
    )
    
    parser.add_argument(
        "--save", "-s",
        action="store_true",
        help="Save results to files (default: output to console)"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="./ocr_output",
        help="Output directory when using --save (default: ./ocr_output)"
    )
    
    parser.add_argument(
        "--find-paths",
        action="store_true",
        help="Find and display WeChat paths"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress messages (only show results)"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="wx-ocr 0.1.5"
    )
    
    args = parser.parse_args()
    
    # Handle --find-paths
    if args.find_paths:
        find_paths_command()
        return 0
    
    # Validate images
    if not args.images:
        parser.print_help()
        return 1
    
    # Get WeChat paths - 优先使用项目自带的 wco_data
    wechat_dir = args.wechat_dir
    ocr_dir = args.ocr_dir
    
    if not wechat_dir or not ocr_dir:
        # 首先尝试使用项目自带的 wco_data
        from pathlib import Path
        package_dir = Path(__file__).parent
        wco_data_dir = package_dir / "wco_data"
        
        if wco_data_dir.exists() and (wco_data_dir / "WeChatOCR.exe").exists():
            # 使用项目自带的
            wechat_dir = wechat_dir or str(wco_data_dir)
            ocr_dir = ocr_dir or str(wco_data_dir / "WeChatOCR.exe")
            if not args.quiet:
                print("使用项目自带的 OCR 文件", file=sys.stderr)
        else:
            # 如果项目自带的不存在，尝试查找系统安装的微信
            if not args.quiet:
                print("正在自动检测 WeChat 路径...", file=sys.stderr)
            paths = auto_find_wechat()
            wechat_dir = wechat_dir or paths.get("wechat_dir")
            ocr_dir = ocr_dir or paths.get("wechat_ocr_dir")
    
    if not wechat_dir or not ocr_dir:
        print("错误: 无法找到 OCR 文件", file=sys.stderr)
        print("", file=sys.stderr)
        print("请确保：", file=sys.stderr)
        print("  1. 项目包含 wco_data 目录，或", file=sys.stderr)
        print("  2. 系统已安装微信，或", file=sys.stderr)
        print("  3. 使用 --wechat-dir 和 --ocr-dir 手动指定路径", file=sys.stderr)
        return 1
    
    # Process images
    return process_images(
        args.images,
        wechat_dir,
        ocr_dir,
        output_format=args.format,
        save_to_file=args.save,
        output_dir=args.output,
        quiet=args.quiet
    )


def find_paths_command():
    """Find and display WeChat paths."""
    from pathlib import Path
    
    print("正在查找 OCR 文件...\n")
    
    # 首先检查项目自带的 wco_data
    package_dir = Path(__file__).parent
    wco_data_dir = package_dir / "wco_data"
    
    if wco_data_dir.exists() and (wco_data_dir / "WeChatOCR.exe").exists():
        print("✓ 找到项目自带的 OCR 文件:")
        print(f"  目录: {wco_data_dir}")
        print(f"  WeChatOCR.exe: {wco_data_dir / 'WeChatOCR.exe'}")
        print(f"  mmmojo.dll: {wco_data_dir / 'mmmojo_64.dll'}")
        print("\n这是推荐使用的方式，无需安装微信！")
    else:
        print("✗ 未找到项目自带的 OCR 文件")
    
    # 然后查找系统安装的微信
    print("\n正在查找系统安装的微信...")
    paths = auto_find_wechat()
    
    print("\n检测到的系统路径:")
    print(f"  WeChat 目录:    {paths.get('wechat_dir') or '未找到'}")
    print(f"  WeChatOCR 目录: {paths.get('wechat_ocr_dir') or '未找到'}")
    
    # List available versions
    from .utils import list_available_ocr_versions
    versions = list_available_ocr_versions()
    
    if versions:
        print(f"\n可用的 WeChatOCR 版本 ({len(versions)} 个):")
        for i, version in enumerate(versions, 1):
            print(f"  {i}. {version}")
    
    # 总结
    print("\n" + "="*60)
    if wco_data_dir.exists():
        print("推荐：使用项目自带的 OCR 文件（无需安装微信）")
    elif paths.get('wechat_dir') and paths.get('wechat_ocr_dir'):
        print("可以使用系统安装的微信 OCR")
    else:
        print("未找到可用的 OCR 文件")
        print("请确保项目包含 wco_data 目录或安装微信")


def process_images(
    image_paths: List[str],
    wechat_dir: str,
    ocr_dir: str,
    output_format: str = "text",
    save_to_file: bool = False,
    output_dir: str = "./ocr_output",
    quiet: bool = False
) -> int:
    """Process images with OCR."""
    # Filter valid images
    valid_images = []
    for img_path in image_paths:
        if Path(img_path).exists():
            valid_images.append(img_path)
        else:
            print(f"警告: 图片不存在: {img_path}", file=sys.stderr)
    
    if not valid_images:
        print("错误: 没有有效的图片可处理", file=sys.stderr)
        return 1
    
    # Create output directory if saving to file
    if save_to_file:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    
    if not quiet:
        print(f"正在处理 {len(valid_images)} 张图片...\n", file=sys.stderr)
    
    # Store results
    all_results = []
    processed = 0
    
    try:
        with WeChatOCR(wechat_dir=wechat_dir) as ocr:
            ocr.init_ocr(wechat_ocr_dir=ocr_dir)
            
            def callback(img_path: str, result: dict):
                nonlocal processed
                processed += 1
                all_results.append((img_path, result))
            
            # Submit all tasks
            for img_path in valid_images:
                ocr.ocr(img_path, callback=callback)
            
            # Wait for completion
            ocr.wait_for_completion(timeout=60)
        
        # Output results
        for img_path, result in all_results:
            ocr_result = result.get("ocrResult", [])
            
            if save_to_file:
                # Save to file
                result_file = output_path / f"{Path(img_path).name}.json"
                with open(result_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                if not quiet:
                    print(f"✓ 已保存: {result_file}", file=sys.stderr)
            else:
                # Output to console
                if len(valid_images) > 1:
                    # Multiple images: show filename
                    print(f"\n{'='*60}")
                    print(f"文件: {Path(img_path).name}")
                    print('='*60)
                
                if output_format == "json":
                    # JSON format
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                else:
                    # Text format (default)
                    if ocr_result:
                        for item in ocr_result:
                            print(item['text'])
                    else:
                        print("(未识别到文字)")
        
        if not quiet:
            if save_to_file:
                print(f"\n✓ 成功处理 {processed} 张图片", file=sys.stderr)
                print(f"✓ 结果已保存到: {output_path.absolute()}", file=sys.stderr)
            else:
                print(f"\n✓ 成功处理 {processed} 张图片", file=sys.stderr)
        
        return 0
        
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
