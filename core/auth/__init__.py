"""
认证和权限抽象层

解决 core ↔ webnet 循环依赖问题

设计:
1. 在 core 中定义抽象的权限接口
2. webnet.AuthNet 实现这些接口
3. 通过依赖注入提供实现
4. 解耦核心业务逻辑和网络实现
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class PermissionProvider(ABC):
    """权限提供者抽象接口"""
    
    @abstractmethod
    def check_permission(self, user_id: str, permission: str) -> bool:
        """检查用户是否有特定权限"""
        pass
    
    @abstractmethod
    def get_user_permissions(self, user_id: str) -> List[str]:
        """获取用户所有权限"""
        pass
    
    @abstractmethod
    def grant_permission(self, user_id: str, permission: str) -> bool:
        """授予用户权限"""
        pass
    
    @abstractmethod
    def revoke_permission(self, user_id: str, permission: str) -> bool:
        """撤销用户权限"""
        pass


class AuthProvider(ABC):
    """认证提供者抽象接口"""
    
    @abstractmethod
    def authenticate(self, credentials: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """认证用户"""
        pass
    
    @abstractmethod
    def create_user(self, user_data: Dict[str, Any]) -> bool:
        """创建用户"""
        pass
    
    @abstractmethod
    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """更新用户"""
        pass


class UserMapper(ABC):
    """用户映射器抽象接口"""
    
    @abstractmethod
    def map_to_unified_id(self, platform: str, user_id: str) -> str:
        """将平台用户ID映射为统一ID"""
        pass
    
    @abstractmethod
    def map_from_unified_id(self, unified_id: str) -> Dict[str, str]:
        """将统一ID映射回平台用户ID"""
        pass
    
    @abstractmethod
    def get_user_info(self, unified_id: str) -> Dict[str, Any]:
        """获取用户信息"""
        pass


# 全局提供者实例
_permission_provider: Optional[PermissionProvider] = None
_auth_provider: Optional[AuthProvider] = None
_user_mapper: Optional[UserMapper] = None


def set_permission_provider(provider: PermissionProvider) -> None:
    """设置权限提供者"""
    global _permission_provider
    _permission_provider = provider


def get_permission_provider() -> Optional[PermissionProvider]:
    """获取权限提供者"""
    return _permission_provider


def set_auth_provider(provider: AuthProvider) -> None:
    """设置认证提供者"""
    global _auth_provider
    _auth_provider = provider


def get_auth_provider() -> Optional[AuthProvider]:
    """获取认证提供者"""
    return _auth_provider


def set_user_mapper(mapper: UserMapper) -> None:
    """设置用户映射器"""
    global _user_mapper
    _user_mapper = mapper


def get_user_mapper() -> Optional[UserMapper]:
    """获取用户映射器"""
    return _user_mapper


# 便捷函数
def check_permission(user_id: str, permission: str) -> bool:
    """检查权限（便捷函数）"""
    provider = get_permission_provider()
    if provider:
        return provider.check_permission(user_id, permission)
    # 默认允许（降级处理）
    return True


def map_to_unified_id(platform: str, user_id: str) -> str:
    """映射到统一ID（便捷函数）"""
    mapper = get_user_mapper()
    if mapper:
        return mapper.map_to_unified_id(platform, user_id)
    # 默认映射格式
    return f"{platform}_{user_id}"