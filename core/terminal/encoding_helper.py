"""
终端编码辅助模块

提供跨平台的编码处理功能
"""

import sys
import os
from typing import Union, Optional


def get_system_encoding() -> str:
    """获取系统编码"""
    if sys.platform == "win32":
        # Windows: 使用GBK作为控制台编码，UTF-8作为文件编码
        try:
            import ctypes
            # 获取控制台代码页
            kernel32 = ctypes.windll.kernel32
            cp = kernel32.GetConsoleOutputCP()
            if cp == 65001:  # UTF-8
                return "utf-8"
            elif cp == 936:  # GBK (简体中文)
                return "gbk"
            else:
                return "gbk"  # 默认GBK
        except:
            return "gbk"
    else:
        # Linux/macOS: 使用UTF-8
        return "utf-8"


def encode_for_terminal(text: str, encoding: Optional[str] = None) -> bytes:
    """为终端编码文本"""
    if encoding is None:
        encoding = get_system_encoding()
    
    try:
        return text.encode(encoding, errors='replace')
    except UnicodeEncodeError:
        # 回退到UTF-8
        return text.encode('utf-8', errors='replace')


def decode_from_terminal(data: bytes, encoding: Optional[str] = None) -> str:
    """从终端解码数据"""
    if encoding is None:
        encoding = get_system_encoding()
    
    encodings_to_try = [encoding, 'utf-8', 'gbk', 'gb2312', 'big5', 'shift_jis']
    
    for enc in encodings_to_try:
        try:
            return data.decode(enc, errors='strict')
        except UnicodeDecodeError:
            continue
    
    # 所有编码都失败，使用replace模式
    try:
        return data.decode('utf-8', errors='replace')
    except:
        return str(data)


def setup_terminal_encoding():
    """设置终端编码"""
    if sys.platform == "win32":
        import io
        # 设置标准输出编码
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer,
                encoding='utf-8',
                errors='replace',
                line_buffering=True
            )
        if hasattr(sys.stdin, 'buffer'):
            sys.stdin = io.TextIOWrapper(
                sys.stdin.buffer,
                encoding='utf-8',
                errors='replace',
                line_buffering=True
            )
        
        # 设置环境变量
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        # 尝试设置控制台代码页为UTF-8
        try:
            subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
        except:
            pass


def safe_print(text: str, end: str = "
", flush: bool = True):
    """安全打印，处理编码问题"""
    try:
        print(text, end=end, flush=flush)
    except UnicodeEncodeError:
        # 编码失败，尝试使用替代字符
        encoded = encode_for_terminal(text)
        decoded = decode_from_terminal(encoded)
        print(decoded, end=end, flush=flush)


if __name__ == "__main__":
    # 测试代码
    print(f"系统编码: {get_system_encoding()}")
    test_text = "中文测试 Chinese Test 日本語テスト"
    encoded = encode_for_terminal(test_text)
    decoded = decode_from_terminal(encoded)
    print(f"原始: {test_text}")
    print(f"编码后: {encoded}")
    print(f"解码后: {decoded}")
    print(f"匹配: {test_text == decoded}")
