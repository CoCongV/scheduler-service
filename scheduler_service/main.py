"""FastAPI主应用文件"""
import os
import tomllib  # Python 3.11+ 的 tomllib 模块用于读取 TOML
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from tortoise import Tortoise
from tortoise.exceptions import DoesNotExist, IntegrityError

from scheduler_service import close_dramatiq, close_tortoise, setup_dramatiq
from scheduler_service.api import setup_routes
from scheduler_service.config import Config


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    # 启动时执行
    await setup_dbs(app)
    # Dramatiq will be set up by the app fixture in tests or via external config in production
    yield
    # 关闭时执行
    await close_dbs()


def get_config():
    """获取配置：首先尝试从运行目录下读取config.toml文件，若不存在则使用默认配置"""
    # 获取默认配置
    default_config = Config.to_dict()

    # 从运行目录获取config.toml文件路径
    config_path = os.path.join(os.getcwd(), "config.toml")

    # 如果config.toml文件存在，则读取它并更新默认配置
    if os.path.exists(config_path):
        try:
            with open(config_path, "rb") as f:
                # 使用tomllib读取TOML文件
                config_data = tomllib.load(f)

                # 更新默认配置
                default_config.update(config_data)
        except Exception as e:
            # 在实际应用中，这里应该使用logger记录错误
            print(f"读取config.toml时出错: {e}")

    return default_config


def create_app(config: Any = None) -> FastAPI:
    """创建FastAPI应用"""
    # 获取默认配置
    default_config = Config.to_dict()

    # 如果传入了配置，则用传入的配置更新默认配置
    if config:
        # 如果传入的是类，获取其字典形式
        if hasattr(config, 'to_dict'):
            config_dict = config.to_dict()
        elif isinstance(config, dict):
            config_dict = config
        else:
            # 尝试将其转换为字典
            config_dict = dict(config.__dict__)

        # 更新默认配置
        default_config.update(config_dict)
    else:
        # 如果没有传入配置，则自动获取配置并更新默认配置
        auto_config = get_config()
        default_config.update(auto_config)

    # 使用新的lifespan事件处理器
    app = FastAPI(
        title="调度服务 API",
        description="任务调度服务的RESTful API",
        version="0.1.0",
        lifespan=lifespan  # 设置生命周期管理
    )

    # 存储配置到app实例
    app.config = default_config

    # 注册路由
    setup_routes(app)

    # 注册异常处理器
    @app.exception_handler(DoesNotExist)
    async def does_not_exist_exception_handler(request: Request, exc: DoesNotExist):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_exception_handler(request: Request, exc: IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": [{"loc": [], "msg": str(exc), "type": "IntegrityError"}]},
        )

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

    # PostgreSQL - Tortoise ORM (使用官方实现)
    await Tortoise.init(
        db_url=db_url,
        modules={"models": ["scheduler_service.models"]},
    )
    # 生成数据库架构（仅开发环境建议）
    await Tortoise.generate_schemas()

    # 初始化 Dramatiq
    setup_dramatiq(app.config)


async def close_dbs():
    """关闭所有数据库连接"""
    # 关闭Tortoise连接
    await close_tortoise()
    # 关闭Dramatiq连接
    close_dramatiq()
