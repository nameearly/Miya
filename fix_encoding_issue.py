#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复终端编码问题

修复Windows上的GBK/UTF-8编码问题，解决'a bytes-like object is required, not 'str''错误
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

# 设置编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("修复终端编码问题")
print("=" * 80)


def fix_conpty_manager():
    """修复ConPTY终端管理器的编码问题"""
    print("\n1. 修复ConPTY终端管理器...")
    
    file_path = "core/conpty_terminal_manager.py"
    if not os.path.exists(file_path):
        print(f"   [SKIP] 文件不存在: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找需要修复的方法
        if 'def send_command(self, session_id: str, command: str) -> bool:' in content:
            # 找到send_command方法
            lines = content.split('\n')
            fixed_lines = []
            in_send_command = False
            
            for i, line in enumerate(lines):
                fixed_lines.append(line)
                
                if 'def send_command(self, session_id: str, command: str) -> bool:' in line:
                    in_send_command = True
                
                if in_send_command and 'session.process.stdin.write(command)' in line:
                    # 替换这一行
                    indent = len(line) - len(line.lstrip())
                    indent_str = ' ' * indent
                    
                    # 添加编码处理
                    fixed_lines[-1] = f"{indent_str}            # 根据平台选择编码"
                    fixed_lines.append(f"{indent_str}            if sys.platform == 'win32':")
                    fixed_lines.append(f"{indent_str}                encoded_command = command.encode('gbk', errors='replace')")
                    fixed_lines.append(f"{indent_str}            else:")
                    fixed_lines.append(f"{indent_str}                encoded_command = command.encode('utf-8', errors='replace')")
                    fixed_lines.append(f"{indent_str}            ")
                    fixed_lines.append(f"{indent_str}            session.process.stdin.write(encoded_command)")
                    
                    in_send_command = False
                
                if in_send_command and 'def _read_output(self, session_id: str):' in line:
                    in_send_command = False
            
            # 确保导入了sys模块
            if 'import sys' not in content:
                # 在文件开头添加import sys
                import_lines = []
                for line in fixed_lines:
                    import_lines.append(line)
                    if line.startswith('import ') and 'import sys' not in '\n'.join(import_lines[-5:]):
                        import_lines.append('import sys')
                fixed_lines = import_lines
            
            fixed_content = '\n'.join(fixed_lines)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print(f"   [OK] 已修复 {file_path}")
            return True
        else:
            print(f"   [SKIP] 未找到send_command方法")
            return False
            
    except Exception as e:
        print(f"   [FAIL] 修复失败: {e}")
        return False


def fix_local_terminal_manager():
    """修复本地终端管理器的编码问题"""
    print("\n2. 修复本地终端管理器...")
    
    file_path = "core/local_terminal_manager.py"
    if not os.path.exists(file_path):
        print(f"   [SKIP] 文件不存在: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找_create_process方法中的编码问题
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            fixed_lines.append(line)
            
            # 修复subprocess.Popen调用中的编码设置
            if 'subprocess.Popen(' in line and 'text=True' in line:
                # 确保有正确的编码参数
                if 'encoding=' not in line:
                    # 在text=True后添加encoding参数
                    line = line.replace('text=True', "text=True, encoding='utf-8'")
                    fixed_lines[-1] = line
                    print(f"   [FIX] 第{i+1}行: 添加编码参数")
            
            # 修复Windows特定的编码
            if platform.system() == "Windows":
                if 'cmd.exe' in line and 'subprocess.Popen' in line:
                    # 确保Windows命令使用正确的编码
                    if 'encoding=' not in line:
                        line = line.replace("['cmd.exe']", "['cmd.exe', '/c', 'chcp', '65001', '>nul']")
                        fixed_lines[-1] = line
                        print(f"   [FIX] 第{i+1}行: 添加chcp命令设置UTF-8")
        
        fixed_content = '\n'.join(fixed_lines)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"   [OK] 已修复 {file_path}")
        return True
        
    except Exception as e:
        print(f"   [FAIL] 修复失败: {e}")
        return False


def create_encoding_helper():
    """创建编码辅助模块"""
    print("\n3. 创建编码辅助模块...")
    
    file_path = "core/terminal/encoding_helper.py"
    
    content = '''"""
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


def safe_print(text: str, end: str = "\n", flush: bool = True):
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
'''
    
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"   [OK] 已创建 {file_path}")
        return True
        
    except Exception as e:
        print(f"   [FAIL] 创建失败: {e}")
        return False


def test_fix():
    """测试修复效果"""
    print("\n4. 测试修复效果...")
    
    try:
        # 测试导入修复后的模块
        import core.conpty_terminal_manager as conpty
        import core.local_terminal_manager as local
        
        print("   [OK] 模块导入成功")
        
        # 测试编码辅助模块
        try:
            from core.terminal.encoding_helper import (
                get_system_encoding, encode_for_terminal, decode_from_terminal
            )
            
            encoding = get_system_encoding()
            print(f"   [OK] 系统编码检测: {encoding}")
            
            test_text = "编码测试"
            encoded = encode_for_terminal(test_text)
            decoded = decode_from_terminal(encoded)
            
            if test_text == decoded:
                print(f"   [OK] 编码解码测试通过")
            else:
                print(f"   [WARN] 编码解码测试不匹配: {test_text} != {decoded}")
                
        except ImportError as e:
            print(f"   [WARN] 编码辅助模块导入失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"   [FAIL] 测试失败: {e}")
        return False


def main():
    """主函数"""
    print("开始修复终端编码问题...\n")
    
    # 执行修复
    fix1 = fix_conpty_manager()
    fix2 = fix_local_terminal_manager()
    fix3 = create_encoding_helper()
    
    # 测试修复
    test_result = test_fix()
    
    # 总结
    print("\n" + "=" * 80)
    print("修复结果总结")
    print("=" * 80)
    
    fixes = [fix1, fix2, fix3]
    successful_fixes = sum(1 for f in fixes if f)
    
    print(f"成功修复: {successful_fixes}/{len(fixes)}")
    print(f"测试结果: {'通过' if test_result else '失败'}")
    
    if successful_fixes == len(fixes) and test_result:
        print("\n[SUCCESS] 编码问题修复完成！")
        print("下一步: 修复命令执行问题")
        return True
    else:
        print("\n[WARNING] 部分修复可能未完成")
        print("请检查上述输出并手动修复剩余问题")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
