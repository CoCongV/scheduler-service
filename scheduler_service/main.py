"""FastAPI主应用文件"""
import os
from typing import Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
from motor.motor_asyncio import AsyncIOMotorClient

from scheduler_service.config import configs
from scheduler_service.api import setup_routes
from scheduler_service.scheduler import init_scheduler
from scheduler_service import setup_dramatiq, close_dramatiq, setup_tortoise as setup_tortoise_db, close_tortoise

# 全局变量
mongo_db = None


def create_app(config: Any = None) -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title="调度服务 API",
        description="任务调度服务的RESTful API",
        version="0.1.0"
    )

    # 配置
    if config:
        app.config = config
    elif os.environ.get("schedulerEnv"):
        app.config = configs[os.environ.get("schedulerEnv")]
    else:
        app.config = configs["default"]

    # 注册路由
    setup_routes(app)

    # 跨域配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应该设置具体的域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 数据库配置
    @app.on_event("startup")
    async def startup_event():
        """应用启动时初始化"""
        # 使用共享的初始化函数
        await setup_dbs(app)
        # 设置Dramatiq消息队列
        setup_dramatiq(app.config)
        # 初始化调度器
        await init_scheduler(app)

    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭时清理"""
        # 使用共享的关闭函数
        await close_dbs()

    return app


async def setup_dbs(app: FastAPI):
    """初始化所有数据库连接"""
    global mongo_db
    
    # 获取数据库URL，支持多种配置键名
    db_url = app.config.get('POSTGRES_URL') or app.config.get('PG_URL') or app.config.get('DB_URL')
    if not db_url:
        raise ValueError("PostgreSQL数据库URL未配置，请设置POSTGRES_URL、PG_URL或DB_URL")
    
    # PostgreSQL - Tortoise ORM
    register_tortoise(
        app=app,
        db_url=db_url,
        modules={"models": ["scheduler_service.models"]},
        generate_schemas=True,  # 开发环境使用，生产环境应使用迁移
        add_exception_handlers=True
    )
    
    # MongoDB配置
    if hasattr(app.config, 'MONGO_URL') and app.config.MONGO_URL:
        mongo_client = AsyncIOMotorClient(app.config.MONGO_URL)
        mongo_db = mongo_client[app.config.get('MONGO_DATABASE', 'scheduler')]


async def close_dbs():
    """关闭所有数据库连接"""
    # 关闭Tortoise连接
    await close_tortoise()
    # 关闭Dramatiq连接
    close_dramatiq()