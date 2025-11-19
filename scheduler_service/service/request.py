from aiohttp import ClientSession
from bson import ObjectId

from scheduler_service import mongo_db


async def ping(ctx, oid):
    session: ClientSession = ctx['session']
    # 使用find_one获取单个文档，而不是find获取游标
    task = await mongo_db.task.find_one({'_id': ObjectId(oid)})
    if task and 'urls' in task:
        for url in task['urls']:
            async with session.get(url.get('request_url'), params=url.get('params')) as resp:
                await resp.text()