"""FastAPI主应用文件"""
import os
from typing import Any, AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise

from scheduler_service.config import configs
from scheduler_service.api import setup_routes
from scheduler_service.scheduler import init_scheduler
from scheduler_service import setup_dramatiq, close_dramatiq, setup_tortoise as setup_tortoise_db, close_tortoise


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    # 启动时执行
    await setup_dbs(app)
    setup_dramatiq(app.config)
    await init_scheduler(app)
    yield
    # 关闭时执行
    await close_dbs()


def create_app(config: Any = None) -> FastAPI:
    """创建FastAPI应用"""
    # 配置
    if config:
        app_config = config
    elif os.environ.get("schedulerEnv"):
        app_config = configs[os.environ.get("schedulerEnv")]
    else:
        app_config = configs["default"]

    # 使用新的lifespan事件处理器
    app = FastAPI(
        title="调度服务 API",
        description="任务调度服务的RESTful API",
        version="0.1.0",
        lifespan=lifespan  # 设置生命周期管理
    )
    
    # 存储配置到app实例
    app.config = app_config

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

    return app


async def setup_dbs(app: FastAPI):
    """初始化所有数据库连接"""

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


async def close_dbs():
    """关闭所有数据库连接"""
    # 关闭Tortoise连接
    await close_tortoise()
    # 关闭Dramatiq连接
    close_dramatiq()