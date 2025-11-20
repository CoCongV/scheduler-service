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
        await setup_db(app)
        await init_scheduler(app)

    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭时清理"""
        await close_db(app)

    return app


async def setup_db(app: FastAPI):
    """初始化数据库"""
    global mongo_db
    
    # PostgreSQL - Tortoise ORM
    register_tortoise(
        app=app,
        db_url=app.config.POSTGRES_URL,
        modules={"models": ["scheduler_service.models"]},
        generate_schemas=True,
        add_exception_handlers=True
    )
    
    # MongoDB
    mongo_client = AsyncIOMotorClient(app.config.MONGO_URL)
    mongo_db = mongo_client[app.config.MONGO_DATABASE]


async def close_db(app: FastAPI):
    """关闭数据库连接"""
    pass