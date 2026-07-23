"""认证路由：注册、登录、获取当前用户信息"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.models.user import User
from app.modules.auth.schemas import RegisterRequest, LoginRequest, TokenResponse, UserInfo

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=dict)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否存在
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    # 创建用户
    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 直接返回Token
    token = create_access_token(data={"sub": user.username})
    return {
        "code": 200,
        "message": "注册成功",
        "data": {
            "access_token": token,
            "token_type": "bearer",
            "user": UserInfo.model_validate(user).model_dump(),
        },
    }


@router.post("/login", response_model=dict)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    token = create_access_token(data={"sub": user.username})
    return {
        "code": 200,
        "message": "登录成功",
        "data": {
            "access_token": token,
            "token_type": "bearer",
            "user": UserInfo.model_validate(user).model_dump(),
        },
    }


@router.get("/me", response_model=dict)
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return {
        "code": 200,
        "message": "ok",
        "data": UserInfo.model_validate(current_user).model_dump(),
    }
