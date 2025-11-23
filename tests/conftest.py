import asyncio
import pytest
from httpx import AsyncClient
import os

import dramatiq
from dramatiq.brokers.stub import StubBroker # Use StubBroker which is an InMemoryBroker for dramatiq 1.x+

from scheduler_service.main import create_app, setup_dbs, close_dbs
from scheduler_service.models import User
from scheduler_service import setup_dramatiq, close_dramatiq


@pytest.fixture
async def client(app):
    """获取测试客户端"""
    # 注意：这里不使用上下文管理器触发lifespan，因为我们已经手动管理了数据库生命周期
    # 这样可以避免lifespan和手动初始化冲突
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def dramatiq_broker():
    """使用内存broker进行Dramatiq测试"""
    broker = StubBroker()
    dramatiq.set_broker(broker)
    yield broker
    broker.flush_all() # 清理所有队列
    dramatiq.set_broker(None) # 重置broker


@pytest.fixture
async def app(dramatiq_broker): # Inject the dramatiq_broker fixture
    """创建并启动测试应用"""
    # 使用测试数据库URL
    # 使用文件数据库以确保连接共享
    db_url = "sqlite://test.db"
    
    # 清理旧的测试数据库及相关文件
    if os.path.exists("test.db"):
        os.remove("test.db")
    if os.path.exists("test.db-shm"):
        os.remove("test.db-shm")
    if os.path.exists("test.db-wal"):
        os.remove("test.db-wal")
        
    test_config = {
        "POSTGRES_URL": db_url,
        "SECRET_KEY": "test-secret-key" # Add a test secret key
    }
    
    app = create_app(test_config)
    
    # 手动初始化数据库，确保在测试开始前数据库已就绪
    await setup_dbs(app)
    
    # Dramatiq setup with in-memory broker
    setup_dramatiq(app.config, dramatiq_broker) # Pass the in-memory broker here
    
    yield app
    
    # 关闭数据库连接
    await close_dbs()
    
    # 关闭Dramatiq连接
    close_dramatiq() # Ensure dramatiq is closed
        
    # 清理所有测试数据库文件
    if os.path.exists("test.db"):
        os.remove("test.db")
    if os.path.exists("test.db-shm"):
        os.remove("test.db-shm")
    if os.path.exists("test.db-wal"):
        os.remove("test.db-wal")


@pytest.fixture
async def user(app): # 依赖app确保DB已初始化
    """创建测试用户"""
    password_hash = User.hash_password("password")
    user = await User.create(
        name="test",
        password_hash=password_hash,
        email="test@test.com",
        verify=True
    )
    return user


@pytest.fixture
async def token(app, user: User):
    """获取测试用户的认证令牌"""
    return user.generate_auth_token(app.config["SECRET_KEY"])


@pytest.fixture
async def headers(token):
    """创建带有认证头的请求头"""
    return {"Authorization": f"Bearer {token}"}
