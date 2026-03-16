"""Keywords API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Keyword

router = APIRouter(prefix="/keywords", tags=["keywords"])


class KeywordCreate(BaseModel):
    keyword: str = Field(min_length=2, max_length=150)
    category: str = Field(min_length=2, max_length=100)
    weight: float = Field(default=1.0, ge=0.1, le=10.0)


@router.get("")
def list_keywords(db: Session = Depends(get_db)):
    rows = db.execute(select(Keyword)).scalars().all()
    return rows


@router.post("")
def create_keyword(payload: KeywordCreate, db: Session = Depends(get_db)):
    exists = db.execute(select(Keyword).where(Keyword.keyword == payload.keyword)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="keyword already exists")
    row = Keyword(keyword=payload.keyword, category=payload.category, weight=payload.weight, status="active")
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{keyword_id}")
def disable_keyword(keyword_id: int, db: Session = Depends(get_db)):
    row = db.get(Keyword, keyword_id)
    if not row:
        raise HTTPException(status_code=404, detail="keyword not found")
    row.status = "disabled"
    db.commit()
    return {"status": "disabled", "id": keyword_id}
