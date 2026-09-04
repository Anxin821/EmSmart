"""
智能工厂工作任务管理平台 - 认证模块（JWT + 权限控制）
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt, ExpiredSignatureError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

security = HTTPBearer()

_MAX_BCRYPT_BYTES = 72


def _truncate_for_bcrypt(password: str) -> str:
    """将密码截断至 bcrypt 允许的 72 字节以内（按 UTF-8 字节安全截断）。"""
    encoded = password.encode("utf-8")
    if len(encoded) <= _MAX_BCRYPT_BYTES:
        return password
    return encoded[:_MAX_BCRYPT_BYTES].decode("utf-8", errors="ignore")


def hash_password(password: str) -> str:
    """对明文密码进行 bcrypt 哈希"""
    return pwd_context.hash(_truncate_for_bcrypt(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(_truncate_for_bcrypt(plain_password), hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT Access Token
    :param data: 要编码到 token 中的数据（需包含 sub、role 等）
    :param expires_delta: 过期时间增量
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """解码并验证 JWT Token，返回 payload；区分过期与无效。"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 已过期，请重新登录")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 无效")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    依赖项：从请求头 Bearer Token 中解析当前用户信息
    直接从 JWT payload 提取，不查数据库
    """
    payload = decode_access_token(credentials.credentials)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 中缺少用户标识")
    return {
        "username": username,
        "role": payload.get("role", "viewer"),
        "full_name": payload.get("full_name", ""),
    }


def require_role(*roles: str):
    """
    角色权限依赖工厂：仅允许指定角色访问
    用法: @router.get("/admin-only", dependencies=[Depends(require_role("admin"))])
    """

    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
        return current_user

    return role_checker


def check_module_access(module_key: str, write: bool = False):
    """
    模块权限检查依赖工厂：admin 全权限，其他角色查 user_permissions 表
    用法: @router.post("/weekly", dependencies=[Depends(check_module_access("weekly", write=True))])
    """

    def checker(
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
    ):
        if current_user["role"] == "admin":
            return current_user

        from app.models import User, UserPermission

        user = db.query(User).filter(User.username == current_user["username"]).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户不存在")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账户已停用")

        perm = db.query(UserPermission).filter(
            UserPermission.user_id == user.id,
            UserPermission.module_key == module_key,
        ).first()
        if not perm or not perm.can_read:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无此模块访问权限")
        if write and not perm.can_write:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无此模块写入权限")
        return current_user

    return checker


def write_operation_log(
    db: Session,
    username: str,
    action: str,
    target_type: str,
    target_id=None,
    detail: str = None,
    request: Request = None,
):
    """
    写入操作日志
    :param db: 数据库会话
    :param username: 操作用户
    :param action: 操作类型 (CREATE/UPDATE/DELETE/LOGIN)
    :param target_type: 操作对象类型
    :param target_id: 操作对象ID
    :param detail: 操作详情
    :param request: FastAPI Request 对象（获取IP）
    """
    from app.models import OperationLog

    client_ip = None
    if request:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        elif request.client:
            client_ip = request.client.host
    log = OperationLog(
        username=username,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id else None,
        detail=str(detail)[:1000] if detail else None,
        ip_address=client_ip,
    )
    db.add(log)
    db.commit()


# ============================================================
# 权限模块清单 —— 全系统唯一来源（key + 中文 label）
# 与前端 Users.vue 权限设置面板的 11 个业务模块完全一致：
# user_service 播种/查询、以及 /login、/me 的 permissions 均引用本清单。
# 看板按角色展示、不做逐用户授权，故不在清单内；
# job_duties 等写操作由路由以 check_module_access 按字面 key 强制，管理员可全权。
# ============================================================
PERMISSION_MODULES = [
    {"key": "devices", "label": "设备管理"},
    {"key": "weekly", "label": "生产周报"},
    {"key": "monthly", "label": "生产月报"},
    {"key": "servers", "label": "服务器管理"},
    {"key": "agingracks", "label": "老化架管理"},
    {"key": "wifi", "label": "WiFi AP 管理"},
    {"key": "orders", "label": "MES 工单管理"},
    {"key": "bugs", "label": "MES BUG 管理"},
    {"key": "devreqs", "label": "MES 需求管理"},
    {"key": "antivirus", "label": "设备杀毒记录"},
    {"key": "users", "label": "用户管理"},
]

_MODULE_KEYS = [m["key"] for m in PERMISSION_MODULES]


def build_permissions(db: Session, user) -> list[dict]:
    """
    统一构造用户权限列表（main 中 /login 与 /me 两处调用，消除重复代码）。

    规则：
    - admin 角色：PERMISSION_MODULES（11 个业务模块）全部 read + write
    - engineer / viewer 角色：查 user_permissions 表；不存在但为 engineer 时默认 read=True
    - 返回 list[dict]，dict 结构 = UserPermissionOut（{module_key, can_read, can_write}）
    """
    from app.models import UserPermission

    if not user:
        return []

    if user.role == "admin":
        return [
            {"module_key": key, "can_read": True, "can_write": True}
            for key in _MODULE_KEYS
        ]

    # 非 admin：查库；不存在则按角色补默认
    rows = db.query(UserPermission).filter(UserPermission.user_id == user.id).all()
    row_map: dict[str, UserPermission] = {r.module_key: r for r in rows}

    default_read = (user.role == "engineer")  # engineer 默认看得到，viewer 默认看不到
    result = []
    for key in _MODULE_KEYS:
        if key in row_map:
            r = row_map[key]
            result.append({"module_key": key, "can_read": bool(r.can_read), "can_write": bool(r.can_write)})
        else:
            result.append({"module_key": key, "can_read": default_read, "can_write": False})
    return result

