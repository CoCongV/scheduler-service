import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from tortoise import Tortoise
from .scheduler import init_scheduler

# 全局变量
rabbitmq_broker = None

# 移除Sanic相关的create_app函数


def setup_dramatiq(config):
    """初始化Dramatiq消息队列"""
    global rabbitmq_broker
    rabbitmq_broker = RabbitmqBroker(
        url=f"amqp://{config.get('RABBITMQ_USER', 'guest')}:{config.get('RABBITMQ_PASSWORD', 'guest')}@{config.get('RABBITMQ_HOST', 'localhost')}:{config.get('RABBITMQ_PORT', 5672)}/{config.get('RABBITMQ_VHOST', '%2F')}"
    )
    # 设置为默认broker
    dramatiq.set_broker(rabbitmq_broker)


def close_dramatiq():
    """关闭Dramatiq连接"""
    global rabbitmq_broker
    if rabbitmq_broker:
        rabbitmq_broker.close()


async def setup_tortoise(config):
    """初始化Tortoise-ORM"""
    # 获取数据库URL，支持多种配置键名
    db_url = config.get('PG_URL') or config.get('POSTGRES_URL') or config.get('DB_URL')
    if not db_url:
        raise ValueError("数据库URL未配置，请设置PG_URL、POSTGRES_URL或DB_URL环境变量")

    # 设置Tortoise-ORM
    await Tortoise.init(
        db_url=db_url,
        modules={'models': ['scheduler_service.models']}
    )


async def close_tortoise():
    """关闭Tortoise连接，不依赖Sanic应用"""
    await Tortoise.close_connections()
