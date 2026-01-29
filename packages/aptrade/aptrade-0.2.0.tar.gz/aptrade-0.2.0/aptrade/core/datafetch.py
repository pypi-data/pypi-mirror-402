import asyncio
import random
import datetime

try:
    import httpx
except Exception:  # httpx may not be installed in minimal env
    httpx = None  # type: ignore


async def fetch_real(api_url: str, timeout: float = 10.0) -> float:
    """Fetch a numeric value from a real HTTP API (expects a simple JSON {value: number})."""
    if httpx is None:
        raise RuntimeError("httpx not installed")
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(api_url)
        r.raise_for_status()
        data = r.json()
        # adapt according to real API shape
        return float(data.get("value", data))


async def fetch_simulator(min_v: float = 0.0, max_v: float = 1.0) -> float:
    """Simulate API by returning a random float."""
    # simulate network jitter
    await asyncio.sleep(random.uniform(0.01, 0.1))
    return random.uniform(min_v, max_v)


def process_value(value: float, history: list[float], window: int = 5) -> dict:
    """Simple processing: push into history and compute simple moving average."""
    history.append(value)
    if len(history) > 1000:  # cap history to avoid unbounded growth
        del history[: len(history) - 1000]
    window_vals = history[-window:]
    sma = sum(window_vals) / len(window_vals)
    return {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "value": value,
        "sma": sma,
    }
