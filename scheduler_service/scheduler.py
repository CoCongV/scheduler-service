import asyncio
import time
from datetime import datetime
import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from scheduler_service.service import ping
from scheduler_service.models import Task, URLDetail


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, app=None):
        self.app = app
        self.scheduler_task = None
        self.is_running = False
    
    async def initialize(self):
        """初始化调度器"""
        if not self.app:
            raise ValueError("App not set")
        
    async def start(self):
        """启动调度器"""
        if self.is_running:
            return
        
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._schedule_tasks())
        self.app.loop.create_task(self._schedule_tasks())
        print("Task scheduler started")
    
    async def stop(self):
        """停止调度器"""
        self.is_running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        print("Task scheduler stopped")
    
    async def _schedule_tasks(self):
        """调度任务的主循环"""
        while self.is_running:
            try:
                await self._check_and_execute_tasks()
            except Exception as e:
                print(f"Error in scheduler: {e}")
            
            # 每秒检查一次任务
            await asyncio.sleep(1)
    
    async def _check_and_execute_tasks(self):
        """检查并执行需要运行的任务"""
        # 获取所有活跃的任务
        tasks = await Task.filter()
        
        for task in tasks:
            # 检查任务是否应该运行
            if task.interval and await self._should_run_task(task):
                # 使用dramatiq异步执行任务
                ping.send(str(task.id))
    
    async def _should_run_task(self, task: Task) -> bool:
        """判断任务是否应该运行"""
        # 这里可以实现更复杂的调度逻辑
        # 简单示例：基于interval检查是否应该运行
        now = time.time()
        start_time = task.start_time.timestamp()
        
        # 检查任务是否应该运行
        if task.interval and (now - start_time) % task.interval < 1:
            return True
        
        return False


# 创建全局调度器实例
scheduler = TaskScheduler()


def init_scheduler(app):
    """初始化调度器"""
    scheduler.app = app
    
    # 注册应用启动和关闭钩子
    app.register_listener(scheduler.initialize, 'before_server_start')
    app.register_listener(scheduler.start, 'after_server_start')
    app.register_listener(scheduler.stop, 'before_server_stop')
    
    return scheduler