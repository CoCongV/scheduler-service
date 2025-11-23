import pytest
import asyncio
from datetime import datetime
import time
import json

from scheduler_service.models import RequestTask, User
from tests import const


class TestTaskModel:
    """测试RequestTask模型"""
    
    async def test_create_task(self, user):
        """测试创建任务"""
        task = await RequestTask.create(
            name="test_task",
            start_time=datetime.now(),
            user_id=user.id,
            request_url="http://example.com",
            callback_url="http://example.com/callback",
            method="GET"
        )
        assert task.name == "test_task"
        assert task.user_id == user.id
        assert task.method == "GET"
        
        # 清理
        await task.delete()
    
    async def test_task_with_random_interval(self, user):
        """测试带有随机间隔的任务"""
        task = await RequestTask.create(
            name="random_task",
            start_time=datetime.now(),
            user_id=user.id,
            request_url="http://example.com",
            callback_url="http://example.com/callback",
            method="POST",
            body={"key": "value"}
        )
        assert task.method == "POST"
        assert task.body == {"key": "value"}
        
        # 清理
        await task.delete()
    
    async def test_task_method_validation(self, user):
        """测试HTTP方法验证"""
        # 测试有效方法
        for method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
            task = await RequestTask.create(
                name=f"test_{method.lower()}",
                start_time=datetime.now(),
                user_id=user.id,
                request_url="http://example.com",
                callback_url="http://example.com/callback",
                method=method
            )
            assert task.method == method.upper()
            await task.delete()
        
        # 测试无效方法
        with pytest.raises(ValueError, match="Invalid HTTP method"):
            await RequestTask.create(
                name="invalid_method",
                start_time=datetime.now(),
                user_id=user.id,
                request_url="http://example.com",
                method="INVALID"
            )
    
    async def test_task_to_dict(self, user):
        """测试任务转字典方法"""
        task = await RequestTask.create(
            name="dict_test",
            start_time=datetime.now(),
            user_id=user.id,
            request_url="http://example.com",
            callback_url="http://example.com/callback",
            method="POST",
            header={"Authorization": "Bearer token"},
            body={"data": "test"}
        )
        task_dict = task.to_dict()
        
        assert task_dict["name"] == "dict_test"
        assert task_dict["method"] == "POST"
        assert task_dict["header"] == {"Authorization": "Bearer token"}
        assert task_dict["body"] == {"data": "test"}
        
        # 清理
        await task.delete()


class TestTaskAPI:
    """测试任务API端点"""
    
    async def test_create_task_api(self, client, headers):
        """测试创建任务API"""
        task_data = {
            "name": "api_test_task",
            "start_time": time.time(),
            "request_url": "http://example.com",
            "callback_url": "http://example.com/callback",
            "method": "POST",
            "header": {"Content-Type": "application/json"},
            "body": {"key": "value"}
        }
        
        resp = await client.post(const.task_url, headers=headers, json=task_data)
        assert resp.status_code == 200
        response_data = resp.json()
        assert "task_id" in response_data
        
        # 清理
        task_id = response_data["task_id"]
        await client.delete(f"{const.task_url}/{task_id}", headers=headers)
    
    async def test_create_task_with_random_interval(self, client, headers):
        """测试创建带有随机间隔的任务"""
        task_data = {
            "name": "random_interval_task",
            "start_time": time.time(),
            "request_url": "http://example.com",
            "method": "GET"
        }
        
        resp = await client.post(const.task_url, headers=headers, json=task_data)
        assert resp.status_code == 200
        response_data = resp.json()
        assert "task_id" in response_data
        
        # 清理
        task_id = response_data["task_id"]
        await client.delete(f"{const.task_url}/{task_id}", headers=headers)
    
    async def test_get_tasks(self, client, headers, user):
        """测试获取任务列表"""
        # 先创建几个任务
        task1 = await RequestTask.create(
            name="task1",
            start_time=datetime.now(),
            user_id=user.id,
            request_url="http://example.com/1",
            callback_url="http://example.com/callback"
        )
        task2 = await RequestTask.create(
            name="task2",
            start_time=datetime.now(),
            user_id=user.id,
            request_url="http://example.com/2",
            callback_url="http://example.com/callback"
        )
        
        # 获取任务列表
        resp = await client.get(const.task_url, headers=headers)
        assert resp.status_code == 200
        response_data = resp.json()
        assert "tasks" in response_data
        assert len(response_data["tasks"]) >= 2
        
        # 清理
        await task1.delete()
        await task2.delete()
    
    async def test_get_task(self, client, headers, user):
        """测试获取单个任务"""
        # 创建任务
        task = await RequestTask.create(
            name="single_task",
            start_time=datetime.now(),
            user_id=user.id,
            request_url="http://example.com/single",
            callback_url="http://example.com/callback",
            method="POST",
            body={"test": "data"}
        )
        
        # 获取任务
        resp = await client.get(f"{const.task_url}/{task.id}", headers=headers)
        assert resp.status_code == 200
        response_data = resp.json()
        assert response_data["name"] == "single_task"
        assert response_data["method"] == "POST"
        assert response_data["body"] == {"test": "data"}
        
        # 清理
        await task.delete()
    
    async def test_get_nonexistent_task(self, client, headers):
        """测试获取不存在的任务"""
        resp = await client.get(f"{const.task_url}/99999", headers=headers)
        assert resp.status_code == 404
    
    async def test_delete_task(self, client, headers, user):
        """测试删除任务"""
        # 创建任务
        task = await RequestTask.create(
            name="delete_me",
            start_time=datetime.now(),
            user_id=user.id,
            request_url="http://example.com/delete",
            callback_url="http://example.com/callback"
        )
        task_id = task.id
        
        # 删除任务
        resp = await client.delete(f"{const.task_url}/{task_id}", headers=headers)
        assert resp.status_code == 200
        
        # 确认任务已删除
        resp = await client.get(f"{const.task_url}/{task_id}", headers=headers)
        assert resp.status_code == 404
    
    async def test_delete_nonexistent_task(self, client, headers):
        """测试删除不存在的任务"""
        resp = await client.delete(f"{const.task_url}/99999", headers=headers)
        assert resp.status_code == 404
    
    async def test_unauthorized_access(self, client):
        """测试未授权访问"""
        # 不带认证头访问
        resp = await client.get(const.task_url)
        assert resp.status_code == 401
        
        resp = await client.post(const.task_url, json={"name": "test", "start_time": time.time(), "request_url": "http://example.com"})
        assert resp.status_code == 401
        
        resp = await client.get(f"{const.task_url}/1")
        assert resp.status_code == 401
        
        resp = await client.delete(f"{const.task_url}/1")
        assert resp.status_code == 401
    
    async def test_invalid_task_data(self, client, headers):
        """测试无效的任务数据"""
        # 缺少必需字段
        resp = await client.post(const.task_url, headers=headers, json={})
        assert resp.status_code == 422
        
        # 无效的HTTP方法
        resp = await client.post(const.task_url, headers=headers, json={
            "name": "invalid_method",
            "start_time": time.time(),
            "request_url": "http://example.com",
            "method": "INVALID_METHOD"
        })
        assert resp.status_code == 422
    
    async def test_user_isolation(self, client, headers):
        """测试用户任务隔离"""
        # 创建第一个用户的任务
        resp = await client.post(const.task_url, headers=headers, json={
            "name": "user1_task",
            "start_time": time.time(),
            "request_url": "http://example.com/user1"
        })
        assert resp.status_code == 200
        task1_id = resp.json()["task_id"]
        
        # 创建第二个用户
        user2_data = {
            "name": "user2",
            "password": "password",
            "email": "user2@test.com"
        }
        resp = await client.post(const.user_url, json=user2_data)
        assert resp.status_code == 200
        
        # 获取第二个用户的token
        resp = await client.post(const.auth_token_url, json={
            "name": "user2",
            "password": "password"
        })
        assert resp.status_code == 200
        user2_headers = {"Authorization": f"Bearer {resp.json()['token']}"}
        
        # 尝试用第二个用户访问第一个用户的任务
        resp = await client.get(f"{const.task_url}/{task1_id}", headers=user2_headers)
        assert resp.status_code == 404
        
        # 清理
        await client.delete(f"{const.task_url}/{task1_id}", headers=headers)