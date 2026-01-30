"""
AIGC Auth Python SDK

使用方法:
    from sdk import AigcAuthClient, require_auth

    # 创建客户端
    client = AigcAuthClient(app_id="your_app_id", app_secret="your_app_secret")

    # 验证 token
    result = client.verify_token(token)

    # 获取用户信息
    user_info = client.get_user_info(token)

    # FastAPI 中间件使用
    @app.get("/protected")
    @require_auth(client)
    def protected_route(user_info: dict):
        return {"user": user_info}
        
旧系统接入:
    from sdk import AigcAuthClient
    from sdk.legacy_adapter import (
        LegacySystemAdapter,
        SyncConfig,
        UserSyncService,
        FieldMapping,
        create_sync_config,
        create_default_field_mappings
    )
    
    # 创建自定义字段映射（根据接入系统的用户表定制）
    field_mappings = create_default_field_mappings()
    # 或自定义: field_mappings = [FieldMapping(...), ...]
    
    sync_config = create_sync_config(
        field_mappings=field_mappings,
        webhook_url="https://your-domain.com/webhook"
    )
    
    # 实现适配器并创建同步服务
    adapter = YourLegacyAdapter(sync_config)
    sync_service = UserSyncService(client, adapter)
"""

from .sdk import (
    AigcAuthClient,
    require_auth,
    AuthMiddleware,
    UserInfo,
    TokenVerifyResult,
    AigcAuthError,
    create_fastapi_auth_dependency
)

from .legacy_adapter import (
    LegacySystemAdapter,
    LegacyUserData,
    SyncConfig,
    SyncDirection,
    PasswordMode,
    FieldMapping,
    UserSyncService,
    WebhookSender,
    SyncResult,
    create_sync_config,
    create_default_field_mappings,
)
# fastapi 相关功能是可选的，如果未安装 fastapi 则跳过
try:
    from .webhook import (
        register_webhook_router,
        verify_webhook_signature,
    )
    _fastapi_available = True
except ImportError:
    _fastapi_available = False
    # 提供占位符，避免 __all__ 导出时出错
    register_webhook_router = None
    verify_webhook_signature = None

# Flask 相关功能是可选的，如果未安装 flask 则跳过
try:
    from .webhook_flask import (
        create_flask_webhook_blueprint,
        register_flask_webhook_routes,
    )
    _flask_available = True
except ImportError:
    _flask_available = False
    # 提供占位符，避免 __all__ 导出时出错
    create_flask_webhook_blueprint = None
    register_flask_webhook_routes = None

def setLogger(log):
    """
    统一设置所有模块的 logger
    
    Args:
        log: logging.Logger 实例
        
    使用示例:
        import logging
        from huace_aigc_auth_client import setLogger
        
        logger = logging.getLogger("my_app")
        logger.setLevel(logging.INFO)
        
        # 设置 SDK 所有模块使用该 logger
        setLogger(logger)
    """
    try:
        from .sdk import setLogger as sdk_setLogger
        sdk_setLogger(log)
    except Exception as e:
        print(f"Failed to set logger for sdk module: {e}")
    
    try:
        from .legacy_adapter import setLogger as legacy_setLogger
        legacy_setLogger(log)
    except Exception as e:
        print(f"Failed to set logger for legacy_adapter module: {e}")
    
    if _fastapi_available:
        try:
            from .webhook import setLogger as webhook_setLogger
            webhook_setLogger(log)
        except Exception as e:
            print(f"Failed to set logger for webhook module: {e}")
    
    # 只在 flask 可用时设置 flask 模块的 logger
    if _flask_available:
        try:
            from .webhook_flask import setLogger as webhook_flask_setLogger
            webhook_flask_setLogger(log)
        except Exception as e:
            print(f"Failed to set logger for webhook_flask module: {e}")


__all__ = [
    # 核心类
    "AigcAuthClient",
    "require_auth",
    "AuthMiddleware",
    "UserInfo",
    "TokenVerifyResult",
    "AigcAuthError",
    "create_fastapi_auth_dependency",
    # 旧系统接入
    "LegacySystemAdapter",
    "LegacyUserData",
    "SyncConfig",
    "SyncDirection",
    "PasswordMode",
    "FieldMapping",
    "UserSyncService",
    "WebhookSender",
    "SyncResult",
    "create_sync_config",
    "create_default_field_mappings",
    # Webhook 接收 (FastAPI)
    "register_webhook_router",
    "verify_webhook_signature",
    # Webhook 接收 (Flask)
    "create_flask_webhook_blueprint",
    "register_flask_webhook_routes",
    # Logger 设置
    "setLogger",
]
__version__ = "1.1.14"
