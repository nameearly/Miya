"""
安全配置加载器 - 支持加密配置的自动解密

功能:
1. 自动检测加密配置项 (enc:前缀)
2. 从环境变量获取主密码
3. 自动解密敏感配置
4. 向后兼容未加密配置
"""
import os
import base64
from pathlib import Path
from typing import Any, Dict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecureConfigLoader:
    """安全配置加载器"""
    
    def __init__(self):
        """初始化安全配置加载器"""
        self.fernet = self._init_fernet()
    
    def _init_fernet(self) -> Fernet | None:
        """
        初始化Fernet加密器
        
        Returns:
            Fernet实例或None(如果未配置主密码)
        """
        # 从环境变量获取主密码
        master_password = os.getenv('ENCRYPTION_PASSWORD')
        
        if not master_password:
            # 尝试从密钥文件读取
            key_file = Path('config/encryption_key.bin')
            if key_file.exists():
                with open(key_file, 'rb') as f:
                    key = f.read()
                return Fernet(key)
            
            # 没有配置加密,返回None(使用明文配置)
            return None
        
        # 使用PBKDF2从主密码派生密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'miya_salt_value',
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        return Fernet(key)
    
    def decrypt_value(self, value: str) -> str:
        """
        解密单个配置值
        
        Args:
            value: 配置值 (可能是加密的或明文的)
            
        Returns:
            解密后的值
        """
        if not self.fernet:
            # 未配置加密,直接返回
            return value
        
        if not value or not isinstance(value, str):
            return value
        
        if not value.startswith('enc:'):
            # 非加密值,直接返回
            return value
        
        try:
            encrypted_data = base64.urlsafe_b64decode(value[4:])
            decrypted = self.fernet.decrypt(encrypted_data)
            return decrypted.decode()
        except Exception as e:
            # 解密失败,可能是明文配置,返回原值
            print(f"警告: 解密配置失败: {e},使用原值")
            return value
    
    def decrypt_config_dict(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        解密配置字典中的所有加密值
        
        Args:
            config: 配置字典
            
        Returns:
            解密后的配置字典
        """
        if not isinstance(config, dict):
            return config
        
        decrypted_config = {}
        for key, value in config.items():
            if isinstance(value, str):
                decrypted_config[key] = self.decrypt_value(value)
            elif isinstance(value, dict):
                decrypted_config[key] = self.decrypt_config_dict(value)
            else:
                decrypted_config[key] = value
        
        return decrypted_config
    
    def load_env_file(self, env_path: str | Path = 'config/.env') -> Dict[str, str]:
        """
        加载并解密.env文件
        
        Args:
            env_path: .env文件路径
            
        Returns:
            配置字典
        """
        config = {}
        
        env_file = Path(env_path)
        if not env_file.exists():
            print(f"警告: 配置文件不存在: {env_path}")
            return config
        
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                
                # 解析键值对
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 移除引号
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # 解密值
                    config[key] = self.decrypt_value(value)
        
        return config
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        获取配置值(支持自动解密)
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        # 优先从环境变量读取
        value = os.getenv(key)
        if value is not None:
            return self.decrypt_value(value)
        
        # 从.env文件读取
        config = self.load_env_file()
        return config.get(key, default)


# 全局单例
_secure_loader = None


def get_secure_loader() -> SecureConfigLoader:
    """获取全局安全配置加载器实例"""
    global _secure_loader
    if _secure_loader is None:
        _secure_loader = SecureConfigLoader()
    return _secure_loader


def get_config_value(key: str, default: Any = None) -> Any:
    """
    便捷函数: 获取配置值(支持自动解密)
    
    Args:
        key: 配置键
        default: 默认值
        
    Returns:
        配置值
    """
    loader = get_secure_loader()
    return loader.get_config_value(key, default)


def load_config(env_path: str | Path = 'config/.env') -> Dict[str, str]:
    """
    便捷函数: 加载配置(支持自动解密)
    
    Args:
        env_path: .env文件路径
        
    Returns:
        配置字典
    """
    loader = get_secure_loader()
    return loader.load_env_file(env_path)
