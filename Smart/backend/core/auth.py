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
from core.database import get_db
from core.config import settings

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

        from models import User, UserPermission

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
    from models import OperationLog

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


# 13 个模块权限清单（和前端 menus 完全对齐）：数据看板 5 + 业务管理 8
_MODULE_PERMISSIONS = [
    # ── 数据看板（5 个，read 可见即可）──
    ("aoi_dashboard", "AOI&AI 看板"),
    ("network_dashboard", "车间网络看板"),
    ("mes_dashboard", "MES 看板"),
    ("antivirus_dashboard", "杀毒看板"),
    ("duties_dashboard", "岗位职责看板"),
    # ── 业务管理（8 个，write = 增删改）──
    ("devices", "AOI&AI 设备管理"),
    ("weekly", "生产周报管理"),
    ("monthly", "生产月报管理"),
    ("servers", "服务器管理"),
    ("aging_racks", "老化架管理"),
    ("wifi", "WiFi AP 管理"),
    ("mes", "MES 工单/BUG/需求管理"),
    ("antivirus", "设备杀毒记录"),
    ("users", "用户管理"),
    ("job_duties", "岗位职责管理"),
]

_MODULE_KEYS = [key for key, _ in _MODULE_PERMISSIONS]


def build_permissions(db: Session, user) -> list[dict]:
    """
    统一构造用户权限列表（main 中 /login 与 /me 两处调用，消除重复代码）。

    规则：
    - admin 角色：所有 13 模块都有 read + write
    - engineer / viewer 角色：查 user_permissions 表；不存在但为 engineer 时默认 read=True
    - 返回 list[dict]，dict 结构 = UserPermissionOut（{module_key, can_read, can_write}）
    """
    from models import UserPermission

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

