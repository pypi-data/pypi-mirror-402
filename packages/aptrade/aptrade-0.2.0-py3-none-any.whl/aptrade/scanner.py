from massive import RESTClient  # type: ignore
from massive.rest.models import (  # type: ignore
    TickerSnapshot,
)
import json
import os
from aptrade.core.config import settings
from pathlib import Path
import time
from datetime import date, datetime, timezone
import logging
from typing import List, Union, cast
from sqlmodel import Session
from aptrade.database import engine
from aptrade.database.models.opening import add_opening_breakout
from aptrade.telegram_bot import TelegramBot
import asyncio
import threading

client = RESTClient(settings.MASSIVE_API_KEY)

# Set up logger to write to a file
logging.basicConfig(
    filename="scanner.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

telegram_bot = TelegramBot()


class GapScanner:
    def __init__(
        self, filename: Path = Path("scanner_data.json"), poll_interval: float = 5.0
    ) -> None:
        self.filename: Path = filename
        self.client: RESTClient = RESTClient(settings.MASSIVE_API_KEY)
        self.poll_interval: float = poll_interval
        if os.path.exists(self.filename):
            with open(self.filename, "r") as f:
                try:
                    self.data = json.load(f)
                except Exception:
                    self.data = []
        else:
            self.data = []

        # nothing to initialize for DB-only mode

    def _today_date_str(self) -> str:
        return date.today().isoformat()

    def refresh(self, threshold: float = 50.0):
        gainers: List[TickerSnapshot] = []

        try:
            while True:
                now = datetime.now(timezone.utc)
                print(self._today_date_str())
                tickers = self.client.get_snapshot_direction(
                    "stocks",
                    direction="gainers",
                )
                ticker_count = len(tickers) if hasattr(tickers, "__len__") else 0

                print(
                    f"{now.strftime('%Y-%m-%d %H:%M:%S')} | Fetched {ticker_count} tickers from Massive API"
                )

                for item in tickers:
                    # verify this is a TickerSnapshot
                    if isinstance(item, TickerSnapshot):
                        # verify this is a float
                        if isinstance(item.todays_change_percent, float):
                            if item.todays_change_percent >= threshold:
                                print(
                                    f"Found gapper: {item.ticker} {item.todays_change_percent}%"
                                )
                                gainers.append(item)

                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            print("OpeningRangeScanner stopped by user")

        print("Refreshing GapScanner data...")

        # gainers: List[TickerSnapshot] = []
        # for item in tickers:
        #     # verify this is a TickerSnapshot
        #     if isinstance(item, TickerSnapshot):
        #         # verify this is a float
        #         if isinstance(item.todays_change_percent, float):
        #             if item.todays_change_percent >= threshold:
        #                 gainers.append(item)

        # # open a DB session for batch operations
        # with Session(engine) as session:
        #     for g in gainers:
        #         # ensure ticker and pct are present
        #         if not getattr(g, "ticker", None):
        #             continue
        #         if not getattr(g, "todays_change_percent", None):
        #             continue

        #         ticker = str(g.ticker)
        #         data = getattr(g, "min") if g.min else getattr(g, "day")
        #         previous_day = getattr(g, "prev_day")
        #         pct = 100 * (data.high - previous_day.close) / previous_day.close

        #         volume = getattr(data, "volume", "")
        #         # persist to DB; add_or_update_gapper returns (gapper, changed, is_new)
        #         day_found = date.today()
        #         ts = int(time.time())
        #         print(g)
        #         _gobj, changed, is_new = add_or_update_gapper(
        #             session=session,
        #             symbol=ticker,
        #             percent_change=round(pct, 2),
        #             day_found=day_found,
        #             open=getattr(data, "open", None),
        #             high=getattr(data, "high", None),
        #             low=getattr(data, "low", None),
        #             close=getattr(data, "close", None),
        #             volume=volume if isinstance(volume, (int, float)) else None,
        #             previous_close=getattr(previous_day, "close", None),
        #             ts=ts,
        #         )

        #         # Logging / notification
        #         if is_new:
        #             print(f"New stock found: {ticker} {pct:.2f}%")
        #             # schedule notification
        #             # self._notify_new_ticker(ticker, pct)

        #         elif changed and not is_new:
        #             print(f"Updated gap (higher) for: {ticker} {pct:.2f}%")

        #         # no CSV: history persisted in DB already
        #         print("{:<15}{:.2f} %".format(ticker, pct))

    def _notify_new_ticker(self, ticker: str, pct: float) -> None:
        """Schedule the async Telegram notification safely.

        If there's a running event loop, create a task. Otherwise run the coroutine
        in a background thread with its own loop to avoid blocking.
        """
        coro = telegram_bot.notify_new_ticker(ticker, pct)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            try:
                asyncio.create_task(coro)
            except Exception:
                # fallback to thread
                threading.Thread(target=lambda: asyncio.run(coro), daemon=True).start()
        else:
            threading.Thread(target=lambda: asyncio.run(coro), daemon=True).start()


class OpeningRangeScanner:
    """Scanner that detects opening-range breakouts for a set of symbols.

    This implementation is defensive: it will try to use a `get_trades` method on
    the Massive REST client if available; otherwise it will fall back to polling
    snapshots. It prints each trade, resamples trades per-minute into OHLCV,
    and when the price breaks above the opening-range high (first N minutes),
    it persists a row into the `OpeningBreakout` table.
    """

    def __init__(
        self,
        symbols: list[str],
        opening_minutes: int = 5,
        poll_interval: float = 1.0,
    ) -> None:
        self.symbols = symbols
        self.opening_minutes = opening_minutes
        self.poll_interval = poll_interval
        self.client = RESTClient(settings.MASSIVE_API_KEY)

        # per-symbol state
        # trades: dict[symbol, list[tuple(ts_seconds, price, size)]]
        self.trades: dict[str, list[tuple[float, float, float]]] = {
            s: [] for s in symbols
        }
        # minute buckets for resampling: dict[symbol, dict[minute_ts -> list[(price,size)]]]
        self.minute_buckets: dict[str, dict[int, list[tuple[float, float]]]] = {
            s: {} for s in symbols
        }
        # whether opening range computed
        self.opening_range_done: dict[str, bool] = {s: False for s in symbols}
        self.opening_range: dict[str, dict] = {s: {} for s in symbols}
        # whether breakout already signaled
        self.signaled: dict[str, bool] = {s: False for s in symbols}

    FloatInput = Union[str, float, int]

    def _now_minute(self, ts: float) -> int:
        # minute epoch (seconds rounded down to minute)
        return int(ts // 60 * 60)

    def _add_trade(
        self, symbol: str, ts: float, price: float, size: float = 0.0
    ) -> None:
        print(f"TRADE {symbol} {ts:.3f} price={price} size={size}")
        self.trades[symbol].append((ts, price, size))

        m = self._now_minute(ts)
        buckets = self.minute_buckets[symbol]
        buckets.setdefault(m, []).append((price, size))

    def _resample_minute_ohlcv(self, symbol: str, minute_ts: int) -> dict:
        items = self.minute_buckets[symbol].get(minute_ts, [])
        if not items:
            return {}
        prices = [p for p, _ in items]
        vols = [v for _, v in items]
        o = items[0][0]
        h = max(prices)
        l = min(prices)
        c = items[-1][0]
        v = sum(vols)
        return {"open": o, "high": h, "low": l, "close": c, "volume": v}

    def _fetch_trades(self, symbol: str):
        # Try to use REST client's trade endpoint if present
        try:
            if hasattr(self.client, "get_trades"):
                # many REST clients return a list of trade objects/dicts
                return self.client.get_trades(symbol)
            if hasattr(self.client, "get_recent_trades"):
                return self.client.get_recent_trades(symbol)
            # fallback to snapshot: create a synthetic trade from snapshot price
            if hasattr(self.client, "get_snapshot"):
                snap = self.client.get_snapshot(symbol)
                # try to extract a current price from snapshot
                price = None
                if getattr(snap, "last_trade", None):
                    last = getattr(snap, "last_trade")
                    price = getattr(last, "price", None) or getattr(last, "p", None)
                # try 'min' or 'day' price if present
                if price is None:
                    data = getattr(snap, "min", None) or getattr(snap, "day", None)
                    if data is not None:
                        price = getattr(data, "close", None) or getattr(
                            data, "open", None
                        )
                if price is not None:
                    return [
                        {
                            "price": price,
                            "size": getattr(snap, "volume", 0),
                            "ts": time.time(),
                        }
                    ]
        except Exception as e:
            logger.exception("Error fetching trades for %s: %s", symbol, e)
        return []

    def run(self) -> None:
        """Main polling loop. This is synchronous and uses `time.sleep` between polls."""
        start_ts = time.time()
        opening_window_end = start_ts + (self.opening_minutes * 60)
        print(
            f"OpeningRangeScanner starting for {self.symbols}, opening window ends at {opening_window_end}"
        )

        try:
            while True:
                now = time.time()
                for symbol in self.symbols:
                    # get trades (list or iterable)
                    trades = self._fetch_trades(symbol)
                    if not trades:
                        continue

                    # trades may be list of objects or dicts
                    for t in trades:
                        try:
                            if isinstance(t, dict):
                                raw_price = t.get("price")
                                if raw_price is None:
                                    raw_price = t.get("p")
                                if raw_price is None:
                                    continue
                                price = float(raw_price)

                                raw_size = t.get("size")
                                if raw_size is None:
                                    raw_size = t.get("s")
                                if raw_size is None:
                                    raw_size = 0
                                size = float(
                                    cast(OpeningRangeScanner.FloatInput, raw_size)
                                )

                                raw_ts = t.get("ts")
                                if raw_ts is None:
                                    raw_ts = time.time()
                                ts = float(raw_ts)
                            else:
                                # object with attributes
                                raw_price = getattr(t, "price", None)
                                if raw_price is None:
                                    raw_price = getattr(t, "p", None)
                                if raw_price is None:
                                    continue
                                price = float(raw_price)

                                raw_size = getattr(t, "size", None)
                                if raw_size is None:
                                    raw_size = getattr(t, "s", 0)
                                if raw_size is None:
                                    raw_size = 0
                                size = float(
                                    cast(OpeningRangeScanner.FloatInput, raw_size)
                                )

                                raw_ts = getattr(t, "ts", None)
                                if raw_ts is None:
                                    raw_ts = time.time()
                                ts = float(raw_ts)
                        except Exception:
                            continue

                        # print each trade
                        self._add_trade(symbol, ts, price, size)

                        # check if we need to compute opening range
                        if (
                            not self.opening_range_done[symbol]
                            and now >= opening_window_end
                        ):
                            # compute opening OHLC from minute buckets covering first N minutes
                            # collect minutes from start_ts to opening_window_end
                            start_min = self._now_minute(start_ts)
                            minutes = [
                                start_min + i * 60 for i in range(self.opening_minutes)
                            ]
                            all_prices = []
                            volumes = 0
                            for m in minutes:
                                ohlcv = self._resample_minute_ohlcv(symbol, m)
                                if ohlcv:
                                    all_prices.extend(
                                        [
                                            ohlcv["open"],
                                            ohlcv["high"],
                                            ohlcv["low"],
                                            ohlcv["close"],
                                        ]
                                    )
                                    volumes += ohlcv.get("volume", 0) or 0

                            if all_prices:
                                opening_high = max(all_prices)
                                opening_low = min(all_prices)
                                opening_open = all_prices[0]
                                self.opening_range_done[symbol] = True
                                self.opening_range[symbol] = {
                                    "open": opening_open,
                                    "high": opening_high,
                                    "low": opening_low,
                                    "volume": volumes,
                                }
                                print(
                                    f"Opening range for {symbol}: open={opening_open} high={opening_high} low={opening_low}"
                                )

                        # if opening computed, check breakout
                        if (
                            self.opening_range_done[symbol]
                            and not self.signaled[symbol]
                        ):
                            orng = self.opening_range[symbol]
                            if orng and price > orng.get("high", float("inf")):
                                # breakout!
                                print(
                                    f"OPENING BREAKOUT {symbol} price={price} > {orng['high']}"
                                )
                                # persist to DB
                                with Session(engine) as session:
                                    day_found = date.today()
                                    ts_int = int(time.time())
                                    add_opening_breakout(
                                        session=session,
                                        symbol=symbol,
                                        open=orng.get("open"),
                                        high=orng.get("high"),
                                        low=orng.get("low"),
                                        breakout_price=price,
                                        volume=size,
                                        day_found=day_found,
                                        ts=ts_int,
                                    )
                                self.signaled[symbol] = True

                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            print("OpeningRangeScanner stopped by user")


if __name__ == "__main__":
    print("Starting scanner...")
    gap_scanner = GapScanner()
    gap_scanner.refresh(threshold=50.0)  # 50% gap threshold
    # gap
    # opening_scanner = OpeningRangeScanner(
    #     symbols=["*"], opening_minutes=1, poll_interval=1.0
    # )
    # opening_scanner.run()
