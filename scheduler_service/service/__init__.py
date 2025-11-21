import dramatiq
import httpx
from scheduler_service.constants import RequestStatus

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
    from scheduler_service.models import RequestTask, URLDetail
    session = get_session()
    
    try:
        # 从数据库获取任务信息
        task = await RequestTask.get_or_none(id=task_id)
        
        if task:
            # 通过task反查URLDetail
            url_details = await URLDetail.filter(request_task_id=task_id)
            
            for url_detail in url_details:
                try:
                    # 准备请求参数
                    request_kwargs = {
                        'url': task.request_url,
                        'headers': task.header if task.header else {}
                    }
                    
                    # 如果有payload，作为请求体
                    if url_detail.payload:
                        request_kwargs['json'] = url_detail.payload
                    
                    # 根据method执行相应的HTTP请求
                    method = task.method.upper()
                    match method:
                        case 'POST':
                            response = await session.post(**request_kwargs)
                        case 'PUT':
                            response = await session.put(**request_kwargs)
                        case 'DELETE':
                            response = await session.delete(**request_kwargs)
                        case 'PATCH':
                            response = await session.patch(**request_kwargs)
                        case _:
                            # 默认使用GET（包括当method为GET或其他未知方法时）
                            response = await session.get(**request_kwargs)
                    
                    # 读取响应内容
                    content = await response.aread()
                    
                    # 准备反馈数据
                    callback_data = {
                        'response': content.decode('utf-8'),
                        'code': response.status_code,
                        'exception': None,
                        'status': RequestStatus.COMPLETE
                    }
                    
                except Exception as e:
                    # 处理请求异常
                    print(f"Error requesting {task.request_url}: {e}")
                    callback_data = {
                        'response': None,
                        'code': None,
                        'exception': str(e),
                        'status': RequestStatus.FAIL
                    }
                
                # 如果有callback_url，发送反馈
                if task.callback_url:
                    try:
                        await session.post(
                            task.callback_url,
                            json=callback_data
                        )
                    except Exception as e:
                        print(f"Error sending callback to {task.callback_url}: {e}")
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