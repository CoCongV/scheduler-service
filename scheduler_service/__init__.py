from motor import motor_asyncio
from arq import ArqRedis, create_pool
from arq.connections import RedisSettings
from sanic import Sanic
from tortoise import Tortoise, run_async

mongo_client: motor_asyncio.AsyncIOMotorClient = None
mongo_db: motor_asyncio.AsyncIOMotorDatabase = None
redis: ArqRedis = None


def create_app(config):
    app = Sanic(name=config.NAME)
    app.config.update_config(config)

    app.listeners['after_server_start'].extend(
        [setup_motor, setup_arq, setup_tortoise])

    app.listeners['before_server_stop'].extend(
        [close_motor, close_arq, close_tortoise])

    from .api.v1 import bpg
    app.blueprint(bpg)

    return app


async def setup_arq(app, loop):
    global redis
    settings = RedisSettings(
        host=app.config.get("REDIS_HOST", "localhost"),
        port=app.config.get("REDIS_PORT", 6379),
        database=app.config.get("REDIS_DATABASE", 0),
        password=app.config.get("REDIS_PASSWORD", None)
    )
    redis = await create_pool(settings)


async def close_arq(app, loop):
    global redis
    if redis:
        redis.close()
        await redis.wait_closed()


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


async def setup_motor(app, loop):
    global mongo_client, mongo_db
    mongo_client = motor_asyncio.AsyncIOMotorClient(
        "mongodb://localhost:27017", io_loop=loop)
    mongo_db = mongo_client['test']


async def close_motor(app, loop):
    global mongo_client
    mongo_client.close()


# def make_arq(config):
#     global redis
#     redis = create_pool(RedisSettings())
#     return redis