import click
from IPython import embed
import os
import sys
sys.path.insert(0, ".")
env = os.getenv("schedulerEnv", "default")

from sanic.log import logger

from scheduler_service import create_app
try:
    import config
except ImportError:
    from scheduler_service.config import configs
    config = configs.get(env)

app = create_app(config)
from scheduler_service.models import User


@click.group()
def cli():
    click.echo("START SCHEDULER SERVICE CLI")


@cli.command()
def shell():
    context = {
        "app": app,
        "User": User
    }
    embed(user_ns=context,
          colors="neutral",
          using="asyncio",
          header="First: await app._database.connect()")


@cli.command()
@click.option('-h', "--host", default="localhost")
@click.option('-p', "--port", default=8080, type=int)
@click.option('-w', "--works", default=1, type=int)
@click.option('--debug/--no-debug', default=True)
@click.option('--access-log/--no-access-log', default=True)
def runserver(host, port, works, debug, access_log):
    app.run(debug=debug,
            host=host,
            port=port,
            workers=works,
            access_log=access_log)


@cli.command()
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose output.')
def worker(verbose):
    """启动dramatiq worker"""
    import logging
    import sys
    
    # 配置日志
    if verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
    
    # 导入需要的模块
    from scheduler_service import create_app
    from scheduler_service.service import ping, startup_worker, shutdown_worker
    
    # 确保应用已初始化
    app = create_app(config)
    
    # 运行dramatiq worker
    from dramatiq.cli import main
    
    # 设置命令行参数
    sys.argv = [sys.argv[0], 'scheduler_service.service', '--processes', '1']
    
    try:
        main()
    except KeyboardInterrupt:
        print("Worker stopped")


@cli.command()
def init_db():
    import sqlalchemy
    from scheduler_service.models import metadata
    engine = sqlalchemy.create_engine(str(pg_db.url))
    metadata.create_all(engine)