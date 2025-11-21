import dramatiq
import httpx

# 定义全局session
_session = None


def get_session():
    """获取httpx会话"""
    global _session
    if _session is None or _session.is_closed:
        _session = httpx.AsyncClient()
    return _session


async def close_session():
    """关闭httpx会话"""
    global _session
    if _session and not _session.is_closed:
        await _session.aclose()


@dramatiq.actor
async def ping(task_id):
    """执行ping任务"""
    from scheduler_service import mongo_db
    session = get_session()
    
    try:
        # 从MongoDB获取任务信息
        task = await mongo_db.task.find_one({'_id': task_id})
        
        if task and 'urls' in task:
            # 这里可以实现实际的请求逻辑
            for url_info in task.get('urls', []):
                url = url_info.get('request_url')
                if url:
                    try:
                        response = await session.get(url)
                        await response.aread()
                    except Exception as e:
                        print(f"Error pinging {url}: {e}")
    except Exception as e:
        print(f"Task {task_id} failed: {e}")


# 注册启动和关闭钩子
@dramatiq.actor
async def startup_worker():
    """worker启动时执行"""
    global _session
    _session = httpx.AsyncClient()


@dramatiq.actor
async def shutdown_worker():
    """worker关闭时执行"""
    await close_session()