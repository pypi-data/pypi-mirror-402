from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import List

from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlmodel import select

from aptrade.api.deps import get_db
from aptrade.database.models.stocks import StockInPlay

router = APIRouter(prefix="/stocks-in-play", tags=["stocks-in-play"])


class StockInPlayBase(BaseModel):
    ticker: str
    percent_change: float


class StockInPlayCreate(StockInPlayBase):
    pass


class StockInPlayRead(StockInPlayBase):
    id: int
    detected_at: datetime

    class Config:
        orm_mode = True


@router.post("/", response_model=StockInPlayRead)
def create_stock_in_play(stock: StockInPlayCreate, db: Session = Depends(get_db)):
    db_stock = StockInPlay(**stock.model_dump())
    db.add(db_stock)
    db.commit()
    db.refresh(db_stock)
    return db_stock


@router.get("/", response_model=List[StockInPlayRead])
def list_stocks_in_play(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    statement = select(StockInPlay).offset(skip).limit(limit)
    return list(db.execute(statement).scalars())


@router.get("/{stock_id}", response_model=StockInPlayRead)
def get_stock_in_play(stock_id: int, db: Session = Depends(get_db)):
    stock = db.get(StockInPlay, stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock


@router.put("/{stock_id}", response_model=StockInPlayRead)
def update_stock_in_play(
    stock_id: int, stock: StockInPlayCreate, db: Session = Depends(get_db)
):
    db_stock = db.get(StockInPlay, stock_id)
    if not db_stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    for key, value in stock.model_dump().items():
        setattr(db_stock, key, value)
    db.commit()
    db.refresh(db_stock)
    return db_stock


@router.delete("/{stock_id}")
def delete_stock_in_play(stock_id: int, db: Session = Depends(get_db)):
    db_stock = db.get(StockInPlay, stock_id)
    if not db_stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    db.delete(db_stock)
    db.commit()
    return {"ok": True}
