# -*- coding: utf-8 -*-
"""
Webhook 接收模块

提供通用的 webhook 接收功能，用于接收 aigc-auth 的用户变更通知
"""

import hmac
import hashlib
import os
import logging
from typing import Callable, Awaitable, Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException

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
    if not secret or not signature:
        return False  # 如果未配置密钥，则签名无效
    
    expected = hmac.new(
        secret.encode('utf-8'),
        payload,  # payload 已经是 bytes 类型
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)


def register_webhook_router(
    api_router: APIRouter,
    handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
    prefix: str = "/webhook",
    secret_env_key: str = "AIGC_AUTH_WEBHOOK_SECRET",
    tags: Optional[list] = None
) -> APIRouter:
    """
    注册 webhook 路由到现有的 API Router
    
    Args:
        api_router: FastAPI APIRouter 实例
        handler: 异步处理函数，接收 webhook 数据并返回结果
                 函数签名: async def handler(data: Dict[str, Any]) -> Dict[str, Any]
        prefix: webhook 路由前缀，默认 "/webhook"
        secret_env_key: webhook 密钥的环境变量名，默认 "AIGC_AUTH_WEBHOOK_SECRET"
        tags: OpenAPI 标签列表，默认 ["Webhook"]
        
    Returns:
        APIRouter: 创建的 webhook router
        
    使用示例:
        from fastapi import APIRouter
        from huace_aigc_auth_client.webhook import register_webhook_router
        
        api_router = APIRouter()
        
        async def my_webhook_handler(data: dict) -> dict:
            event = data.get("event")
            if event == "user.created":
                # 处理用户创建事件
                pass
            return {"status": "ok"}
        
        register_webhook_router(api_router, my_webhook_handler)
    """
    if tags is None:
        tags = ["Webhook"]
    
    webhook_router = APIRouter()
    
    @webhook_router.post("/auth")
    async def receive_auth_webhook(request: Request):
        """
        接收 aigc-auth 用户变更通知
        
        当 aigc-auth 中创建或更新用户时，会发送 webhook 通知到此端点，
        本系统接收后会调用自定义的处理函数进行处理。
        
        支持的事件:
        - user.created: 用户创建
        - user.updated: 用户更新
        """
        # 获取请求体
        body = await request.body()
        
        # 验证签名
        signature = request.headers.get("X-Webhook-Signature", "")
        secret = os.getenv(secret_env_key, "")
        
        if not verify_webhook_signature(body, signature, secret):
            logger.warning("Webhook signature verification failed")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # 解析请求数据
        try:
            data = await request.json()
        except Exception as e:
            logger.error(f"Failed to parse webhook payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # 记录日志
        event = data.get("event", "unknown")
        logger.info(f"Received webhook event: {event}")
        
        # 调用用户提供的处理函数
        try:
            result = await handler(data)
            return result
        except Exception as e:
            logger.exception(f"Failed to handle webhook: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # 将 webhook router 注册到主 router
    api_router.include_router(webhook_router, prefix=prefix, tags=tags)
    
    return webhook_router
