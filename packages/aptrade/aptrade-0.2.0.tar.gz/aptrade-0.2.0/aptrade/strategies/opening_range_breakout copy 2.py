# mypy: ignore-errors
# pyright: reportGeneralTypeIssues=false

import datetime as dt
import aptrade.backtrader as bt
from typing import Optional


class OpeningRangeBreakout(bt.Strategy):
    params = (
        ("gap", float(1)),
        ("pull_back_threshold", float(20)),
        ("printlog", False),
    )
    open_range_minutes = 10
    cooldown_minutes = 5
    pre_market_trade: bool = True
    pre_market_end: dt.time = dt.time(9, 30)
    exit_minute_bar: dt.time = dt.time(15, 50)
    stop_loss_pct: float = 0.30
    profit_target_pct: float = 0.30

    last_minute_bar_in_opening_range = dt.time(9, 20 + open_range_minutes)
    risk_percent = 0.01
    take_profit_multiple = 10
    # pull_back_threshold = 20  # pullback threshold in percentage
    daily_high_threshold = 100  # daily high threshold in percentage
    high_move_threshold: float = 1.00
    reclaim_pct: float = 0.90

    def __init__(self):
        self.current_day: Optional[dt.date] = None
        self.prev_close: Optional[float] = None

        self.current_day_open: Optional[float] = None
        self.opening_range_high: Optional[float] = None
        self.opening_range_low: Optional[float] = None
        self.pre_market_close: Optional[float] = None
        self.pull_back: Optional[float] = None  # tracks the pullback percentage
        self.hit_percentage: bool = False
        self.hit_pull_back: bool = False
        self.traded_today: bool = False  # tracks if we have traded today
        self.max_leverage: float = 1.0

    def log(self, txt, dt=None, doprint=False):
        """Logging function fot this strategy"""
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print("%s, %s" % (dt.isoformat(), txt))

    def _reset_day(self, day, open, pre_market_close=None, pull_back=None):
        """Reset the opening range at the start of a new day."""
        self.current_day = day
        self.prev_close = None

        self.opening_range_high = None
        self.opening_range_low = None
        self.current_day_open = open
        self.pre_market_close = pre_market_close
        self.pull_back = pull_back  # tracks the pullback percentage
        self.hit_percentage = False
        self.hit_pull_back = False
        self.traded_today = False  # reset traded status for the new day

    def notify_trade(self, trade):
        if trade.isclosed:
            self.log(
                f"TRADE closed @ {trade.price:.2f} "
                f"size={trade.size} "
                f"pnl={trade.pnl:.2f} "
                f"pnlcomm={trade.pnlcomm:.2f}"
            )

    def _get_position_size(self, entry_price: float, stop_price: float) -> int:
        per_share_risk = abs(entry_price - stop_price)  #  |P − S|  =  R

        if per_share_risk == 0:
            return 0

        # Risk-based cap: position that loses 1 % of equity at the stop
        account_value = self.broker.getvalue()
        shares_by_risk = (self.risk_percent * account_value) / per_share_risk

        # Leverage-based cap: shares affordable with 4× buying power
        buying_power = account_value * self.max_leverage
        shares_by_leverage = buying_power / entry_price if entry_price else 0

        # Final size: smaller of the two, floored to an int
        return int(min(shares_by_risk, shares_by_leverage))

    def next(self):
        data = self.datas[0]
        current_dt = data.datetime.datetime(0)
        current_day = current_dt.date()
        prev_close_time = None
        # print(data.close[0], current_dt)

        # Detect new day and get previous close
        if current_day != self.current_day:
            prev_close = data.close[-1] if len(data) > 1 else None

            self.pre_market_close = None
            history = min(len(data), 500)
            previous_day = current_day - dt.timedelta(days=1)
            # print(
            #     f"Searching previous day ({previous_day}) for first bar at/after 16:55"
            # )
            for ago in range(1, history):
                bar_dt = data.datetime.datetime(-ago)
                bar_close = data.close[-ago]
                # print(f"  ago={ago} dt={bar_dt} close={data.close[-ago]}")

                if bar_dt.time() <= dt.time(16, 00):
                    self.pre_market_close = data.close[-ago]
                    prev_close_time = bar_dt
                    # print(
                    #     f"Selected pre_market_close={self.pre_market_close} at {bar_dt} (idx={-ago})"
                    # )
                    break
            else:
                print("No qualifying bar found; pre_market_close remains None")

            self._reset_day(
                current_day,
                data.open[0],
                pre_market_close=self.pre_market_close,
            )

            # print(
            #     f"[{current_dt}] prev_close={prev_close} - { prev_close_time} "
            #     f"open={data.open[0]} high={data.high[0]} low={data.low[0]} close={data.close[0]}"
            # )

            if self.pre_market_close is not None:
                open_price = data.open[0]
                pct_change = (
                    100 * (open_price - self.pre_market_close) / self.pre_market_close
                )
                print(f"% Change from pre-market close to open: {pct_change:.2f}%")

        if current_dt.time() < self.last_minute_bar_in_opening_range:
            current_high = data.high[0]
            current_low = data.low[0]

            self.opening_range_high = (
                max(self.opening_range_high, current_high)
                if self.opening_range_high is not None
                else current_high
            )
            self.opening_range_low = (
                min(self.opening_range_low, current_low)
                if self.opening_range_low is not None
                else current_low
            )

            return

        if current_dt.time() == self.last_minute_bar_in_opening_range:
            print(f"opening range high is {self.opening_range_high}")
            print(f"opening range low is {self.opening_range_low}")
            if self.opening_range_high and self.opening_range_low:
                pct = (
                    100
                    * (self.opening_range_high - self.opening_range_low)
                    / self.opening_range_low
                )
                print(f"{current_dt.time()}  =  opening range percentage is {pct:.2f}%")
                if pct > self.daily_high_threshold:
                    self.hit_percentage = True
                    print(
                        f"{current_dt.time()}  = Opening range percentage hit threshold: {pct:.2f}%"
                    )

        if current_dt.time() >= self.last_minute_bar_in_opening_range:
            if self.opening_range_high and self.opening_range_low:
                draw = (
                    100
                    * (self.opening_range_high - data.close[0])
                    / self.opening_range_low
                )
                self.pull_back = draw
                if draw > self.params.pull_back_threshold:
                    self.hit_pull_back = True

        if not self.position and not self.traded_today:
            planned_entry_price = data.close[0]

            if self.hit_percentage and self.hit_pull_back and self.opening_range_high:
                stop_loss_price = self.opening_range_high
                per_share_risk = abs(planned_entry_price - stop_loss_price)
                if per_share_risk > 0:
                    position_size = self._get_position_size(
                        planned_entry_price, stop_loss_price
                    )
                    take_profit_price = planned_entry_price * 0.70
                    print("take_profit_price", take_profit_price, current_dt.time())
                    print(
                        f"going short, position size {position_size} shares at planned price {planned_entry_price}, stop loss {stop_loss_price}"
                    )
                    self.sell(
                        size=position_size,
                        price=planned_entry_price,
                        exectype=bt.Order.Market,
                    )
                    self.traded_today = True
        if self.position and current_dt.time() >= self.exit_minute_bar:
            print("closing out position")
            self.close()

    def stop(self):
        self.log(
            "(pull_back_threshold %2d) Ending Value %.2f"
            % (self.params.pull_back_threshold, self.broker.getvalue()),
            doprint=True,
        )
