"""用户API路由"""
from fastapi import APIRouter

# 导入并注册路由处理函数
from .main import get_current_user_info, create_user, update_user, delete_user
from .token import get_token
# 创建路由器

router = APIRouter()

# 注册路由
router.post("", status_code=201)(create_user)
router.get("", response_model=dict)(get_current_user_info)
router.patch("", response_model=dict)(update_user)
router.delete("")(delete_user)
router.get("/auth/token", response_model=dict)(get_token)
