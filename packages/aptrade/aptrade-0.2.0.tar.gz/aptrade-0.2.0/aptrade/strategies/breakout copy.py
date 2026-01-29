import pandas as pd
from backtesting import Strategy
import datetime as dt
from pydantic import BaseModel, Field
import os


class CustomData(BaseModel):
    date: dt.date = Field(..., description="Date of the data point")


class BreakoutStrategy(Strategy):
    cooldown_minutes = 5  # Default cooldown period, can be set externally
    open_range_minutes = 10
    premarket_end = dt.time(9, 30)
    exit_minute_bar = dt.time(15, 59)
    risk_percent = 0.01
    stop_loss_pct = 0.30
    profit_target_pct = 0.30
    pull_back_threshold = 0.20  # 20% pullback
    high_move_threshold = 1.00  # 100% move
    reclaim_pct = 0.90  # 90% reclaim
    to_print = False  # Flag to control printing
    info: list = Field(
        default_factory=list, description="List to store results for each day"
    )
    symbol: str = ""  # Initialize symbol to None
    get_last_day_price: bool = True  # Whether to fetch last day's close from data
    run_number: int = 1  # To differentiate output files in different runs

    def init(self):
        self.current_day = None
        self.prev_close = None
        self.premarket_high = None
        self.premarket_high_time = None
        self.premarket_qualified = False
        self.pullback_detected = False
        self.pullback_detected_time = None
        self.pullback_low = None
        self.reclaim_detected = False
        self.reclaim_detected_time = None
        self.entry_price = None
        self.traded_today = False
        self.info = []
        self.theoretical_entry_price = None
        self.time_at_entry = None

        # self.symbol = kwargs.get("symbol", "")  # Initialize symbol to None
        self.full_pullback = None
        self.full_pullback_date = None
        self.stop_loss = None
        self.real_stop_loss = None
        self.real_stop_loss_time = None

        self.max_day_high = None  # Track max high of the day
        self.max_day_high_time = None  # Track time of max high

        self.low_day = None  # Track low of the day
        self.low_day_time = None  # Track time of low of the day

        self.eod = None
        # Flag to control full pullback logic

    def _reset_day(self, day, prev_close):
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

        self.max_day_high = None  # Track max high of the day
        self.max_day_high_time = None  # Track time of max high

        self.low_day = None  # Track low of the day
        self.low_day_time = None  # Track time of low of the day

        self.real_stop_loss = None
        self.real_stop_loss_time = None
        self.eod = None

    def next(self):
        t = self.data.index[-1]
        current_bar_date = t.date()
        current_time = t.time()
        # print(f"Current time: {current_time}, Date: {current_bar_date}")
        # Detect new day and get previous close
        if self.current_day != current_bar_date:
            # print(f"New day detected: {current_bar_date}")
            if self.get_last_day_price:
                # Find previous day's last close
                prev_day_mask = self.data.index.date < current_bar_date
                if prev_day_mask.any():
                    self.prev_close = self.data.Close[prev_day_mask][-1]
                else:
                    self.prev_close = None
            else:
                # prev_day = current_bar_date - dt.timedelta(days=1)
                # print(f"Previous day: {prev_day}")
                # print(current_bar_date)
                # target_time = dt.time(15, 59)
                # print(self.data.index.date)
                mask = (self.data.index.date < current_bar_date) & (
                    self.data.index.time <= dt.time(15, 59)
                )
                if mask.any():
                    self.prev_close = self.data.Close[mask][-1]
                else:
                    self.prev_close = None
            self._reset_day(current_bar_date, self.prev_close)
            self.prev_close = round(self.prev_close, 2) if self.prev_close else None

        # 1. Track pre-market high and check for >100% move
        if (
            current_time < self.premarket_end
            and self.prev_close
            and not self.pullback_detected
        ):
            if self.premarket_high is None or self.data.High[-1] > self.premarket_high:
                if (
                    self.data.High[-1] < 1.5 * self.data.Close[-1]
                ):  # Only consider highs above previous close
                    self.premarket_high = self.data.High[-1]
                    self.premarket_high_time = t

                # if self.to_print:
                # print(f"New pre-market high: {self.premarket_high} at {self.premarket_high_time}")

            move = (self.premarket_high - self.prev_close) / self.prev_close
            # if self.to_print:
            # print(f"{current_time} | {self.data.Close[-1]} :1.  Premarket  {self.premarket_high:.2f} is {move*100:.2f}% above {self.prev_close}")

            if move >= self.high_move_threshold:
                self.premarket_qualified = True
                self.entry_price = self.premarket_high * self.reclaim_pct
                self.theoretical_entry_price = self.premarket_high * self.reclaim_pct

        # 2. After 100% move, look for 20% pullback from high
        if self.premarket_qualified and not self.pullback_detected:
            # Only consider prices after premarket high
            if self.premarket_high_time and t > self.premarket_high_time:
                pullback = (
                    self.premarket_high - self.data.Low[-1]
                ) / self.premarket_high
                # if self.to_print:
                #     print(f"{current_time} | {self.data.Close[-1]} :2.  Pullback {pullback*100:.2f}% from high {self.premarket_high:.2f} to low {self.data.Close[-1]:.2f}")
                if pullback >= self.pull_back_threshold:
                    self.pullback_detected = True
                    self.pullback_low = self.data.Low[-1]
                    self.pullback_detected_time = t
                    self.full_pullback = self.data.Low[-1]
                    self.full_pullback_date = t
                    # if self.to_print:
                    #     print(f"{current_time} |+++++++ 2. Pullback detected: {pullback*100:.2f}% from high {self.premarket_high:.2f} to low {self.pullback_low:.2f}")

        # pct = 100 * (self.premarket_high - self.data.Close[-1]) / self.premarket_high
        # 3. Wait for reclaim to 90% of high (entry trigger)
        if self.pullback_detected and not self.reclaim_detected:
            reclaim_price = self.premarket_high * self.reclaim_pct
            # print(f"{current_time} | Reclaim price: {reclaim_price:.2f}, Current close: {self.data.High[-1]:.2f}")
            if self.data.High[-1] >= reclaim_price:
                self.reclaim_detected = True
                self.reclaim_detected_time = t
                self.entry_price = self.premarket_high * self.reclaim_pct
                # if self.to_print:
                #     print(f"++++++++++++++++ Reclaim detected: price {self.data.High[-1]:.2f} >= {reclaim_price:.2f}")
            if self.data.Low[-1] < self.full_pullback:
                self.full_pullback = self.data.Low[-1]
                self.full_pullback_date = t

        # 4. Enter short if not already in position and not traded today
        # Cooldown logic: only allow entry after cooldown_minutes have passed since reclaim_detected_time
        cooldown_delta = dt.timedelta(minutes=self.cooldown_minutes)
        if (
            self.reclaim_detected
            and not self.position
            and not self.traded_today
            and t > self.reclaim_detected_time + cooldown_delta
        ):
            stop_loss = self.entry_price * (1 + self.stop_loss_pct)
            self.stop_loss = stop_loss
            take_profit = self.entry_price * (1 - self.profit_target_pct)
            per_share_risk = abs(self.entry_price - stop_loss)
            position_size = int((self.risk_percent * self.equity) / per_share_risk)
            # if self.to_print:
            self.time_at_entry = t
            # print(f"Short entry at {self.entry_price:.2f}, stop {stop_loss:.2f}, tp {take_profit:.2f}, size {position_size}")
            # self.sell(size=position_size, sl=stop_loss, tp=take_profit)
            self.sell(size=position_size)
            self.traded_today = True
            self.low_day = self.data.Low[-1]
            self.low_day_time = t
            self.max_day_high = self.data.High[-1]  # Update max day high
            self.max_day_high_time = t  # Update time of max day high

        if self.traded_today:
            if self.data.High[-1] >= self.max_day_high:
                self.max_day_high = self.data.High[-1]  # Update max day high
                self.max_day_high_time = t  # Update time of max day high
            if self.data.Low[-1] <= self.low_day:
                self.low_day = self.data.Low[-1]
                self.low_day_time = t
                # if self.to_print:
                #     print(f"New low of the day: {self.low_day:.2f} at {self.low_day_time}")

        # 5. Close at end of day
        if self.position:
            # print(f"Current time: {current_time}, Date: {current_bar_date}")
            # print(current_time >= self.exit_minute_bar, self.exit_minute_bar)
            if current_time >= self.exit_minute_bar:
                # print("Close")
                # print(f"| {self.symbol} | Closing position at end of day")
                self.eod = self.data.Close[-1]
                self.position.close()
                self.write_results()
                # print("Closing position at end of day")
            # Check for stop loss or profit target
            if self.data.Close[-1] >= self.stop_loss:
                # print(f"| {self.symbol} | Closing position at stop loss: {self.data.Close[-1]:.2f} >= {self.stop_loss:.2f}")
                # self.position.close()
                # self.write_results()
                self.real_stop_loss = self.data.Close[-1]
                self.real_stop_loss_time = t
            # elif self.data.Close[-1] <= self.entry_price * (1 - self.profit_target_pct):
            #     self.position.close()
            #     if self.to_print:
            #         print(f"Closing position at profit target: {self.data.Close[-1]} <= {self.entry_price * (1 - self.profit_target_pct):.2f}")

            # elif self.data.Close[-1] >= self.entry_price * (1 + self.stop_loss_pct):
            #     self.position.close()
            #     if self.to_print:
            #         print(f"Closing position at stop loss: {self.data.Close[-1]} >= {self.entry_price * (1 + self.stop_loss_pct):.2f}")

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
            # print(f"6. Current equity: {self.equity:.2f}")

    def write_results(self):
        result = {
            "date": self.current_day,
            "symbol": self.symbol,
            "premarket_high": round(self.premarket_high, 2),
            "premarket_high_time": self.premarket_high_time.strftime("%H:%M"),
            "theoretical_pullback": self.premarket_high
            * (1 - self.pull_back_threshold),
            "max_pullback": round(self.full_pullback, 2),
            "max_pullback_date": self.full_pullback_date.strftime("%H:%M"),
            "th_entry_price": round(self.theoretical_entry_price, 2),
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
            "high_after_entry_time": self.max_day_high_time.strftime("%H:%M"),
            "low_after_entry": self.low_day,
            "low_after_entry_time": self.low_day_time.strftime("%H:%M"),
            "eod": self.eod,
        }

        filename = f"/home/vcaldas/aptrade/science/breakout_{self.run_number}.csv"

        result_df = pd.DataFrame([result])

        file_exists = os.path.isfile(filename)
        if file_exists:
            df = pd.read_csv(filename)
            df = pd.concat([df, result_df], ignore_index=True)
        else:
            df = result_df
        df.to_csv(filename, index=False)

        self.info.append(result)


def covert_to_datetime(dt_str):
    """Convert ISO format string to datetime object."""
    return dt.datetime.fromisoformat(dt_str).strftime("%H:%M")
