"""
AIGC Auth Legacy System Adapter

提供旧系统接入支持，包括：
1. 字段映射配置
2. 用户数据同步
3. 密码处理策略
4. Webhook 推送支持
"""

import os
import hmac
import hashlib
import json
import logging
import requests
from typing import Optional, List, Dict, Any, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)
def setLogger(log):
    global logger
    logger = log

class PasswordMode(Enum):
    """密码处理模式"""
    UNIFIED = "unified"  # 统一初始密码
    CUSTOM_MAPPING = "custom_mapping"  # 自定义映射函数


class SyncDirection(Enum):
    """同步方向"""
    AUTH_TO_LEGACY = "auth_to_legacy"  # aigc-auth → 旧系统
    LEGACY_TO_AUTH = "legacy_to_auth"  # 旧系统 → aigc-auth
    BIDIRECTIONAL = "bidirectional"  # 双向同步


@dataclass
class FieldMapping:
    """字段映射配置"""
    auth_field: str  # aigc-auth 字段名
    legacy_field: str  # 旧系统字段名
    transform_to_legacy: Optional[Callable[[Any], Any]] = None  # auth → legacy 转换函数
    transform_to_auth: Optional[Callable[[Any], Any]] = None  # legacy → auth 转换函数
    required: bool = False  # 是否必填
    default_value: Any = None  # 默认值


@dataclass
class SyncConfig:
    """同步配置"""
    # 基本配置
    enabled: bool = True
    direction: SyncDirection = SyncDirection.AUTH_TO_LEGACY
    
    # 字段映射
    field_mappings: List[FieldMapping] = field(default_factory=list)
    
    # 唯一标识字段（用于匹配用户）
    unique_field: str = "username"
    
    # 密码处理
    password_mode: PasswordMode = PasswordMode.UNIFIED
    unified_password: str = "Abc@123456"  # 统一初始密码
    password_mapper: Optional[Callable[[Dict], str]] = None  # 自定义密码映射函数（接收用户数据字典）
    password_is_hashed: bool = False  # password_mapper 返回的是否已经是加密后的密码
    
    # Webhook 配置
    webhook_enabled: bool = False
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    webhook_retry_count: int = 3
    webhook_timeout: int = 10


@dataclass
class LegacyUserData:
    """旧系统用户数据"""
    data: Dict[str, Any]
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        return self.data.copy()


@dataclass
class SyncResult:
    """同步结果"""
    success: bool
    user_id: Optional[int] = None
    auth_user_id: Optional[int] = None
    legacy_user_id: Optional[Any] = None
    message: str = ""
    errors: List[str] = field(default_factory=list)


class LegacySystemAdapter(ABC):
    """
    旧系统适配器抽象基类
    
    接入系统需要继承此类并实现以下方法：
    - get_user_by_username_async
    - _create_user_async
    - _update_user_async
    - _delete_user_async
    - get_all_users_async
    """
    
    def __init__(self, sync_config: SyncConfig, auth_client=None):
        """
        初始化适配器
        
        Args:
            sync_config: 同步配置
            auth_client: AigcAuthClient 实例（可选，用于批量同步）
        """
        self.config = sync_config
        self.auth_client = auth_client
    
    @abstractmethod
    async def get_user_by_username_async(self, username: str) -> Optional[LegacyUserData]:
        """异步获取用户（子类必须实现）
        
        Args:
            username: 用户名
            
        Returns:
            Optional[LegacyUserData]: 用户数据，不存在返回 None
        """
        logger.info(f"Fetching user by username asynchronously: {username}")
        raise NotImplementedError("Subclass must implement get_user_by_username_async method")
    
    @abstractmethod
    async def _create_user_async(self, user_data: Dict[str, Any]) -> Optional[Any]:
        """异步创建用户（子类必须实现）
        
        Args:
            user_data: 用户数据字典
            
        Returns:
            Optional[Any]: 创建的用户 ID 或其他标识
        """
        logger.info(f"Creating user with data: {user_data}")
        raise NotImplementedError("Subclass must implement _create_user_async method")
    
    @abstractmethod
    async def _update_user_async(self, username: str, user_data: Dict[str, Any]) -> bool:
        """异步更新用户（子类必须实现）
        
        Args:
            username: 用户名
            user_data: 要更新的用户数据
            
        Returns:
            bool: 更新成功返回 True
        """
        logger.info(f"Updating user: {username} with data: {user_data}")
        raise NotImplementedError("Subclass must implement _update_user_async method")
    
    @abstractmethod
    async def _delete_user_async(self, username: str) -> bool:
        """异步删除用户（子类必须实现）
        
        Args:
            username: 用户名
            
        Returns:
            bool: 删除成功返回 True
        """
        logger.info(f"Deleting user: {username}")
        raise NotImplementedError("Subclass must implement _delete_user_async method")
    
    @abstractmethod
    async def get_all_users_async(self) -> List[LegacyUserData]:
        """获取所有用户（子类必须实现，用于批量同步）
        
        Returns:
            List[LegacyUserData]: 所有用户数据列表
        """
        logger.info("Fetching all users from legacy system asynchronously")
        raise NotImplementedError("Subclass must implement get_all_users_async method")
    
    async def upsert_user_async(self, user_data: Dict[str, Any], auth_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """异步创建或更新用户（存在则更新，不存在则新增）
        
        这是一个默认实现，子类可以选择性覆盖以优化性能。
        
        Args:
            user_data: 用户数据字典（必须包含 username）
            auth_data: 鉴权系统用户数据字典（可选）
        Returns:
            Dict: 操作结果 {"created": bool, "user_id": Any}
        """
        username = user_data.get("username")
        if not username:
            logger.error("username is required for upsert operation")
            raise ValueError("username is required for upsert operation")
        
        # 检查用户是否存在
        existing = await self.get_user_by_username_async(username)
        
        if existing:
            # 用户存在，执行更新
            if not auth_data or auth_data.get("updatedFields") is None or len(auth_data.get("updatedFields")) == 0:
                logger.info(f"No updatedFields provided for user: {username}, skipping update")
                # 如果没有提供 auth_data 或 updatedFields，则不更新
                return {"created": False, "user_id": existing.get("id")}
            await self._update_user_async(username, user_data)
            return {"created": False, "user_id": existing.get("id")}
        else:
            # 用户不存在，执行创建
            user_id = await self._create_user_async(user_data)
            return {"created": True, "user_id": user_id}
    
    async def sync_user_to_auth(self, legacy_user: LegacyUserData) -> Dict[str, Any]:
        """同步单个旧系统用户到 aigc-auth（默认实现）
        
        子类可以选择性覆盖此方法以自定义同步逻辑。
        
        Args:
            legacy_user: 旧系统用户数据
        Returns:
            Dict: 同步结果
        """
        if not self.auth_client:
            logger.error("auth_client is required for sync_user_to_auth")
            raise ValueError("auth_client is required for sync_user_to_auth. Please provide it in constructor.")
        
        logger.info(f"Syncing legacy user to auth: {legacy_user.to_dict()}")
        auth_data = self.transform_legacy_to_auth(legacy_user)
        
        # 获取密码（支持新的元组返回格式）
        password_result = self.get_password_for_sync(legacy_user)
        if isinstance(password_result, tuple):
            password, is_hashed = password_result
        else:
            password, is_hashed = password_result, False
        
        # 根据是否已加密选择不同的字段
        if is_hashed:
            auth_data["password_hashed"] = password
        else:
            auth_data["password"] = password
        
        result = self.auth_client.sync_user_to_auth(auth_data)
        logger.info(f"Sync result for user {legacy_user.get('username')}: {result}")
        
        return result
    
    async def batch_sync_to_auth(self) -> Dict[str, Any]:
        """批量同步旧系统用户到 aigc-auth（默认实现）
        
        子类可以选择性覆盖此方法以自定义同步逻辑。
        
        Returns:
            Dict: 同步结果统计
        """
        if not self.auth_client:
            logger.error("auth_client is required for batch_sync_to_auth")
            raise ValueError("auth_client is required for batch_sync_to_auth. Please provide it in constructor.")
        
        logger.info("Starting batch sync from legacy system to aigc-auth")
        users = await self.get_all_users_async()
        
        results = {
            "total": len(users),
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }
        
        for user in users:
            try:
                # 将 dict 转换为 LegacyUserData 对象
                if isinstance(user, dict):
                    legacy_user = LegacyUserData(data=user)
                else:
                    legacy_user = user
                    
                result = await self.sync_user_to_auth(legacy_user)
                logger.info(f"Sync result for user {user.get('username')}: {result}")
                
                if result.get("success"):
                    if result.get("created"):
                        results["success"] += 1
                    else:
                        results["skipped"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "user": user.get("username"),
                        "error": result.get("message")
                    })
            except Exception as e:
                import traceback
                logger.error(f"Error syncing user {user.get('username')}: {e}\n{traceback.format_exc()}")
                results["failed"] += 1
                results["errors"].append({
                    "user": user.get("username"),
                    "error": str(e)
                })
        
        return results
    
    async def handle_webhook(self, event: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理来自 aigc-auth 的 webhook 通知（默认实现）
        
        子类可以选择性覆盖此方法以自定义 webhook 处理逻辑。
        
        Args:
            event: 事件类型，如 "user.created", "user.updated", "user.deleted"
            data: 事件数据（用户信息）
            
        Returns:
            Dict: 处理结果
        """
        logger.info(f"Handling webhook event: {event} with data: {data}")
        if event == "user.created" or event == "user.updated" or event == "user.login":
            # 转换数据格式
            legacy_data = self.transform_auth_to_legacy(data)
            
            # 获取密码
            password_result = self.get_password_for_sync(legacy_data)
            if isinstance(password_result, tuple):
                password, is_hashed = password_result
            else:
                password, is_hashed = password_result, False
            if is_hashed:
                legacy_data["password_hashed"] = password
            else:
                legacy_data["password"] = password
            
            # 创建或更新用户
            logger.info(f"Handling {event} event for user: {legacy_data}")
            result = await self.upsert_user_async(legacy_data, data)
            
            return {
                "success": True,
                "message": "User created" if result["created"] else "User updated",
                "created": result["created"],
                "user_id": result["user_id"]
            }
        
        elif event == "user.deleted":
            logger.info("Handling user.deleted event")
            # 禁用用户而不是删除
            username = data.get("username")
            if not username:
                logger.error("username is required for user.deleted event")
                logger.error("username is required for user.deleted event")
                return {"success": False, "message": "username is required for user.deleted event"}
            logger.info(f"Disabling user: {username}")
            await self._delete_user_async(username)
            
            return {"success": True, "message": "User disabled"}
        
        elif event == "user.init_sync_auth":
            logger.info("Handling user.init_sync_auth event")
            # 初始化同步：批量同步旧系统用户到 aigc-auth
            if not self.auth_client:
                logger.error("auth_client is required for init_sync_auth event")
                return {"success": False, "message": "auth_client is required for init_sync_auth event. Please provide it in constructor."}
            
            results = await self.batch_sync_to_auth()
            
            return {
                "success": True,
                "message": f"Batch sync completed: {results['success']} created, {results['skipped']} skipped, {results['failed']} failed",
                "results": results
            }
        
        return {"success": True, "message": "Event ignored"}
    
    def transform_auth_to_legacy(self, auth_user: Dict[str, Any]) -> Dict[str, Any]:
        """将 aigc-auth 用户数据转换为旧系统格式"""
        result = {}
        
        for mapping in self.config.field_mappings:
            auth_value = auth_user.get(mapping.auth_field)
            
            if auth_value is None:
                if mapping.required and mapping.default_value is None:
                    raise ValueError(f"Required field '{mapping.auth_field}' is missing")
                auth_value = mapping.default_value
            
            if mapping.transform_to_legacy:
                auth_value = mapping.transform_to_legacy(auth_value)
            
            if auth_value is not None:
                result[mapping.legacy_field] = auth_value
        logger.info(f"Transformed auth user({auth_user}) to legacy format: {result}")
        return result
    
    def transform_legacy_to_auth(self, legacy_user: LegacyUserData) -> Dict[str, Any]:
        """将旧系统用户数据转换为 aigc-auth 格式"""
        result = {}
        
        for mapping in self.config.field_mappings:
            legacy_value = legacy_user.get(mapping.legacy_field)
            
            if legacy_value is None:
                if mapping.required and mapping.default_value is None:
                    raise ValueError(f"Required field '{mapping.legacy_field}' is missing")
                legacy_value = mapping.default_value
            
            if mapping.transform_to_auth:
                legacy_value = mapping.transform_to_auth(legacy_value)
            
            if legacy_value is not None:
                result[mapping.auth_field] = legacy_value
        logger.info(f"Transformed legacy user({legacy_user}) to auth format: {result}")
        return result
    
    def get_password_for_sync(self, legacy_user: Optional[LegacyUserData] = None) -> tuple:
        """获取同步时使用的密码
        
        Returns:
            tuple: (password, is_hashed)
                - password: 密码字符串
                - is_hashed: 是否已经是加密后的密码
        """
        if self.config.password_mode == PasswordMode.UNIFIED:
            return (self.config.unified_password, False)
        elif self.config.password_mode == PasswordMode.CUSTOM_MAPPING:
            if self.config.password_mapper and legacy_user:
                # 兼容 dict 和 LegacyUserData 两种类型
                if isinstance(legacy_user, dict):
                    user_data = legacy_user
                elif isinstance(legacy_user, LegacyUserData):
                    user_data = legacy_user.data
                else:
                    user_data = legacy_user
                password = self.config.password_mapper(user_data)
                return (password, self.config.password_is_hashed)
            return (self.config.unified_password, False)
        return (self.config.unified_password, False)


class WebhookSender:
    """Webhook 发送器"""
    
    def __init__(self, config: SyncConfig):
        self.config = config
    
    def generate_signature(self, payload: str) -> str:
        """生成 HMAC-SHA256 签名"""
        if not self.config.webhook_secret:
            return ""
        
        return hmac.new(
            self.config.webhook_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def send(self, event_type: str, data: Dict[str, Any]) -> bool:
        """发送 webhook 通知"""
        if not self.config.webhook_enabled or not self.config.webhook_url:
            return False
        
        payload = json.dumps({
            "event": event_type,
            "data": data
        }, ensure_ascii=False)
        
        signature = self.generate_signature(payload)
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": event_type
        }
        
        for attempt in range(self.config.webhook_retry_count):
            try:
                response = requests.post(
                    self.config.webhook_url,
                    data=payload,
                    headers=headers,
                    timeout=self.config.webhook_timeout
                )
                
                if response.status_code == 200:
                    logger.info(f"Webhook sent successfully: {event_type}")
                    return True
                else:
                    logger.warning(f"Webhook failed with status {response.status_code}: {response.text}")
                    
            except requests.RequestException as e:
                logger.error(f"Webhook request failed (attempt {attempt + 1}): {e}")
        
        return False


class UserSyncService:
    """
    用户同步服务
    
    提供以下功能：
    1. 登录时自动同步（auth → legacy）
    2. 初始化批量同步（legacy → auth）
    3. Webhook 增量推送
    """
    
    def __init__(
        self,
        auth_client,  # AigcAuthClient
        legacy_adapter: LegacySystemAdapter
    ):
        self.auth_client = auth_client
        self.adapter = legacy_adapter
        self.config = legacy_adapter.config
        self.webhook_sender = WebhookSender(self.config)
        
        # 确保 adapter 也持有 auth_client 引用
        if not self.adapter.auth_client:
            self.adapter.auth_client = auth_client
    
    def _user_info_to_dict(self, user_info) -> Dict[str, Any]:
        """将 UserInfo 对象转换为字典"""
        return {
            "id": user_info.id,
            "username": user_info.username,
            "nickname": user_info.nickname,
            "email": user_info.email,
            "phone": user_info.phone,
            "avatar": user_info.avatar,
            "roles": user_info.roles,
            "permissions": user_info.permissions,
            "department": user_info.department,
            "company": user_info.company,
            "is_admin": user_info.is_admin,
            "status": user_info.status,
        }
    
    async def sync_on_login_async(self, auth_user_info) -> Dict[str, Any]:
        """
        登录时异步同步用户到旧系统
        
        当用户通过 aigc-auth 登录成功后调用，
        如果旧系统没有该用户则自动创建。
        
        Args:
            auth_user_info: aigc-auth 返回的 UserInfo 对象
            
        Returns:
            Dict: 同步结果
        """
        if not self.config.enabled:
            return {"success": True, "message": "Sync disabled"}
        
        # 转换用户数据
        auth_data = self._user_info_to_dict(auth_user_info)
        legacy_data = self.adapter.transform_auth_to_legacy(auth_data)
        
        # 获取密码（支持新的元组返回格式）
        password_result = self.adapter.get_password_for_sync()
        if isinstance(password_result, tuple):
            password, is_hashed = password_result
        else:
            password, is_hashed = password_result, False
        legacy_data["password"] = password
        
        # 使用 upsert 方法（存在则更新，不存在则创建）
        result = await self.adapter.upsert_user_async(legacy_data, auth_data)
        
        return {
            "success": True,
            "auth_user_id": auth_user_info.id,
            "legacy_user_id": result["user_id"],
            "created": result["created"],
            "message": "User created" if result["created"] else "User updated"
        }
    
    async def batch_sync_to_auth_async(self) -> Dict[str, Any]:
        """
        异步批量同步旧系统用户到 aigc-auth
        
        直接委托给 adapter 的默认实现
        
        Returns:
            Dict: 同步结果统计
        """
        return await self.adapter.batch_sync_to_auth()

# ============ 预设字段映射 ============

def create_default_field_mappings() -> List[FieldMapping]:
    """创建默认字段映射配置（通用基础映射）"""
    return [
        FieldMapping(
            auth_field="username",
            legacy_field="username",
            required=True
        ),
        FieldMapping(
            auth_field="email",
            legacy_field="email"
        ),
        FieldMapping(
            auth_field="nickname",
            legacy_field="nickname"
        ),
        FieldMapping(
            auth_field="phone",
            legacy_field="phone"
        ),
        FieldMapping(
            auth_field="avatar",
            legacy_field="avatar"
        ),
        FieldMapping(
            auth_field="company",
            legacy_field="company"
        ),
        FieldMapping(
            auth_field="department",
            legacy_field="department"
        ),
    ]


# ============ 便捷函数 ============

def create_sync_config(
    field_mappings: List[FieldMapping] = None,
    password_mode: PasswordMode = PasswordMode.UNIFIED,
    unified_password: str = "Abc@123456",
    webhook_url: Optional[str] = None,
    webhook_secret: Optional[str] = None,
    direction: SyncDirection = SyncDirection.AUTH_TO_LEGACY,
    **kwargs
) -> SyncConfig:
    """
    创建同步配置的便捷函数
    
    Args:
        field_mappings: 字段映射列表，默认使用通用映射
        password_mode: 密码处理模式
        unified_password: 统一初始密码
        webhook_url: Webhook 接收地址
        webhook_secret: Webhook 签名密钥
        direction: 同步方向
        
    Returns:
        SyncConfig: 同步配置对象
    """
    return SyncConfig(
        enabled=True,
        direction=direction,
        field_mappings=field_mappings or create_default_field_mappings(),
        password_mode=password_mode,
        unified_password=unified_password,
        webhook_enabled=bool(webhook_url),
        webhook_url=webhook_url,
        webhook_secret=webhook_secret,
        **kwargs
    )
