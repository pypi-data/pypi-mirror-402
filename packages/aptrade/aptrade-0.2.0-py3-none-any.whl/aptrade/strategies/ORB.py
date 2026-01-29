# mypy: ignore-errors
# pyright: reportGeneralTypeIssues=false

import datetime as dt
import pandas as pd
import aptrade.backtrader as bt
from typing import Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
from aptrade.backtrader import date2num


@dataclass
class ORBData:
    name: str
    prev_close: float | None = None
    current_day: dt.date | None = None
    volume: float = 0.0
    events: dict[str, Any] = field(default_factory=dict)
    opening_range_high: Optional[float] = None
    opening_range_low: Optional[float] = None
    pull_back: Optional[float] = None
    hit_percentage: bool = False
    hit_pull_back: bool = False
    traded_today: bool = False
    max_leverage: float = 1.0
    pull_back_detected: bool = False
    premarket_high: Optional[float] = None
    premarket_high_time: Optional[dt.datetime] = None
    pullback_low: Optional[float] = None
    entry_price: Optional[float] = None
    theoretical_entry_price: Optional[float] = None
    reclaim_detected_time: Optional[dt.datetime] = None
    pb_time: Optional[dt.datetime] = None
    premarket_qualified: bool = False
    reclaim_detected: bool = False
    _pending_close: Any | None = None
    volume_at_entry: float = 0.0
    full_pullback: Optional[float] = None
    full_pullback_date: Optional[dt.datetime] = None
    theoretical_pull_back: Optional[float] = None
    theoretical_stop_loss: Optional[float] = None
    time_at_entry: Optional[dt.datetime] = None
    low_day: Optional[float] = None
    low_day_time: Optional[dt.datetime] = None
    max_day_high: Optional[float] = None
    max_day_high_time: Optional[dt.datetime] = None
    # order: Any | None = None

    def reset_day(self, day, prev_close=None, pull_back=None):
        """Reset the opening range at the start of a new day."""
        self.current_day = day
        self.prev_close = prev_close

        self.opening_range_high = None
        self.opening_range_low = None
        self.pull_back = pull_back
        self.hit_percentage = False
        self.hit_pull_back = False
        self.traded_today = False
        self._pending_close = None

        self.pull_back_detected = False
        self.premarket_high = None
        self.premarket_high_time = None
        self.pb_time = None
        self.pullback_low = None
        self.entry_price = None
        self.theoretical_entry_price = None
        self.reclaim_detected_time = None
        self.premarket_qualified = False
        self.reclaim_detected = False
        self.volume = 0.0
        self.events = {}
        self.volume_at_entry = 0.0
        self.full_pullback = None
        self.full_pullback_date = None
        self.theoretical_pull_back = None
        self.theoretical_stop_loss = None
        self.time_at_entry = None
        self.low_day = None
        self.low_day_time = None
        self.max_day_high = None
        self.max_day_high_time = None
        # self.order = None

    def add_volume(self, vol: float):
        self.volume += vol


class OpeningRangeBreakout(bt.Strategy):
    params = (
        ("gap", float(1)),
        ("pull_back_threshold", float(20)),
        ("printlog", False),
        ("cooldown_minutes", int(4)),
        ("stop_loss_pct", float(0.30)),
        ("profit_target_pct", float(0.30)),
        ("reclaim_pct", float(0.90)),
        ("high_move_threshold", float(1.00)),
        ("trail", False),
        ("debug", False),
    )

    events: Dict[str, Any] = {}
    pre_market_trade: bool = True
    market_opening_time: dt.time = dt.time(9, 30)
    exit_minute_bar: dt.time = dt.time(15, 30)
    market_close_time: dt.time = dt.time(15, 59)
    entry_time_limit: dt.time = dt.time(14, 0)
    risk_percent = 0.01

    def __init__(self):
        self.o: dict[bt.feed.DataBase, list[bt.Order | None]] = {}
        # self.holding: dict[bt.feed.DataBase, int] = {}
        self.state: dict[bt.feed.DataBase, ORBData] = {}
        # self.data_feed = self.datas[0]
        # self.daily_feed  = self.datas[1]

        for i, data in enumerate(self.datas):
            label = getattr(data, "_name", f"data_{i}") or getattr(
                data, "_dataname", f"data_{i}"
            )
            self.state[label] = ORBData(name=label)
            self.o[label] = []
            # self.holding[data] = 0

    def log(self, txt, dt=None, doprint=False):
        """Logging function fot this strategy"""
        if self.params.printlog or doprint:
            # dt = dt or self.datas[0].datetime.datetime(0)
            print("%s, %s" % (dt.isoformat(), txt))

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        dt = trade.data.datetime.datetime(0)
        self.log(
            f"{trade.data._name} | TRADE cloed @ {trade.price:.2f} "
            f"size={trade.size} "
            f"pnl={trade.pnl:.2f} "
            f"pnlcomm={trade.pnlcomm:.2f}",
            dt=dt,
            doprint=True,
        )

    def notify_order(self, order):
        # print("Order Submitted", order.__dict__, order.data._name)

        # if not order.status == order.Completed:
        #     print("Order Submitted")
        #     return  # discard any other notification

        _, dn = self.datetime.date(), order.data._name
        dt_minute = order.data.datetime.datetime(0)
        print(
            "{} {} Order {} Status {}".format(
                dt_minute, dn, order.ref, order.getstatusname()
            )
        )

        if order.status == order.Submitted:
            # print("Order Submitted", order.data._name)
            return

        whichord = ["main", "stop", "limit", "close"]
        # print(order.alive(), self.o[order.data._name])
        if not order.alive():  # not alive - nullify
            dorders = self.o[order.data._name]

            try:
                idx = dorders.index(order)
                dorders[idx] = None
                print("-- No longer alive {} Ref".format(whichord[idx]))

                if all(x is None for x in dorders):
                    dorders[:] = []  # empty list - New orders allowed
            except Exception as e:
                print("Order not found in pending orders list", e)
                print("Order with error: ", order)
                pass

    def start(self):
        self.dtstart = dt.datetime.now()
        # print('Strat Start Time:            {}'.format(self.dtstart))

    def next(self):
        for data in self.datas:
            self.next_single_data(data)

    def next_single_data(self, data):
        current_day, dn = self.datetime.date(), data._name
        current_dt = data.datetime.datetime(0)

        # No trading outside market hours
        if current_dt.time() >= self.market_close_time:
            return

        s = self.state[dn]
        pos = self.getposition(data).size

        if current_day != s.current_day:
            history = min(len(data), 500)
            for ago in range(1, history):
                bar_dt = data.datetime.datetime(-ago)

                if bar_dt.time() < dt.time(16, 00):
                    s.prev_close = data.close[-ago]
                    break

            s.reset_day(
                current_dt.date(),
                prev_close=s.prev_close,
            )
        s.volume += float(data.volume[0])
        # self.log(
        #     f"{s.name} Open: {data.open[0]:.2f} High: {data.high[0]:.2f} Low: {data.low[0]:.2f} Close: {data.close[0]:.2f} Vol: {data.volume[0]:.0f}",
        #     dt=current_dt, doprint=self.params.debug
        # )
        # Track pre-market high and low for opening range
        # print(s.name, s.pull_back_detected, s.premarket_qualified, s.reclaim_detected)
        if not s.pull_back_detected:
            if s.premarket_high is None or data.high[0] > s.premarket_high:
                s.premarket_high = data.high[0]
                s.premarket_high_time = current_dt
                s.theoretical_pull_back = data.high[0] * (
                    1 - self.params.pull_back_threshold / 100
                )
                self.log(
                    f"{s.name} New high {s.premarket_high:.2f} at {current_dt}",
                    dt=current_dt,
                    doprint=self.params.debug,
                )

            if s.premarket_high and s.prev_close:
                move = (s.premarket_high - s.prev_close) / s.prev_close
                if move >= self.params.high_move_threshold:
                    s.premarket_qualified = True
                    s.entry_price = s.premarket_high * self.params.reclaim_pct
                    s.theoretical_entry_price = (
                        s.premarket_high * self.params.reclaim_pct
                    )
                    self.log(
                        f"{s.name} qualified: move {(move*100):.1f}% prev_close {s.prev_close:.2f} | entry {s.entry_price:.2f} | data.high {data.high[0]:.2f}",
                        dt=current_dt,
                        doprint=self.params.debug,
                    )

        # 2. After 100% move, look for 20% pullback from high
        if s.premarket_qualified and not s.pull_back_detected:
            if s.premarket_high_time and current_dt > s.premarket_high_time:
                pullback = (s.premarket_high - data.low[0]) / s.premarket_high
                if pullback >= self.params.pull_back_threshold / 100:
                    # print(f"Pullback detected: {pullback*100:.2f}% at {current_dt}")
                    s.pull_back_detected = True
                    s.pullback_low = data.low[0]
                    s.full_pullback = data.low[0]
                    self.log(
                        f"{s.name} pullback {(pullback*100):.1f}% low {s.pullback_low:.2f}",
                        dt=current_dt,
                        doprint=self.params.debug,
                    )

        # 3. Wait for reclaim to 90% of high (entry trigger)
        if (
            s.pull_back_detected and not s.reclaim_detected
            # and s.premarket_high
        ):
            reclaim_price = s.premarket_high * self.params.reclaim_pct
            if data.high[0] >= reclaim_price:
                s.reclaim_detected = True
                s.reclaim_detected_time = current_dt
                s.entry_price = reclaim_price
                print(f"reclaim detected: {reclaim_price:.2f} at {current_dt}")
                self.log(
                    f"{s.name} reclaim >= {reclaim_price:.2f} at {current_dt}",
                    dt=current_dt,
                    doprint=self.params.debug,
                )
            if data.low[0] < (
                s.full_pullback if s.full_pullback is not None else data.low[0]
            ):
                s.full_pullback = data.low[0]
                s.full_pullback_date = current_dt
                s.pb_time = current_dt

        # 4. Enter short if not already in position and not traded today, after cooldown
        cooldown_delta = dt.timedelta(minutes=self.params.cooldown_minutes)
        if (
            s.reclaim_detected
            and not s.traded_today
            # and s.reclaim_detected_time
            and current_dt > s.reclaim_detected_time + cooldown_delta
            # and current_dt.time() < self.market_close_time
            and current_dt.time() > self.market_opening_time
            and current_dt.time() < self.entry_time_limit
        ):
            s.theoretical_stop_loss = s.entry_price * (1 + self.params.stop_loss_pct)
            print(
                f"Entry conditions met at {current_dt} | entry price {s.entry_price:.2f} | stop loss {s.theoretical_stop_loss:.2f}"
            )
            s.time_at_entry = current_dt
            if not pos and not self.o.get(data, None):
                exit_dt = dt.datetime.combine(current_dt.date(), self.exit_minute_bar)
                order = self.sell(
                    data=data,
                    exectype=bt.Order.Market,
                    valid=date2num(exit_dt),
                )
                self.o[dn].append(order)
                print(len(self.o), dn, current_dt)
                # Configure stop loss and profit target
                if not self.params.trail:
                    print(
                        "Placing Stop Order at {:.2f}".format(s.theoretical_stop_loss)
                    )
                    _order = self.close(
                        data=data, exectype=bt.Order.Stop, price=s.theoretical_stop_loss
                    )
                else:
                    print(
                        "Placing Trailing Stop Order with trail amount {:.2f}".format(
                            s.entry_price * self.params.stop_loss_pct
                        )
                    )
                    _order = self.close(
                        data=data,
                        exectype=bt.Order.StopTrail,
                        trailamount=self.params.trail,
                    )
                self.o[dn].append(_order)
                # print('{} {} Sell {}'.format(current_dt, dn, order.ref))

            s.volume_at_entry = s.volume
            s.traded_today = True
            s.low_day = data.low[0]
            s.low_day_time = current_dt
            s.max_day_high = data.high[0]
            s.max_day_high_time = current_dt

        # # 6. Close at end of day or on stop loss
        if pos and s.theoretical_stop_loss and len(self.o[dn]) == 0:
            if data.close[0] >= s.theoretical_stop_loss:
                # if data.close[0] > sell
                print("HIT STOP LOSS")
                close_order = self.close(data=data, exectype=bt.Order.Market)
                print(pos, current_dt.time(), self.exit_minute_bar)
                print("{} {} Close {}".format(current_day, dn, close_order.ref))
                self.log(
                    f"{s.name} Open: {data.open[0]:.2f} High: {data.high[0]:.2f} Low: {data.low[0]:.2f} Close: {data.close[0]:.2f} Vol: {data.volume[0]:.0f}",
                    dt=current_dt,
                    doprint=True,
                )
                self.o[dn].append(close_order)

        if pos and len(self.o[dn]) == 0 and current_dt.time() >= self.exit_minute_bar:
            print(pos, current_dt, len(self.o[dn]), self.o[dn], data.close[0])
            close_order = self.close(data=data, exectype=bt.Order.Market)
            # print(pos, current_dt.time(), self.exit_minute_bar)
            print("{} {} Close  {}".format(current_dt.time(), dn, close_order.ref))
            self.log(
                f"{s.name} Open: {data.open[0]:.2f} High: {data.high[0]:.2f} Low: {data.low[0]:.2f} Close: {data.close[0]:.2f} Vol: {data.volume[0]:.0f}",
                dt=current_dt,
                doprint=True,
            )
            self.o[dn].append(close_order)
            # for order in self.o[dn]:
            #     print(order.__dict__, order.data._name, order.status)
            self.write_event(s)

            # print(current_dt, s)

    def write_event(self, s):
        export_path = Path("/home/vcaldas/aptrade/results/stocks")
        export_path.mkdir(parents=True, exist_ok=True)
        # outfile = export_path / f"{s.name}.csv"
        outfile2 = Path("/home/vcaldas/aptrade/results/stocks/all_trades.csv")

        payload = {
            "datetime": s.current_day.isoformat() if s.current_day else None,
            "symbol": s.name,
            "previous_day_close": s.prev_close,
            "gap_trigger": (
                s.prev_close * (1 + self.params.high_move_threshold)
                if s.prev_close is not None
                else None
            ),
            "premarket_high": s.premarket_high,
            "premarket_high_time": s.premarket_high_time.isoformat()
            if s.premarket_high_time
            else None,
            "pull_back_theoretical": s.theoretical_pull_back,
            "pull_back_low": s.pullback_low,
            "pull_back_full": s.full_pullback,
            "pull_back_time": s.pb_time.isoformat() if s.pb_time else None,
            "theoretical_entry_price": s.theoretical_entry_price,
            "entry_price": s.entry_price,
            "entry_time": s.reclaim_detected_time.isoformat()
            if s.reclaim_detected_time
            else None,
            "stop_loss_theoretical": (
                round(s.theoretical_stop_loss, 3)
                if s.theoretical_stop_loss is not None
                else None
            ),
            "volume_at_entry": s.volume_at_entry,
            "total_volume": s.volume,
        }
        df2 = pd.DataFrame([payload]).set_index("symbol")

        # if outfile.exists():
        #     df = pd.concat([pd.read_csv(outfile, index_col="symbol"), df])
        # df.to_csv(outfile)

        if outfile2.exists():
            df2 = pd.concat([pd.read_csv(outfile2, index_col="symbol"), df2])
        df2.to_csv(outfile2)

    def nextstart(self):
        self.next()

    # def stop(self):
    #     if self.params.printlog:
    #         self.log(
    #             "(pull_back_threshold %2d) Ending Value %.2f"
    #             % (self.params.pull_back_threshold, self.broker.getvalue()),
    #             doprint=True,
    #         )
