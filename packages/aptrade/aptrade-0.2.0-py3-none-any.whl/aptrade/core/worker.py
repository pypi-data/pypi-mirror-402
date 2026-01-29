import os
import asyncio
from typing import Optional, Callable, Awaitable
from aptrade.core import datafetch as core


# simple shared datastore for latest processed result
class DataStore:
    def __init__(self):
        self._lock = asyncio.Lock()
        self.latest: Optional[dict] = None
        self.history: list[float] = []

    async def update(self, item: dict):
        async with self._lock:
            self.latest = item

    async def get_latest(self) -> Optional[dict]:
        async with self._lock:
            return self.latest


async def sampler_loop(
    datastore: DataStore,
    fetcher: "Callable[[], Awaitable[float]]",
    interval: int = 60,
    window: int = 5,
):
    """Continuously fetch, process and store latest result every `interval` seconds."""
    # align to wall clock minute if interval is 60
    while True:
        try:
            value = await fetcher()
            processed = core.process_value(value, datastore.history, window=window)
            print("sampler fetched and processed:", processed)
            await datastore.update(processed)
            # You can also persist, push to DB, or send to other services here.
        except Exception as e:
            # keep loop alive; in real app use structured logging
            print("sampler error:", e)
        await asyncio.sleep(interval)


def get_fetcher_from_env():
    use_sim = os.getenv("USE_SIMULATOR", "true").lower() in ("1", "true", "yes")
    if use_sim:
        return lambda: core.fetch_simulator(0.0, 100.0)
    api_url = os.getenv("REMOTE_API_URL", "https://example.com/value")
    return lambda: core.fetch_real(api_url)


async def run_worker_forever(interval: int = 5):
    ds = DataStore()
    fetcher = get_fetcher_from_env()
    # start sampler
    print("Starting sampler loop with interval", interval)
    await sampler_loop(ds, fetcher, interval=interval)


if __name__ == "__main__":
    # For development, shorten the interval with env var
    interval = int(os.getenv("INTERVAL_SEC", "5"))
    asyncio.run(run_worker_forever(interval=interval))
