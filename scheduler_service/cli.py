import os
import sys
import logging
import tomllib  # Python 3.11+ 的 tomllib 模块用于读取 TOML

import click
from tortoise import run_async

from scheduler_service.main import create_app
from scheduler_service.config import configs
from scheduler_service.models import User
from scheduler_service import setup_tortoise, close_tortoise
from tortoise import Tortoise


@click.group()
def scheduler():
    """Scheduler Service 命令行工具"""
    click.echo("Scheduler Service CLI")


def get_config():
    """获取配置：首先尝试从运行目录下读取config.toml文件，若不存在则使用默认配置"""
    # 从运行目录获取config.toml文件路径
    config_path = os.path.join(os.getcwd(), "config.toml")
    
    # 如果config.toml文件存在，则读取它
    if os.path.exists(config_path):
        try:
            with open(config_path, "rb") as f:
                # 使用tomllib读取TOML文件
                config_data = tomllib.load(f)
                
                # 确保返回的是字典格式的配置
                return config_data
        except Exception as e:
            click.echo(f"读取config.toml时出错: {e}", err=True)
    
    # 如果文件不存在或读取失败，则回退到环境变量指定的默认配置
    env = os.getenv("schedulerEnv", "default")
    return configs.get(env)


@scheduler.command()
def shell():
    """启动交互式shell"""
    from IPython import embed
    config = get_config()
    app = create_app(config)
    context = {
        "app": app,
        "User": User
    }
    embed(user_ns=context,
          colors="neutral",
          using="asyncio",
          header="First: await app._database.connect()")


@scheduler.command()
@click.option('-h', "--host", default="localhost")
@click.option('-p', "--port", default=8080, type=int)
@click.option('-w', "--workers", default=1, type=int)
@click.option('--debug/--no-debug', default=True)
@click.option('--access-log/--no-access-log', default=True)
def runserver(host, port, workers, debug, access_log):
    """启动Web服务器（开发环境使用）"""
    import uvicorn
    import os

    # 确保配置正确
    config = get_config()
    
    # 将配置保存到环境变量，供create_app函数在热重载时读取
    if config:
        for key, value in config.items():
            os.environ[f"SCHEDULER_{key.upper()}"] = str(value)
    
    # 使用字符串导入路径，以支持热重载功能
    uvicorn.run(
        "scheduler_service.main:create_app",
        host=host,
        port=port,
        reload=debug,  # 开发模式下启用热重载
        access_log=access_log,
        factory=True  # 告知uvicorn这是一个应用工厂函数
    )


@scheduler.command()
@click.option('-v', '--verbose', is_flag=True, help='启用详细输出')
def worker(verbose):
    """启动dramatiq worker"""
    # 配置日志
    if verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    # 确保应用已初始化
    config = get_config()
    app = create_app(config)

    # 运行dramatiq worker
    from dramatiq.cli import main

    # 保存原始argv，避免修改全局状态
    original_argv = sys.argv.copy()
    try:
        sys.argv = [sys.argv[0], 'scheduler_service.service', '--processes', '1']
        main()
    except KeyboardInterrupt:
        print("Worker stopped")
    finally:
        sys.argv = original_argv


@scheduler.command()
def init_db():
    """初始化数据库"""
    config = get_config()

    async def init_tables():
        try:
            # 使用共享的数据库初始化函数
            await setup_tortoise(config)
            # 使用Tortoise ORM生成数据库模式
            await Tortoise.generate_schemas()
            click.echo("数据库初始化完成")
        except Exception as e:
            click.echo(f"数据库初始化失败: {e}")
        finally:
            await close_tortoise()

    # 运行异步函数
    run_async(init_tables())


if __name__ == '__main__':
    scheduler()