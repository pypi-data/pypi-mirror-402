import pandas as pd
from backtesting import Strategy
import datetime as dt
from pydantic import BaseModel, Field
from typing import List, Any, Optional
import os


class CustomData(BaseModel):
    date: dt.date = Field(..., description="Date of the data point")


class BreakoutStrategy(Strategy):
    """Optimized Breakout Strategy with cooldown, type safety, and robust logic."""

    cooldown_minutes: int = 5
    open_range_minutes: int = 10
    premarket_end: dt.time = dt.time(9, 30)
    exit_minute_bar: dt.time = dt.time(15, 59)
    risk_percent: float = 0.01
    stop_loss_pct: float = 0.30
    profit_target_pct: float = 0.30
    pull_back_threshold: float = 0.20
    high_move_threshold: float = 1.00
    reclaim_pct: float = 0.90
    to_print: bool = False
    info: List[Any] = Field(
        default_factory=list, description="List to store results for each day"
    )
    symbol: str = ""
    get_last_day_price: bool = True
    run_number: int = 1

    def init(self) -> None:
        """Initialize/reset all state variables."""
        self.current_day: Optional[dt.date] = None
        self.prev_close: Optional[float] = None
        self.premarket_high: Optional[float] = None
        self.premarket_high_time: Optional[dt.datetime] = None
        self.premarket_qualified: bool = False
        self.pullback_detected: bool = False
        self.pullback_detected_time: Optional[dt.datetime] = None
        self.pullback_low: Optional[float] = None
        self.reclaim_detected: bool = False
        self.reclaim_detected_time: Optional[dt.datetime] = None
        self.entry_price: Optional[float] = None
        self.traded_today: bool = False
        self.info: List[Any] = []
        self.theoretical_entry_price: Optional[float] = None
        self.time_at_entry: Optional[dt.datetime] = None
        self.full_pullback: Optional[float] = None
        self.full_pullback_date: Optional[dt.datetime] = None
        self.stop_loss: Optional[float] = None
        self.real_stop_loss: Optional[float] = None
        self.real_stop_loss_time: Optional[dt.datetime] = None
        self.max_day_high: Optional[float] = None
        self.max_day_high_time: Optional[dt.datetime] = None
        self.low_day: Optional[float] = None
        self.low_day_time: Optional[dt.datetime] = None
        self.eod: Optional[float] = None

    def _reset_day(self, day: dt.date, prev_close: Optional[float]) -> None:
        """Reset state for a new trading day."""
        self.current_day = day
        self.prev_close = prev_close
        self.premarket_high = None
        self.premarket_high_time = None
        self.premarket_qualified = False
        self.pullback_detected = False
        self.pullback_detected_time = None
        self.full_pullback = None
        self.full_pullback_date = None
        self.pullback_low = None
        self.reclaim_detected = False
        self.reclaim_detected_time = None
        self.theoretical_entry_price = None
        self.entry_price = None
        self.traded_today = False
        self.time_at_entry = None
        self.stop_loss = None
        self.max_day_high = None
        self.max_day_high_time = None
        self.low_day = None
        self.low_day_time = None
        self.real_stop_loss = None
        self.real_stop_loss_time = None
        self.eod = None

    def next(self) -> None:
        """Main strategy logic executed on each bar."""
        t = self.data.index[-1]
        current_bar_date = t.date()
        current_time = t.time()
        # Wick validation: only run breakout logic if High > 1.15 * Close
        # if self.data.High[-1] >= 1.15 * self.data.Close[-1]:
        #     self.data.High[-1] = 1.15 * self.data.Close[-1]
        #     # return  # Skip this bar, wait for the next one

        # Detect new day and get previous close
        if self.current_day != current_bar_date:
            if self.get_last_day_price:
                prev_day_mask = self.data.index.date < current_bar_date
                self.prev_close = (
                    self.data.Close[prev_day_mask][-1] if prev_day_mask.any() else None
                )
            else:
                mask = (self.data.index.date < current_bar_date) & (
                    self.data.index.time <= self.exit_minute_bar
                )
                self.prev_close = self.data.Close[mask][-1] if mask.any() else None
            self._reset_day(current_bar_date, self.prev_close)
            self.prev_close = round(self.prev_close, 2) if self.prev_close else None

        # 1. Track pre-market high and check for >100% move
        if (
            current_time < self.premarket_end
            and self.prev_close
            and not self.pullback_detected
        ):
            if self.premarket_high is None or self.data.High[-1] > self.premarket_high:
                self.premarket_high = self.data.High[-1]
                self.premarket_high_time = t
            if self.premarket_high and self.prev_close:
                move = (self.premarket_high - self.prev_close) / self.prev_close
                if move >= self.high_move_threshold:
                    self.premarket_qualified = True
                    self.entry_price = self.premarket_high * self.reclaim_pct
                    self.theoretical_entry_price = (
                        self.premarket_high * self.reclaim_pct
                    )

        # 2. After 100% move, look for 20% pullback from high
        if self.premarket_qualified and not self.pullback_detected:
            if self.premarket_high_time and t > self.premarket_high_time:
                pullback = (
                    self.premarket_high - self.data.Low[-1]
                ) / self.premarket_high
                if pullback >= self.pull_back_threshold:
                    self.pullback_detected = True
                    self.pullback_low = self.data.Low[-1]
                    self.pullback_detected_time = t
                    self.full_pullback = self.data.Low[-1]
                    self.full_pullback_date = t
                    # return

        # 3. Wait for reclaim to 90% of high (entry trigger)
        if self.pullback_detected and not self.reclaim_detected and self.premarket_high:
            reclaim_price = self.premarket_high * self.reclaim_pct
            if self.data.High[-1] >= reclaim_price:
                self.reclaim_detected = True
                self.reclaim_detected_time = t
                self.entry_price = reclaim_price

            if self.data.Low[-1] < (
                self.full_pullback
                if self.full_pullback is not None
                else self.data.Low[-1]
            ):
                self.full_pullback = self.data.Low[-1]
                self.full_pullback_date = t

        # 4. Enter short if not already in position and not traded today, after cooldown
        cooldown_delta = dt.timedelta(minutes=self.cooldown_minutes)
        if (
            self.reclaim_detected
            and not self.position
            and not self.traded_today
            and self.reclaim_detected_time
            and t > self.reclaim_detected_time + cooldown_delta
        ):
            stop_loss = (
                self.entry_price * (1 + self.stop_loss_pct)
                if self.entry_price
                else None
            )
            self.stop_loss = stop_loss
            take_profit = (
                self.entry_price * (1 - self.profit_target_pct)
                if self.entry_price
                else None
            )
            per_share_risk = (
                abs(self.entry_price - stop_loss)
                if self.entry_price and stop_loss
                else 1
            )
            position_size = (
                int((self.risk_percent * self.equity) / per_share_risk)
                if per_share_risk
                else 0
            )
            self.time_at_entry = t
            if position_size > 0:
                self.sell(size=position_size)
                self.traded_today = True
                self.low_day = self.data.Low[-1]
                self.low_day_time = t
                self.max_day_high = self.data.High[-1]
                self.max_day_high_time = t

        # 5. Track highs/lows after entry
        if self.traded_today:
            if self.data.High[-1] >= (
                self.max_day_high
                if self.max_day_high is not None
                else self.data.High[-1]
            ):
                self.max_day_high = self.data.High[-1]
                self.max_day_high_time = t
            if self.data.Low[-1] <= (
                self.low_day if self.low_day is not None else self.data.Low[-1]
            ):
                self.low_day = self.data.Low[-1]
                self.low_day_time = t

        # 6. Close at end of day or on stop loss
        if self.position:
            if current_time >= self.exit_minute_bar:
                self.eod = self.data.Close[-1]
                self.position.close()
                self.write_results()
            if self.stop_loss and self.data.Close[-1] >= self.stop_loss:
                self.real_stop_loss = self.data.Close[-1]
                self.real_stop_loss_time = t

        # 7. Optional debug printing
        if self.prev_close and self.to_print:
            print("\n\n")
            print(
                f"{current_time} | C: {self.data.Close[-1]} | Peak: {self.premarket_high}"
            )
            print(
                f"Open: {self.data.Open[-1]} | High: {self.data.High[-1]} | Low: {self.data.Low[-1]} | Close: {self.data.Close[-1]}"
            )
            stop_loss = (
                self.entry_price * (1 + self.stop_loss_pct)
                if self.entry_price
                else None
            )
            take_profit = (
                self.entry_price * (1 - self.profit_target_pct)
                if self.entry_price
                else None
            )
            if self.premarket_qualified:
                print(
                    f"1. Premarket qualified: {self.premarket_qualified} with high {self.premarket_high:.2f}"
                )
                print(
                    f"Entry price: {self.entry_price} | Stop loss: {stop_loss} | Take profit: {take_profit} "
                )
            if self.pullback_detected:
                pullback_pct = (
                    100
                    * (self.premarket_high - self.pullback_low)
                    / self.premarket_high
                    if self.premarket_high
                    else 0
                )
                print(
                    f"2. Pullback detected: {pullback_pct:.2f} | from high {self.premarket_high} to low {self.pullback_low}"
                )
            if self.reclaim_detected:
                print(f"3. Reclaim detected: entry price {self.entry_price:.2f}")
            if self.position:
                print(
                    f"4. Position: {self.position.size} shares at entry price {self.entry_price:.2f}"
                )
            if self.traded_today:
                print("5. Traded today, no new trades allowed")

    def write_results(self) -> None:
        """Write results to CSV and update info list."""
        result = {
            "date": self.current_day,
            "symbol": self.symbol,
            "previous_close": round(self.prev_close, 2) if self.prev_close else None,
            "premarket_high": round(self.premarket_high, 2)
            if self.premarket_high
            else None,
            "premarket_high_time": self.premarket_high_time.strftime("%H:%M")
            if self.premarket_high_time
            else None,
            "theoretical_pullback": self.premarket_high * (1 - self.pull_back_threshold)
            if self.premarket_high
            else None,
            "max_pullback": round(self.full_pullback, 2)
            if self.full_pullback
            else None,
            "max_pullback_date": self.full_pullback_date.strftime("%H:%M")
            if self.full_pullback_date
            else None,
            "th_entry_price": round(self.theoretical_entry_price, 2)
            if self.theoretical_entry_price
            else None,
            "real_entry_price": round(self.entry_price, 2)
            if self.entry_price
            else None,
            "time_at_entry": self.time_at_entry.strftime("%H:%M")
            if self.time_at_entry
            else None,
            "trigger_time": self.reclaim_detected_time.strftime("%H:%M")
            if self.reclaim_detected_time
            else None,
            "th_stop_loss": round(self.entry_price * (1 + self.stop_loss_pct), 2)
            if self.entry_price
            else None,
            "real_stop_loss": round(self.real_stop_loss, 2)
            if self.real_stop_loss
            else None,
            "stop_loss_time": self.real_stop_loss_time.strftime("%H:%M")
            if self.real_stop_loss_time
            else None,
            "high_after_entry": self.max_day_high,
            "high_after_entry_time": self.max_day_high_time.strftime("%H:%M")
            if self.max_day_high_time
            else None,
            "low_after_entry": self.low_day,
            "low_after_entry_time": self.low_day_time.strftime("%H:%M")
            if self.low_day_time
            else None,
            "eod": self.eod,
        }
        filename = f"/home/vcaldas/aptrade/science/breakout_{self.run_number}.csv"
        result_df = pd.DataFrame([result])
        file_exists = os.path.isfile(filename)
        if file_exists:
            df = pd.read_csv(filename)
            if not df.empty and not df.isna().all().all():
                df = pd.concat([df, result_df], ignore_index=True)
        else:
            df = result_df
        df.to_csv(filename, index=False)
        self.info.append(result)
