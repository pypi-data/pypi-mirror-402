# mypy: ignore-errors
# pyright: reportGeneralTypeIssues=false

import datetime as dt
import pandas as pd
import aptrade.backtrader as bt
from typing import Dict, Optional, Any
from pathlib import Path


class ORBMarcelo(bt.Strategy):
    params = (
        ("gap", float(1)),
        ("data_name", ""),
        ("pull_back_threshold", float(20)),
        ("printlog", True),
        ("cooldown_minutes", int(5)),
        ("stop_loss_pct", float(0.30)),
        ("profit_target_pct", float(0.30)),
    )

    events: Dict[str, Any] = {}
    pre_market_trade: bool = True
    market_opening_time: dt.time = dt.time(9, 30)
    exit_minute_bar: dt.time = dt.time(15, 55)
    risk_percent = 0.01
    high_move_threshold: float = 1.00
    reclaim_pct: float = 0.90

    def __init__(self):
        self.data_feed = self.datas[0]
        # self.daily_feed  = self.datas[1]

        label = str(getattr(self.params, "data_name", "")).strip()
        if not label:
            label = getattr(self.data_feed, "_name", None) or getattr(
                self.data_feed, "_dataname", None
            )
        self.data_label = label or "data_0"

        self.current_day: Optional[dt.date] = None
        self.prev_close: Optional[float] = None
        self.opening_range_high: Optional[float] = None
        self.opening_range_low: Optional[float] = None
        self.pull_back: Optional[float] = None  # tracks the pullback percentage
        self.hit_percentage: bool = False
        self.hit_pull_back: bool = False
        self.traded_today: bool = False  # tracks if we have traded today
        self.max_leverage: float = 1.0
        self.pull_back_detected = False
        self.premarket_high: Optional[float] = None
        self.premarket_high_time: Optional[dt.time] = None
        self.pullback_low: Optional[float] = None
        self.entry_price: Optional[float] = None
        self.theoretical_entry_price: Optional[float] = None
        self.reclaim_detected_time: Optional[dt.time] = None
        self.pb_time: Optional[dt.time] = None
        self.premarket_qualified: bool = False
        self.reclaim_detected: bool = False
        # self._closing_out: bool = False
        self._pending_close = None
        self.volume: float = 0.0
        self.volume_at_entry: float = 0.0
        self.order = None
        # self.percents = GapPercent(self.daily_feed)
        self.buyprice = None
        self.buycomm = None

    def log(self, txt, dt=None, doprint=False):
        """Logging function fot this strategy"""
        if self.params.printlog or doprint:
            dt = dt or self.data_feed.datetime.date(0)
            print("%s, %s" % (dt.isoformat(), txt))

    def _reset_day(self, day, prev_close=None, pull_back=None):
        """Reset the opening range at the start of a new day."""
        self.current_day = day
        self.prev_close = prev_close

        self.opening_range_high = None
        self.opening_range_low = None
        self.pull_back = pull_back  # tracks t  he pullback percentage
        self.hit_percentage = False
        self.hit_pull_back = False
        self.traded_today = False  # reset traded status for the new day
        # self._closing_out = False
        self._pending_close = None

        self.pull_back_detected = False
        self.premarket_high: Optional[float] = None
        self.premarket_high_time = None
        self.pb_time = None
        self.pullback_low = None
        self.entry_price = None
        self.theoretical_entry_price = None
        self.reclaim_detected_time = None
        self.premarket_qualified = False
        self.reclaim_detected = False
        self.volume = 0
        self.events = {}
        self.volume_at_entry = 0.0

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log(
            f"TRADE closed @ {trade.price:.2f} "
            f"size={trade.size} "
            f"pnl={trade.pnl:.2f} "
            f"pnlcomm={trade.pnlcomm:.2f}"
        )

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    "BUY EXECUTED, Price: %.2f, Cost: %.2f, Size: %.2f Comm %.2f"
                    % (
                        order.executed.price,
                        order.executed.value,
                        order.executed.size,
                        order.executed.comm,
                    )
                )

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            if order.issell():  # Sell
                self.log(
                    "SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f"
                    % (order.executed.price, order.executed.value, order.executed.comm)
                )

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        self.order = None

    def start(self):
        self.dtstart = dt.datetime.now()
        # print('Strat Start Time:            {}'.format(self.dtstart))

    def next(self):
        if self.order:
            return
        data = self.data_feed
        # data_daily = self.daily_feed

        current_dt = data.datetime.datetime(0)
        current_day = current_dt.date()
        position = self.getposition(data)
        self.volume += data.volume[0]

        # Detect new day and get previous close
        if current_day != self.current_day:
            # prev_close = self.daily_feed.close[-1]
            history = min(len(data), 500)
            # previous_day = current_day - dt.timedelta(days=1)
            # print(
            #     f"Searching previous day ({previous_day}) for first bar at/after 16:55"
            # )
            for ago in range(1, history):
                bar_dt = data.datetime.datetime(-ago)
                bar_close = data.close[-ago]
                # print(f"  ago={ago} dt={bar_dt} close={data.close[-ago]}")

                if bar_dt.time() < dt.time(16, 00):
                    self.prev_close = data.close[-ago]
                    prev_close_time = bar_dt
                    # print(
                    #     f"Selected prev_close={self.prev_close} at {bar_dt} (idx={-ago})"
                    # )
                    break
            self._reset_day(
                current_day,
                prev_close=self.prev_close,
            )

        ## Track pre-market high and low for opening range
        if not self.pull_back_detected:
            if self.premarket_high is None or data.high[0] > self.premarket_high:
                self.premarket_high = data.high[0]
                self.premarket_high_time = current_dt
                self.theoretical_pull_back = data.high[0] * (
                    1 - self.params.pull_back_threshold / 100
                )

            if self.premarket_high and self.prev_close:
                move = (self.premarket_high - self.prev_close) / self.prev_close
                if move >= self.high_move_threshold:
                    self.premarket_qualified = True
                    self.entry_price = self.premarket_high * self.reclaim_pct
                    self.theoretical_entry_price = (
                        self.premarket_high * self.reclaim_pct
                    )

        #     # 2. After 100% move, look for 20% pullback from high
        if self.premarket_qualified and not self.pull_back_detected:
            if self.premarket_high_time and current_dt > self.premarket_high_time:
                pullback = (self.premarket_high - data.low[0]) / self.premarket_high
                if pullback >= self.params.pull_back_threshold / 100:
                    # print(f"Pullback detected: {pullback*100:.2f}% at {current_dt}")
                    self.pull_back_detected = True
                    self.pullback_low = data.low[0]
                    self.full_pullback = data.low[0]

        # 3. Wait for reclaim to 90% of high (entry trigger)
        if (
            self.pull_back_detected
            and not self.reclaim_detected
            and self.premarket_high
        ):
            reclaim_price = self.premarket_high * self.reclaim_pct
            if data.high[0] >= reclaim_price:
                self.reclaim_detected = True
                self.reclaim_detected_time = current_dt
                self.entry_price = reclaim_price
                # print(f"reclaim detected: {reclaim_price:.2f} at {current_dt}")
            if data.low[0] < (
                self.full_pullback if self.full_pullback is not None else data.low[0]
            ):
                self.full_pullback = data.low[0]
                self.full_pullback_date = current_dt
                self.pb_time = current_dt

        # 4. Enter short if not already in position and not traded today, after cooldown
        cooldown_delta = dt.timedelta(minutes=self.params.cooldown_minutes)
        if (
            self.reclaim_detected
            and not self.traded_today
            and self.reclaim_detected_time
            and current_dt > self.reclaim_detected_time + cooldown_delta
        ):
            self.theoretical_stop_loss = self.entry_price * (
                1 + self.params.stop_loss_pct
            )
            take_profit = (
                self.entry_price * (1 - self.params.profit_target_pct)
                if self.entry_price
                else None
            )

            self.time_at_entry = current_dt
            self.order = self.sell(
                data=data,
                exectype=bt.Order.Market,
            )

            self.volume_at_entry = self.volume
            self.traded_today = True
            self.low_day = data.low[0]
            self.low_day_time = current_dt
            self.max_day_high = data.high[0]
            self.max_day_high_time = current_dt

        # 6. Close at end of day or on stop loss
        position = self.getposition(data)
        if position.size and current_dt.time() >= self.exit_minute_bar:
            self.order = self.close(data=data)
            self.write_event()

    def write_event(self):
        export_path = Path("/home/vcaldas/aptrade/results")
        export_path.mkdir(parents=True, exist_ok=True)
        outfile = export_path / "events_test.csv"

        payload = {
            "datetime": self.current_day.isoformat() if self.current_day else None,
            "symbol": self.data_label,
            "previous_day_close": self.prev_close,
            "gap_trigger": self.prev_close * (1 + self.high_move_threshold),
            "premarket_high": self.premarket_high,
            "premarket_high_time": self.premarket_high_time.isoformat()
            if self.premarket_high_time
            else None,
            "pull_back_theoretical": self.theoretical_pull_back,
            "pull_back_low": self.pullback_low,
            "pull_back_full": self.full_pullback,
            "pull_back_time": self.pb_time.isoformat() if self.pb_time else None,
            "theoretical_entry_price": self.theoretical_entry_price,
            "entry_price": self.entry_price,
            "entry_time": self.reclaim_detected_time.isoformat()
            if self.reclaim_detected_time
            else None,
            "stop_loss_theoretical": round(self.theoretical_stop_loss, 3),
            "volume_at_entry": self.volume_at_entry,
            "total_volume": self.volume,
        }
        df = pd.DataFrame([payload]).set_index("symbol")
        if outfile.exists():
            df = pd.concat([pd.read_csv(outfile, index_col="symbol"), df])
        df.to_csv(outfile)

    def prenext(self):
        if len(self.data0) == 1:  # only 1st time
            self.dtprenext = dt.datetime.now()
            # print('Pre-Next Start Time:         {}'.format(self.dtprenext))
            # indcalc = (self.dtprenext - self.dtstart).total_seconds()
            # print('Time Calculating Indicators: {:.2f}'.format(indcalc))

    def nextstart(self):
        if len(self.data0) == 1:  # there was no prenext
            self.dtprenext = dt.datetime.now()
            # print('Pre-Next Start Time:         {}'.format(self.dtprenext))
            # indcalc = (self.dtprenext - self.dtstart).total_seconds()
            # print('Time Calculating Indicators: {:.2f}'.format(indcalc))

        self.dtnextstart = dt.datetime.now()
        # if self.params.printlog:
        #     print("Next Start Time:             {}".format(self.dtnextstart))
        #     warmup = (self.dtnextstart - self.dtprenext).total_seconds()
        #     print("Strat warm-up period Time:   {:.2f}".format(warmup))
        #     nextstart = (self.dtnextstart - self.env.dtcerebro).total_seconds()
        #     print("Time to Strat Next Logic:    {:.2f}".format(nextstart))
        self.next()

    def stop(self):
        if self.params.printlog:
            self.log(
                "(pull_back_threshold %2d) Ending Value %.2f"
                % (self.params.pull_back_threshold, self.broker.getvalue()),
                doprint=True,
            )
            dtstop = dt.datetime.now()
            print("End Time:                    {}".format(dtstop))
            nexttime = (dtstop - self.dtnextstart).total_seconds()
            print("Time in Strategy Next Logic: {:.2f}".format(nexttime))
            strattime = (dtstop - self.dtprenext).total_seconds()
            print("Total Time in Strategy:      {:.2f}".format(strattime))
            totaltime = (dtstop - self.env.dtcerebro).total_seconds()
            print("Total Time:                  {:.2f}".format(totaltime))
            print("Length of data feeds:        {}".format(len(self.data)))
