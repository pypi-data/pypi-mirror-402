from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from sqlmodel import Field, SQLModel, Session, select


class OpeningBreakoutBase(SQLModel):
    symbol: str = Field(min_length=1, max_length=64, index=True)
    open: Optional[float] = Field(default=None)
    high: Optional[float] = Field(default=None)
    low: Optional[float] = Field(default=None)
    breakout_price: Optional[float] = Field(default=None)
    volume: Optional[float] = Field(default=None)
    day_found: Optional[date] = Field(default=None, index=True)
    ts: Optional[int] = Field(default=None, description="epoch timestamp")


class OpeningBreakoutCreate(OpeningBreakoutBase):
    pass


class OpeningBreakoutRead(OpeningBreakoutBase):
    id: uuid.UUID


class OpeningBreakout(OpeningBreakoutBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


def add_opening_breakout(
    session: Session,
    symbol: str,
    open: Optional[float],
    high: Optional[float],
    low: Optional[float],
    breakout_price: Optional[float],
    volume: Optional[float],
    day_found: date,
    ts: Optional[int] = None,
) -> tuple[OpeningBreakout, bool]:
    """Insert a new opening-breakout row. Returns (obj, created).

    If the same symbol/day_found already exists, return existing without creating.
    """
    stmt = select(OpeningBreakout).where(
        OpeningBreakout.symbol == symbol, OpeningBreakout.day_found == day_found
    )
    existing = session.exec(stmt).first()

    if existing is None:
        obj = OpeningBreakout(
            symbol=symbol,
            open=open,
            high=high,
            low=low,
            breakout_price=breakout_price,
            volume=volume,
            day_found=day_found,
            ts=ts,
        )
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj, True

    return existing, False
