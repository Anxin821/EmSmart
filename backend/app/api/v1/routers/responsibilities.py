from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user, check_module_access
from app.schemas import ApiResponse
from app.services import responsibilities_service as service

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


@router.get("")
def list_job_duties(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return ApiResponse(data=service.list_job_duties(db))


@router.post("")
def create_job_duty(body: DutyCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user), _=Depends(check_module_access("job_duties", write=True)) , request: Request = None):
    return ApiResponse(data=service.create_job_duty(db, body.model_dump(), request, current_user["username"]), message="创建成功")


@router.patch("/{duty_id}")
def patch_job_duty(duty_id: int, body: DutyUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user), _=Depends(check_module_access("job_duties", write=True)), request: Request = None):
    res = service.patch_job_duty(db, duty_id, body.model_dump(exclude_unset=True), request, current_user["username"])
    if not res:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return ApiResponse(data=res, message="修改成功")


@router.put("/{duty_id}")
def update_job_duty_items(duty_id: int, body: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user), _=Depends(check_module_access("job_duties", write=True)), request: Request = None):
    res = service.put_job_duty_items(db, duty_id, body, request, current_user["username"])
    if not res:
        raise HTTPException(status_code=404, detail="记录不存在")
    return ApiResponse(data=res)


@router.delete("/{duty_id}")
def delete_job_duty(duty_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user), _=Depends(check_module_access("job_duties", write=True)), request: Request = None):
    ok = service.delete_job_duty(db, duty_id, request, current_user["username"])
    if not ok:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return ApiResponse(data={"id": duty_id}, message="删除成功")
