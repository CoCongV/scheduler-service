from motor import motor_asyncio
import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from sanic import Sanic
from tortoise import Tortoise, run_async
from .scheduler import init_scheduler

mongo_client: motor_asyncio.AsyncIOMotorClient = None
rabbitmq_broker = None


def create_app(config):
    app = Sanic(name=config.NAME)
    app.config.update_config(config)

    app.listeners['after_server_start'].extend(
        [setup_dramatiq, setup_tortoise])

    app.listeners['before_server_stop'].extend(
        [close_dramatiq, close_tortoise])

    from .api.v1 import bpg
    app.blueprint(bpg)
    
    # 初始化任务调度器
    init_scheduler(app)

    return app


def setup_dramatiq(app, loop):
    global rabbitmq_broker
    rabbitmq_broker = RabbitmqBroker(
        url=f"amqp://{app.config.get('RABBITMQ_USER', 'guest')}:{app.config.get('RABBITMQ_PASSWORD', 'guest')}@{app.config.get('RABBITMQ_HOST', 'localhost')}:{app.config.get('RABBITMQ_PORT', 5672)}/{app.config.get('RABBITMQ_VHOST', '%2F')}"
    )
    # 设置为默认broker
    dramatiq.set_broker(rabbitmq_broker)


def close_dramatiq(app, loop):
    global rabbitmq_broker
    if rabbitmq_broker:
        rabbitmq_broker.close()


async def setup_tortoise(app, loop):
    # 设置Tortoise-ORM
    await Tortoise.init(
        db_url=app.config['PG_URL'],
        modules={'models': ['scheduler_service.models']}
    )
    # 自动创建表（仅开发环境使用，生产环境应使用迁移）
    await Tortoise.generate_schemas()


async def close_tortoise(app, loop):
    await Tortoise.close_connections()