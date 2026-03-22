"""
全量配置加密系统 - 安全加固第一阶段

设计目标:
1. 支持环境变量和配置文件加密
2. 提供透明的加密/解密机制
3. 支持密钥轮换和版本控制
4. 与现有配置系统无缝集成
"""

import os
import json
import base64
import hashlib
import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

# 加密库
try:
    from cryptography.fernet import Fernet, MultiFernet
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

logger = logging.getLogger(__name__)


class EncryptionAlgorithm(Enum):
    """加密算法"""
    AES256_GCM = "aes256_gcm"      # AES-256-GCM
    CHACHA20 = "chacha20"          # ChaCha20-Poly1305
    FERNET = "fernet"             # Fernet (AES-128-CBC)
    AES256_CBC = "aes256_cbc"     # AES-256-CBC


class KeySource(Enum):
    """密钥来源"""
    ENV_VAR = "env_var"           # 环境变量
    KEY_FILE = "key_file"         # 密钥文件
    KMS = "kms"                   # 密钥管理服务
    HSM = "hsm"                   # 硬件安全模块


@dataclass
class EncryptionConfig:
    """加密配置"""
    algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES256_GCM
    key_source: KeySource = KeySource.ENV_VAR
    key_env_var: str = "MIYA_ENCRYPTION_KEY"
    key_file_path: Optional[Path] = None
    key_rotation_days: int = 90  # 密钥轮换天数
    enable_versioning: bool = True  # 启用版本控制
    current_key_version: int = 1
    max_key_versions: int = 3
    enable_memory_protection: bool = True  # 内存保护


@dataclass
class EncryptedValue:
    """加密值"""
    version: int = 1
    algorithm: str = ""
    ciphertext: str = ""
    iv: str = ""  # 初始化向量
    auth_tag: str = ""  # 认证标签 (GCM/Poly1305)
    key_id: str = ""  # 密钥标识
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConfigEncryptor:
    """配置加密器"""
    
    # 敏感字段模式
    SENSITIVE_PATTERNS = [
        "password", "passwd", "pwd",
        "token", "secret", "key",
        "credential", "auth",
        "private", "secure",
        "api_key", "access_key",
        "client_secret", "refresh_token",
    ]
    
    def __init__(self, config: Optional[EncryptionConfig] = None):
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("加密功能需要 cryptography 库")
        
        self.config = config or EncryptionConfig()
        self._keys: Dict[int, bytes] = {}  # 版本 -> 密钥
        self._current_key: Optional[bytes] = None
        
        # 初始化密钥
        self._load_keys()
        
        logger.info(f"[配置加密] 初始化完成，算法={self.config.algorithm.value}")
    
    def _load_keys(self):
        """加载密钥"""
        # 从环境变量加载主密钥
        if self.config.key_source == KeySource.ENV_VAR:
            master_key = os.getenv(self.config.key_env_var)
            if not master_key:
                logger.warning(f"[配置加密] 环境变量 {self.config.key_env_var} 未设置")
                # 生成临时密钥（仅用于开发）
                if os.getenv("MIYA_DEVELOPMENT") == "1":
                    master_key = Fernet.generate_key().decode()
                    logger.warning("[配置加密] 使用临时开发密钥")
                else:
                    raise ValueError(f"加密密钥未设置: {self.config.key_env_var}")
            
            # 派生密钥（支持版本控制）
            self._derive_keys(master_key)
        
        # 从文件加载密钥
        elif self.config.key_source == KeySource.KEY_FILE:
            if not self.config.key_file_path:
                raise ValueError("密钥文件路径未设置")
            
            if not self.config.key_file_path.exists():
                logger.warning(f"[配置加密] 密钥文件不存在: {self.config.key_file_path}")
                # 创建新密钥文件
                self._generate_key_file()
            
            self._load_key_file()
        
        # 设置当前密钥
        self._current_key = self._keys.get(self.config.current_key_version)
        if not self._current_key:
            raise ValueError(f"当前密钥版本 {self.config.current_key_version} 不存在")
    
    def _derive_keys(self, master_key: str):
        """从主密钥派生版本化密钥"""
        for version in range(1, self.config.max_key_versions + 1):
            # 使用版本号作为盐
            salt = f"miya_config_v{version}".encode()
            
            # 使用PBKDF2派生密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,  # 256位
                salt=salt,
                iterations=100000,
            )
            
            derived_key = kdf.derive(master_key.encode())
            self._keys[version] = derived_key
            
            logger.debug(f"[配置加密] 派生密钥版本 {version}")
    
    def _generate_key_file(self):
        """生成密钥文件"""
        try:
            # 生成主密钥
            master_key = Fernet.generate_key().decode()
            
            # 创建密钥文件内容
            key_data = {
                "format_version": 1,
                "key_algorithm": "aes256",
                "keys": {
                    "v1": {
                        "key": master_key,
                        "created_at": "2025-01-01T00:00:00Z",
                        "active": True
                    }
                }
            }
            
            # 写入文件
            self.config.key_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config.key_file_path, 'w') as f:
                json.dump(key_data, f, indent=2)
            
            # 设置文件权限（仅所有者可读写）
            if hasattr(os, 'chmod'):
                os.chmod(self.config.key_file_path, 0o600)
            
            logger.info(f"[配置加密] 生成密钥文件: {self.config.key_file_path}")
            
        except Exception as e:
            logger.error(f"[配置加密] 生成密钥文件失败: {e}")
            raise
    
    def _load_key_file(self):
        """加载密钥文件"""
        try:
            with open(self.config.key_file_path, 'r') as f:
                key_data = json.load(f)
            
            # 验证格式
            if key_data.get("format_version") != 1:
                raise ValueError("不支持的密钥文件格式")
            
            # 加载密钥
            for key_id, key_info in key_data.get("keys", {}).items():
                if key_info.get("active", False):
                    version = int(key_id[1:])  # 从 "v1" 提取 1
                    key_value = key_info.get("key", "").encode()
                    
                    # 派生实际加密密钥
                    kdf = PBKDF2HMAC(
                        algorithm=hashes.SHA256(),
                        length=32,
                        salt=f"miya_file_key_v{version}".encode(),
                        iterations=100000,
                    )
                    
                    derived_key = kdf.derive(key_value)
                    self._keys[version] = derived_key
                    
                    logger.debug(f"[配置加密] 从文件加载密钥版本 {version}")
        
        except Exception as e:
            logger.error(f"[配置加密] 加载密钥文件失败: {e}")
            raise
    
    def _is_sensitive_key(self, key: str) -> bool:
        """检查是否为敏感键"""
        key_lower = key.lower()
        return any(pattern in key_lower for pattern in self.SENSITIVE_PATTERNS)
    
    def _is_sensitive_value(self, value: Any) -> bool:
        """检查是否为敏感值"""
        if not isinstance(value, str):
            return False
        
        # 检查长度（太短可能不是敏感信息）
        if len(value) < 8:
            return False
        
        # 检查是否为Base64格式（可能已经是加密的）
        try:
            if len(value) % 4 == 0:
                base64.b64decode(value)
                return False  # 已经是Base64，可能已加密
        except:
            pass
        
        # 检查是否为JSON Web Token格式
        if value.count('.') == 2 and len(value) > 50:
            return False  # 可能是JWT
        
        return True
    
    def encrypt_value(self, value: Any, key_version: Optional[int] = None) -> EncryptedValue:
        """加密值"""
        if not self._current_key:
            raise ValueError("加密器未初始化")
        
        key_version = key_version or self.config.current_key_version
        key = self._keys.get(key_version)
        if not key:
            raise ValueError(f"密钥版本 {key_version} 不存在")
        
        # 序列化值
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, ensure_ascii=False)
        else:
            value_str = str(value)
        
        value_bytes = value_str.encode('utf-8')
        
        try:
            if self.config.algorithm == EncryptionAlgorithm.AES256_GCM:
                return self._encrypt_aes_gcm(value_bytes, key, key_version)
            elif self.config.algorithm == EncryptionAlgorithm.CHACHA20:
                return self._encrypt_chacha20(value_bytes, key, key_version)
            elif self.config.algorithm == EncryptionAlgorithm.FERNET:
                return self._encrypt_fernet(value_bytes, key, key_version)
            else:
                raise ValueError(f"不支持的算法: {self.config.algorithm}")
        
        except Exception as e:
            logger.error(f"[配置加密] 加密失败: {e}")
            raise
    
    def _encrypt_aes_gcm(self, data: bytes, key: bytes, version: int) -> EncryptedValue:
        """AES-256-GCM加密"""
        # 生成随机IV（12字节用于GCM）
        iv = os.urandom(12)
        
        # 创建AESGCM实例
        aesgcm = AESGCM(key)
        
        # 加密（GCM模式自动生成认证标签）
        ciphertext = aesgcm.encrypt(iv, data, None)
        
        # 分离密文和认证标签（GCM的认证标签是最后16字节）
        tag = ciphertext[-16:]
        ciphertext = ciphertext[:-16]
        
        return EncryptedValue(
            version=version,
            algorithm="aes256_gcm",
            ciphertext=base64.b64encode(ciphertext).decode(),
            iv=base64.b64encode(iv).decode(),
            auth_tag=base64.b64encode(tag).decode(),
            key_id=f"v{version}",
            metadata={"mode": "gcm"}
        )
    
    def _encrypt_chacha20(self, data: bytes, key: bytes, version: int) -> EncryptedValue:
        """ChaCha20-Poly1305加密"""
        # 生成随机nonce（12字节用于ChaCha20）
        nonce = os.urandom(12)
        
        # 创建ChaCha20实例
        chacha = ChaCha20Poly1305(key)
        
        # 加密（Poly1305模式自动生成认证标签）
        ciphertext = chacha.encrypt(nonce, data, None)
        
        # 分离密文和认证标签
        tag = ciphertext[-16:]
        ciphertext = ciphertext[:-16]
        
        return EncryptedValue(
            version=version,
            algorithm="chacha20",
            ciphertext=base64.b64encode(ciphertext).decode(),
            iv=base64.b64encode(nonce).decode(),
            auth_tag=base64.b64encode(tag).decode(),
            key_id=f"v{version}",
            metadata={"mode": "poly1305"}
        )
    
    def _encrypt_fernet(self, data: bytes, key: bytes, version: int) -> EncryptedValue:
        """Fernet加密"""
        # Fernet需要32字节密钥
        if len(key) != 32:
            # 派生Fernet密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=f"fernet_salt_v{version}".encode(),
                iterations=100000,
            )
            fernet_key = kdf.derive(key)
        else:
            fernet_key = key
        
        # 创建Fernet实例
        fernet = Fernet(base64.urlsafe_b64encode(fernet_key))
        
        # 加密
        ciphertext = fernet.encrypt(data)
        
        return EncryptedValue(
            version=version,
            algorithm="fernet",
            ciphertext=ciphertext.decode(),
            key_id=f"v{version}",
            metadata={"mode": "cbc"}
        )
    
    def decrypt_value(self, encrypted_value: Union[EncryptedValue, Dict[str, Any]]) -> Any:
        """解密值"""
        if isinstance(encrypted_value, dict):
            encrypted_value = EncryptedValue(**encrypted_value)
        
        key_version = encrypted_value.version
        key = self._keys.get(key_version)
        if not key:
            raise ValueError(f"密钥版本 {key_version} 不存在")
        
        try:
            if encrypted_value.algorithm == "aes256_gcm":
                result = self._decrypt_aes_gcm(encrypted_value, key)
            elif encrypted_value.algorithm == "chacha20":
                result = self._decrypt_chacha20(encrypted_value, key)
            elif encrypted_value.algorithm == "fernet":
                result = self._decrypt_fernet(encrypted_value, key)
            else:
                raise ValueError(f"不支持的算法: {encrypted_value.algorithm}")
            
            # 尝试解析为JSON
            try:
                return json.loads(result.decode('utf-8'))
            except:
                return result.decode('utf-8')
        
        except Exception as e:
            logger.error(f"[配置加密] 解密失败: {e}")
            raise
    
    def _decrypt_aes_gcm(self, encrypted: EncryptedValue, key: bytes) -> bytes:
        """AES-256-GCM解密"""
        # 解码数据
        ciphertext = base64.b64decode(encrypted.ciphertext)
        iv = base64.b64decode(encrypted.iv)
        tag = base64.b64decode(encrypted.auth_tag)
        
        # 合并密文和标签
        ciphertext_with_tag = ciphertext + tag
        
        # 创建AESGCM实例并解密
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(iv, ciphertext_with_tag, None)
    
    def _decrypt_chacha20(self, encrypted: EncryptedValue, key: bytes) -> bytes:
        """ChaCha20-Poly1305解密"""
        # 解码数据
        ciphertext = base64.b64decode(encrypted.ciphertext)
        nonce = base64.b64decode(encrypted.iv)
        tag = base64.b64decode(encrypted.auth_tag)
        
        # 合并密文和标签
        ciphertext_with_tag = ciphertext + tag
        
        # 创建ChaCha20实例并解密
        chacha = ChaCha20Poly1305(key)
        return chacha.decrypt(nonce, ciphertext_with_tag, None)
    
    def _decrypt_fernet(self, encrypted: EncryptedValue, key: bytes) -> bytes:
        """Fernet解密"""
        # Fernet需要32字节密钥
        if len(key) != 32:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=f"fernet_salt_v{encrypted.version}".encode(),
                iterations=100000,
            )
            fernet_key = kdf.derive(key)
        else:
            fernet_key = key
        
        # 创建Fernet实例并解密
        fernet = Fernet(base64.urlsafe_b64encode(fernet_key))
        return fernet.decrypt(encrypted.ciphertext.encode())
    
    def encrypt_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """加密配置字典"""
        encrypted_config = {}
        
        for key, value in config.items():
            if self._is_sensitive_key(key) and self._is_sensitive_value(value):
                # 加密敏感值
                encrypted_value = self.encrypt_value(value)
                encrypted_config[key] = {
                    "__encrypted__": True,
                    **encrypted_value.__dict__
                }
                logger.debug(f"[配置加密] 加密字段: {key}")
            else:
                # 保持原值
                encrypted_config[key] = value
        
        return encrypted_config
    
    def decrypt_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解密配置字典"""
        decrypted_config = {}
        
        for key, value in config.items():
            if isinstance(value, dict) and value.get("__encrypted__"):
                # 解密值
                try:
                    decrypted_value = self.decrypt_value(value)
                    decrypted_config[key] = decrypted_value
                    logger.debug(f"[配置加密] 解密字段: {key}")
                except Exception as e:
                    logger.error(f"[配置加密] 解密失败 {key}: {e}")
                    # 保持加密值（降级处理）
                    decrypted_config[key] = value
            else:
                # 保持原值
                decrypted_config[key] = value
        
        return decrypted_config
    
    def rotate_keys(self):
        """轮换密钥"""
        if not self.config.enable_versioning:
            logger.warning("[配置加密] 密钥版本控制未启用，无法轮换")
            return
        
        # 增加版本号
        new_version = max(self._keys.keys()) + 1
        
        # 生成新密钥
        if self.config.key_source == KeySource.ENV_VAR:
            # 从环境变量派生新密钥
            master_key = os.getenv(self.config.key_env_var)
            if not master_key:
                raise ValueError("无法轮换密钥：主密钥未设置")
            
            salt = f"miya_config_v{new_version}".encode()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            new_key = kdf.derive(master_key.encode())
            self._keys[new_version] = new_key
        
        # 更新当前版本
        self.config.current_key_version = new_version
        self._current_key = new_key
        
        # 清理旧密钥（保留最近3个版本）
        versions_to_keep = sorted(self._keys.keys())[-self.config.max_key_versions:]
        for version in list(self._keys.keys()):
            if version not in versions_to_keep:
                del self._keys[version]
        
        logger.info(f"[配置加密] 密钥已轮换到版本 {new_version}")


# 全局加密器实例
_global_encryptor: Optional[ConfigEncryptor] = None


def get_encryptor(config: Optional[EncryptionConfig] = None) -> ConfigEncryptor:
    """获取全局加密器"""
    global _global_encryptor
    
    if _global_encryptor is None:
        _global_encryptor = ConfigEncryptor(config)
    
    return _global_encryptor


def encrypt_config_value(value: Any, key_version: Optional[int] = None) -> Dict[str, Any]:
    """便捷函数：加密配置值"""
    encryptor = get_encryptor()
    encrypted = encryptor.encrypt_value(value, key_version)
    return {
        "__encrypted__": True,
        **encrypted.__dict__
    }


def decrypt_config_value(encrypted_data: Dict[str, Any]) -> Any:
    """便捷函数：解密配置值"""
    encryptor = get_encryptor()
    return encryptor.decrypt_value(encrypted_data)


def load_encrypted_config(file_path: Path) -> Dict[str, Any]:
    """加载加密配置文件"""
    if not file_path.exists():
        logger.warning(f"[配置加密] 配置文件不存在: {file_path}")
        return {}
    
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
        
        encryptor = get_encryptor()
        return encryptor.decrypt_config(config)
    
    except Exception as e:
        logger.error(f"[配置加密] 加载配置文件失败: {file_path}, error={e}")
        return {}


def save_encrypted_config(config: Dict[str, Any], file_path: Path):
    """保存加密配置文件"""
    try:
        encryptor = get_encryptor()
        encrypted_config = encryptor.encrypt_config(config)
        
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(encrypted_config, f, indent=2, ensure_ascii=False)
        
        # 设置文件权限
        if hasattr(os, 'chmod'):
            os.chmod(file_path, 0o600)
        
        logger.info(f"[配置加密] 配置文件已保存: {file_path}")
    
    except Exception as e:
        logger.error(f"[配置加密] 保存配置文件失败: {file_path}, error={e}")
        raise