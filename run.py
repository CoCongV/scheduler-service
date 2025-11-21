"""FastAPI应用启动脚本"""
import uvicorn
from scheduler_service.main import create_app


if __name__ == "__main__":
    # 创建FastAPI应用
    app = create_app()

    # 启动应用
    uvicorn.run(
        "scheduler_service.main:create_app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        factory=True
    )