# -*- coding: utf-8 -*-
"""
Flask Webhook 接口

提供 Flask 版本的 webhook 接收功能，用于接收 aigc-auth 的用户变更通知。
适用于使用 Flask 框架的项目。
"""

import os
import hmac
import hashlib
import logging
from typing import Callable, Dict, Any, Optional
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)
def setLogger(log):
    global logger
    logger = log

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    验证 webhook 签名
    
    Args:
        payload: 请求体（bytes）
        signature: 签名字符串
        secret: 密钥
        
    Returns:
        bool: 签名是否有效
    """
    if not secret:
        # 如果未配置密钥，跳过验证（开发环境）
        logger.warning("Webhook secret not configured, skipping signature verification")
        return True
    
    if not signature:
        return False
    
    expected = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)


def create_flask_webhook_blueprint(
    handler: Callable[[Dict[str, Any]], Dict[str, Any]],
    secret_env_key: str = "AIGC_AUTH_WEBHOOK_SECRET",
    url_prefix: str = "/api/webhook",
    blueprint_name: str = "aigc_auth_webhook"
) -> Blueprint:
    """
    创建 Flask Webhook Blueprint
    
    Args:
        handler: 处理函数，接收 webhook 数据并返回结果
                 函数签名: def handler(data: Dict[str, Any]) -> Dict[str, Any]
                 - 如果是同步函数，直接调用
                 - 如果是异步函数，会使用 asyncio.run 包装
        secret_env_key: webhook 密钥的环境变量名
        url_prefix: URL 前缀，默认为 "/api/webhook"
        blueprint_name: Blueprint 名称，默认为 "aigc_auth_webhook"
        
    Returns:
        Blueprint: Flask Blueprint 实例
        
    使用示例:
        from huace_aigc_auth_client.webhook_flask import create_flask_webhook_blueprint
        
        # 方式1：使用适配器的 handle_webhook 方法
        from your_app.adapters import YourAdapter
        
        sync_config = create_sync_config(...)
        auth_client = AigcAuthClient(...)
        adapter = YourAdapter(sync_config, auth_client)
        
        async def webhook_handler(data: dict) -> dict:
            event = data.get("event")
            event_data = data.get("data", {})
            return await adapter.handle_webhook(event, event_data)
        
        webhook_bp = create_flask_webhook_blueprint(
            handler=webhook_handler,
            url_prefix="/api/webhook"
        )
        
        # 方式2：自定义处理逻辑
        def custom_handler(data: dict) -> dict:
            event = data.get("event")
            if event == "user.created":
                # 自定义处理逻辑
                user_data = data.get("data", {})
                # ... 处理用户创建事件
                return {"status": "success", "created": True}
            return {"status": "ok"}
        
        webhook_bp = create_flask_webhook_blueprint(handler=custom_handler)
        
        # 注册到 Flask app
        app.register_blueprint(webhook_bp)
        
        # Webhook 端点: POST /api/webhook/auth
    """
    webhook_bp = Blueprint(blueprint_name, __name__, url_prefix=url_prefix)
    
    @webhook_bp.route('/auth', methods=['POST'])
    def receive_auth_webhook():
        """
        接收 aigc-auth 用户变更通知
        
        当 aigc-auth 中创建或更新用户时，会发送 webhook 通知到此端点。
        
        支持的事件:
        - user.created: 用户创建
        - user.updated: 用户更新
        - user.deleted: 用户删除
        - user.login: 用户登录
        - user.init_sync_auth: 初始化同步请求
        """
        # 获取请求体
        body = request.get_data()
        
        # 验证签名
        signature = request.headers.get("X-Webhook-Signature", "")
        secret = os.getenv(secret_env_key, "")
        
        if not verify_webhook_signature(body, signature, secret):
            logger.warning("Webhook 签名验证失败")
            return jsonify({"code": 401, "message": "Invalid signature"}), 401
        
        # 解析请求数据
        try:
            data = request.get_json()
        except Exception as e:
            logger.error(f"解析 webhook 数据失败: {e}")
            return jsonify({"code": 400, "message": "Invalid JSON payload"}), 400
        
        # 记录日志
        event = data.get("event", "unknown")
        logger.info(f"收到 webhook 事件: {event}")
        
        # 调用用户提供的处理函数
        try:
            import asyncio
            import inspect
            
            # 检查 handler 是否为协程函数
            if inspect.iscoroutinefunction(handler):
                result = asyncio.run(handler(data))
            else:
                result = handler(data)
            
            return jsonify({"code": 0, "message": "success", "data": result})
            
        except Exception as e:
            logger.exception(f"处理 webhook 失败: {e}")
            return jsonify({"code": 500, "message": str(e)}), 500
    
    return webhook_bp


def register_flask_webhook_routes(
    app,
    handler: Callable[[Dict[str, Any]], Dict[str, Any]],
    secret_env_key: str = "AIGC_AUTH_WEBHOOK_SECRET",
    url_prefix: str = "/api/webhook",
    blueprint_name: str = "aigc_auth_webhook"
):
    """
    注册 webhook 路由到 Flask 应用
    
    这是一个便捷函数，封装了创建 blueprint 和注册的过程。
    
    Args:
        app: Flask 应用实例
        handler: 处理函数，接收 webhook 数据并返回结果
        secret_env_key: webhook 密钥的环境变量名
        url_prefix: URL 前缀，默认为 "/api/webhook"
        blueprint_name: Blueprint 名称
        
    使用示例:
        from huace_aigc_auth_client.webhook_flask import register_flask_webhook_routes
        
        app = Flask(__name__)
        
        # 创建适配器
        adapter = YourAdapter(sync_config, auth_client)
        
        # 定义处理函数
        async def webhook_handler(data: dict) -> dict:
            event = data.get("event")
            event_data = data.get("data", {})
            return await adapter.handle_webhook(event, event_data)
        
        # 注册 webhook 路由
        register_flask_webhook_routes(
            app,
            handler=webhook_handler,
            url_prefix="/custom/webhook"  # 自定义前缀
        )
        
        # Webhook 端点: POST /custom/webhook/auth
    """
    webhook_bp = create_flask_webhook_blueprint(
        handler=handler,
        secret_env_key=secret_env_key,
        url_prefix=url_prefix,
        blueprint_name=blueprint_name
    )
    app.register_blueprint(webhook_bp)
    logger.info(f"Webhook 路由已注册: {url_prefix}/auth")


# 向后兼容的别名
create_webhook_blueprint = create_flask_webhook_blueprint
register_webhook_routes = register_flask_webhook_routes
