import uuid
from datetime import date
from typing import Optional

from sqlmodel import Field, SQLModel, Session, select


# Shared properties for the Gapper table
class GapperBase(SQLModel):
    symbol: str = Field(min_length=1, max_length=64, index=True)
    open: Optional[float] = Field(default=None)
    high: Optional[float] = Field(default=None)
    low: Optional[float] = Field(default=None)
    close: Optional[float] = Field(default=None)
    volume: Optional[float] = Field(default=None)
    previous_close: Optional[float] = Field(default=None)
    percent_change: Optional[float] = Field(default=None, index=True)
    day_found: Optional[date] = Field(default=None, index=True)
    ts: Optional[int] = Field(default=None, description="epoch timestamp")


class GapperCreate(GapperBase):
    pass


class GapperRead(GapperBase):
    id: uuid.UUID


class Gapper(GapperBase, table=True):
    """Database table for daily gap detections.

    Unique constraint expectation: (symbol, day_found) should be unique in practice.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


def add_or_update_gapper(
    session: Session,
    symbol: str,
    percent_change: float,
    day_found: date,
    open: Optional[float] = None,
    high: Optional[float] = None,
    low: Optional[float] = None,
    close: Optional[float] = None,
    volume: Optional[float] = None,
    previous_close: Optional[float] = None,
    ts: Optional[int] = None,
) -> tuple[Gapper, bool, bool]:
    """Insert a new gapper row or update existing one only if the new percent_change is higher.

    Returns (gapper_obj, changed) where changed=True when an insert or update happened.
    """
    stmt = select(Gapper).where(Gapper.symbol == symbol, Gapper.day_found == day_found)
    existing = session.exec(stmt).first()

    if existing is None:
        g = Gapper(
            symbol=symbol,
            open=open,
            high=high,
            low=low,
            close=close,
            volume=volume,
            previous_close=previous_close,
            percent_change=percent_change,
            day_found=day_found,
            ts=ts,
        )
        session.add(g)
        session.commit()
        session.refresh(g)
        return g, True, True

    # existing row found: update only if new gap is larger
    existing_pct = existing.percent_change or 0.0
    if percent_change > existing_pct:
        existing.open = open or existing.open
        existing.high = high or existing.high
        existing.low = low or existing.low
        existing.close = close or existing.close
        existing.volume = volume or existing.volume
        existing.previous_close = previous_close or existing.previous_close
        existing.percent_change = percent_change
        existing.ts = ts or existing.ts
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing, True, False

    return existing, False, False
