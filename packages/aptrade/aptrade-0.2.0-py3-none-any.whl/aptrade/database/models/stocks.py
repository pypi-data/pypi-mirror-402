import datetime
from sqlmodel import Field, SQLModel


class StockInPlay(SQLModel, table=True):
    __tablename__ = "stocks_in_play"
    id: int = Field(default=None, primary_key=True)
    ticker: str = Field(nullable=False, unique=True)
    percent_change: float = Field(nullable=False)
    detected_at: datetime.datetime = Field(default=datetime.datetime.utcnow)
