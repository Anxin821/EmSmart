"""
岗位职责管理 API
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from core.auth import get_current_user, check_module_access
from schemas import ApiResponse
from models import JobResponsibility

router = APIRouter(prefix="/job-duties", tags=["岗位职责"])


class DutyItem(BaseModel):
    content: str
    is_primary: bool = False


class DutyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=50)
    items: Optional[List[DutyItem]] = None
    sort_order: Optional[int] = 0


class DutyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    title: Optional[str] = Field(None, min_length=1, max_length=50)
    items: Optional[List[DutyItem]] = None
    sort_order: Optional[int] = None


def _serialize(r: JobResponsibility):
    try:
        items = json.loads(r.items or "[]")
    except json.JSONDecodeError:
        items = []
    return {
        "id": r.id,
        "name": r.name,
        "title": r.title,
        "items": items,
        "sort_order": r.sort_order,
    }


@router.get("")
def list_job_duties(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取所有人员岗位职责"""
    rows = db.query(JobResponsibility).order_by(
        JobResponsibility.sort_order,
        JobResponsibility.id,
    ).all()
    return ApiResponse(data=[_serialize(r) for r in rows])


@router.post("")
def create_job_duty(
    body: DutyCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _=Depends(check_module_access("job_duties", write=True)),
):
    """新增岗位组（人员 + 职称 + 初始职责）"""
    items_json = "[]"
    if body.items:
        items_json = json.dumps(
            [{"content": i.content, "is_primary": i.is_primary} for i in body.items],
            ensure_ascii=False,
        )

    if body.sort_order is None:
        # 默认追加到末尾
        max_order = db.query(JobResponsibility.sort_order).order_by(
            JobResponsibility.sort_order.desc()
        ).first()
        sort_order = (max_order[0] or 0) + 1 if max_order else 1
    else:
        sort_order = body.sort_order

    row = JobResponsibility(
        name=body.name.strip(),
        title=body.title.strip(),
        items=items_json,
        sort_order=sort_order,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ApiResponse(data=_serialize(row), message="创建成功")


@router.patch("/{duty_id}")
def patch_job_duty(
    duty_id: int,
    body: DutyUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _=Depends(check_module_access("job_duties", write=True)),
):
    """修改岗位组基础信息（姓名 / 职称 / 排序 / 职责）"""
    row = db.query(JobResponsibility).filter(JobResponsibility.id == duty_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="岗位不存在")

    if body.name is not None:
        row.name = body.name.strip()
    if body.title is not None:
        row.title = body.title.strip()
    if body.sort_order is not None:
        row.sort_order = body.sort_order
    if body.items is not None:
        row.items = json.dumps(
            [{"content": i.content, "is_primary": i.is_primary} for i in body.items],
            ensure_ascii=False,
        )

    db.commit()
    db.refresh(row)
    return ApiResponse(data=_serialize(row), message="修改成功")


@router.put("/{duty_id}")
def update_job_duty_items(
    duty_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _=Depends(check_module_access("job_duties", write=True)),
):
    """兼容旧前端：仅更新职责条目列表 (PUT /job-duties/{id} 接收 dict)"""
    row = db.query(JobResponsibility).filter(JobResponsibility.id == duty_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="记录不存在")

    if "items" in body and body["items"] is not None:
        row.items = json.dumps(body["items"], ensure_ascii=False)
    if "title" in body and body["title"] is not None:
        row.title = body["title"]
    if "name" in body and body["name"] is not None:
        row.name = body["name"]

    db.commit()
    db.refresh(row)
    return ApiResponse(data=_serialize(row))


@router.delete("/{duty_id}")
def delete_job_duty(
    duty_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _=Depends(check_module_access("job_duties", write=True)),
):
    """删除整个岗位组"""
    row = db.query(JobResponsibility).filter(JobResponsibility.id == duty_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="岗位不存在")
    db.delete(row)
    db.commit()
    return ApiResponse(data={"id": duty_id}, message="删除成功")
