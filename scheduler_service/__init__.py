import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from tortoise import Tortoise

# 移除Sanic相关的create_app函数


def setup_dramatiq(config):
    """初始化Dramatiq消息队列"""
    rabbitmq_broker = RabbitmqBroker(
        url=f"amqp://{config.get('RABBITMQ_USER')}:{config.get('RABBITMQ_PASSWORD')}@{config.get('RABBITMQ_HOST')}:{config.get('RABBITMQ_PORT')}/{config.get('RABBITMQ_VHOST')}"
    )
    # 设置为默认broker
    dramatiq.set_broker(rabbitmq_broker)


def close_dramatiq():
    """关闭Dramatiq连接"""
    # 使用dramatiq.get_broker()获取当前broker，不需要全局变量
    current_broker = dramatiq.get_broker()
    if current_broker:
        current_broker.close()


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