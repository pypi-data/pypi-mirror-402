import logging
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
from typing import Any, Dict, List
import json
import time
from datetime import datetime
from pathlib import Path
from io import StringIO

TMP_DIR = Path("./tmp")
TMP_DIR.mkdir(exist_ok=True)
logger = logging.getLogger(__name__)


class BCException(Exception):
    pass


CHANGE_RE = re.compile(
    r"(?P<abs>[-+]?[0-9]*\.?[0-9]+)\s*\(?\s*(?P<pct>[-+]?[0-9]*\.?[0-9]+)%?\s*\)?"
)

BASE_URL = "https://trade-ideas.com/TIPro/controllers/top_list_data_feed.php"

DEFAULT_PARAMS = {
    "form": "1",
    "sort": "MaxFCP",
    "MinPrice": "0.5",
    "MinRV": "0.5",
    "MinTV": "200",
    "MinVol5D": "1000",
    "X_NYSE": "on",
    "X_ARCA": "on",
    "X_AMEX": "on",
    "XN": "on",
    "EntireUniverse": "2",
    "SL_1_5": "on",
    "WN": "Biggest Gainers (%)",
    "show0": "D_Symbol",
    "show1": "Price",
    "show2": "FCD",
    "show3": "FCP",
    "show4": "TV",
    "show5": "RD",
    "show6": "",
    "col_ver": "1",
    "hist": "1",
    # "exact_time" will be set dynamically below
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Accept": "*/*",
    "Referer": "https://trade-ideas.com/TIPro/marketscope360/",
    "Origin": "https://trade-ideas.com",
}


def parse_top_list(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    print(soup.prettify())
    container = soup.find(id="stock-ticker-biggest-gainers")
    if not container:
        return []

    rows = container.select(".top-list-body-row")
    out = []
    for r in rows:
        symbol_el = r.select_one(
            ".symbol-plus-symbol-span-positive, .symbol-plus-symbol-span-negative, .symbol-plus-symbol-span"
        )
        price_el = r.select_one(".symbol-plus-price-span")
        change_el = r.select_one(
            ".symbol-plus-change-span-positive, .symbol-plus-change-span-negative, .symbol-plus-change-span"
        )
        logo_el = r.select_one(".symbol-plus-logo")
        logo = logo_el.get("src") if (logo_el and logo_el.get("src")) else None

        symbol = symbol_el.get_text(strip=True) if symbol_el else None
        price = None
        try:
            price = float(price_el.get_text(strip=True)) if price_el else None
        except Exception:
            price = None

        raw_change = change_el.get_text(strip=True) if change_el else ""
        abs_change = None
        pct_change = None
        m = CHANGE_RE.search(raw_change.replace(" ", ""))
        if m:
            try:
                abs_change = float(m.group("abs"))
            except Exception:
                abs_change = None
            try:
                pct_change = float(m.group("pct"))
            except Exception:
                pct_change = None

        out.append(
            {
                "symbol": symbol,
                "price": price,
                "abs_change": abs_change,
                "pct_change": pct_change,
                "logo": logo,
                "raw_change": raw_change,
            }
        )
    return out


PAGEURL = "https://trade-ideas.com/"


def create_bc_session(config_obj: dict, do_login=True):
    """
    Create and return a web session, optionally logging into Barchart with the supplied
    credentials.

    Args:
        config_obj: dict containing Barchart credentials, with keys `barchart_username`
            and `barchart_password`
        do_login: if True, authenticate session with Barchart credentials

    Returns:
        A requests.Session instance

    Raises:
        Exception: if credentials are invalid
    """

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    if do_login is True and (
        "barchart_username" not in config_obj or "barchart_password" not in config_obj
    ):
        raise BCException("Missing credentials")

    if do_login:
        # GET the login page, scrape to get CSRF token
        resp = session.get(PAGEURL + "login")
        soup = BeautifulSoup(resp.text, "html.parser")
        tag = soup.find(type="hidden")
        csrf_token = tag.attrs["value"]
        logger.info(
            f"GET {PAGEURL + 'login'}, status: {resp.status_code}, "
            f"CSRF token: {csrf_token}"
        )

        # login to site with a POST
        payload = {
            "email": config_obj["barchart_username"],
            "password": config_obj["barchart_password"],
            "_token": csrf_token,
        }
        resp = session.post(PAGEURL + "login", data=payload)
        logger.info(f"POST {PAGEURL + 'login'}, status: {resp.status_code}")
        if resp.url == PAGEURL + "login":
            raise BCException("Invalid credentials")

    return session


def build_params_for_time(ts: int | None = None):
    # exact_time is epoch seconds — page used 1762873200 in your example.
    # Use provided ts or current time aligned to minute.
    if ts is None:
        now = int(time.time())
        ts = now - (now % 60)
    p = DEFAULT_PARAMS.copy()
    # p["exact_time"] = str(ts)
    # Print the exact time human readable
    human_time = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    print(f"Building params for exact_time={ts} ({human_time} UTC)")

    return p


# column mapping based on request params / observed payload
COLS = [
    "symbol",  # 0
    "price",  # 1
    "abs_change",  # 2 (absolute change)
    "pct_change",  # 3 (percent change)
    "volume",  # 4 (TV)
    "score",  # 5 (some score / metric)
    "time_str",  # 6 (time like "14:14:18")
    "rank",  # 7 (position / bucket)
    "exchange",  # 8
    "datetime_str",  # 9 (human datetime)
    "epoch",  # 10 (epoch seconds as string)
]


def parse_ti_top_list(path: str | Path = "./tmp/ti_top_list.json") -> pd.DataFrame:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    # data is a list-of-lists
    df = pd.DataFrame(data)

    # assign column names if width matches expected
    if df.shape[1] == len(COLS):
        df.columns = COLS
    else:
        # defensive: give generic names if structure differs
        df.columns = [f"c{i}" for i in range(df.shape[1])]

    # convert numeric columns
    for col in ("price", "abs_change", "pct_change", "score"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").astype("Int64")

    if "rank" in df.columns:
        df["rank"] = pd.to_numeric(df["rank"], errors="coerce").astype("Int64")

    # epoch -> timezone-aware datetime (UTC)
    if "epoch" in df.columns:
        df["epoch"] = pd.to_numeric(df["epoch"], errors="coerce").astype("Int64")
        df["datetime_utc"] = pd.to_datetime(
            df["epoch"].astype("float"), unit="s", utc=True
        )

    # parse provided datetime_str if you prefer (may be local)
    if "datetime_str" in df.columns:
        df["datetime_parsed"] = pd.to_datetime(df["datetime_str"], errors="coerce")

    # optional: compute pct as 0-1
    if "pct_change" in df.columns:
        df["pct_change_frac"] = df["pct_change"] / 100.0

    # df.sort_values(by="pct_change", ascending=False, inplace=True)
    df.to_csv(TMP_DIR / "ti_top_list_parsed.csv", index=False)
    return df


def fetch_top_list(
    session: requests.Session,
    params: dict | None = None,
    save_debug: bool = True,
    timeout: int = 20,
):
    s = session
    s.headers.update(HEADERS)
    params = params or build_params_for_time()
    resp = s.get(BASE_URL, params=params, timeout=timeout)
    # # save raw response for debugging
    # TMP_DIR.mkdir(exist_ok=True)
    # raw_path = TMP_DIR / "ti_top_list_raw.txt"
    # raw_path.write_text(resp.text, encoding="utf-8")
    # print(f"Saved raw response to {raw_path} (status {resp.status_code})")

    # try parse as JSON
    try:
        # save JSON
        # (TMP_DIR / "ti_top_list.json").write_text(json.dumps(data, default=str), encoding="utf-8")
        # print("Parsed response as JSON")
        df = parse_ti_top_list(path=TMP_DIR / "ti_top_list.json")
        # print(df)
        # print(df.columns)
        # If JSON contains rows under a key, normalize
        # rows = None
        # if isinstance(data, dict):
        #     for key in ("data", "rows", "results", "items"):
        #         if key in data and isinstance(data[key], list):
        #             rows = data[key]
        #             break
        #     if rows is None and isinstance(data.get("data"), dict):
        #         for key in ("rows", "results", "items"):
        #             if key in data["data"]:
        #                 rows = data["data"][key]
        #                 break
        # elif isinstance(data, list):
        #     rows = data

        # if rows is None:
        #     print("No obvious rows array in JSON — inspect tmp/ti_top_list.json")
        #     return None

        # print(rows[:5])
        # df = pd.json_normalize(rows)

        return df

    except ValueError:
        # not JSON - try parsing as HTML table(s)
        print("Response is not JSON, trying to parse HTML tables")
        try:
            tables = pd.read_html(StringIO(resp.text))
            if tables:
                df = tables[0]
                (TMP_DIR / "ti_top_list_table.csv").write_text(
                    df.to_csv(index=False), encoding="utf-8"
                )
                print("Parsed HTML table and saved to tmp/ti_top_list_table.csv")
                return df
        except Exception:
            pass

        # fallback: try reading as CSV/TSV
        try:
            df = pd.read_csv(StringIO(resp.text))
            (TMP_DIR / "ti_top_list_csv.csv").write_text(
                df.to_csv(index=False), encoding="utf-8"
            )
            print("Parsed response as CSV")
            return df
        except Exception as e:
            print("Failed to parse response as JSON/HTML/CSV:", e)
            return pd.DataFrame()


def update_stocks_play(
    df: pd.DataFrame, storage_path: Path = TMP_DIR / "stocks_play.csv"
) -> pd.DataFrame:
    """
    Filter rows with pct_change > 100, add them to a persistent StocksPlayDF (CSV).
    Print notification for symbols not already present.
    Returns the updated StocksPlayDF as a DataFrame.
    """
    if "pct_change" not in df.columns:
        raise ValueError("Input DataFrame must contain 'pct_change' column")

    # select stocks with more than 100% pct_change
    candidates = df.loc[df["pct_change"] > 100].copy()
    if candidates.empty:
        return (
            pd.read_csv(storage_path)
            if storage_path.exists()
            else pd.DataFrame(
                columns=["symbol", "price", "pct_change", "datetime_utc", "epoch"]
            )
        )

    # load existing StocksPlayDF or create empty
    if storage_path.exists():
        stocks_df = pd.read_csv(storage_path)
    else:
        stocks_df = pd.DataFrame(
            columns=["symbol", "price", "pct_change", "datetime_utc", "epoch"]
        )

    # ensure symbol column exists
    if "symbol" not in stocks_df.columns:
        stocks_df["symbol"] = []
    for _, row in candidates.iterrows():
        sym = str(row.get("symbol"))
        price = row.get("price")
        pct = row.get("pct_change")
        epoch = row.get("epoch", None)
        datetime_utc = row.get("datetime_utc", row.get("datetime_str", None))

    if sym not in stocks_df["symbol"].values:
        # notify and append
        print(f"New stock: {sym} pct_change={pct} price={price}")
        stocks_df = pd.concat(
            [
                stocks_df,
                pd.DataFrame(
                    [
                        {
                            "symbol": sym,
                            "price": price,
                            "pct_change": pct,
                            "datetime_utc": datetime_utc,
                            "epoch": epoch,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
    else:
        # update existing entry if newer (by epoch) or pct changed
        match_idx = stocks_df.index[stocks_df["symbol"] == sym]
        if len(match_idx) > 0:
            i = match_idx[0]
            try:
                existing_epoch = (
                    int(stocks_df.at[i, "epoch"])
                    if stocks_df.at[i, "epoch"] not in (None, "")
                    else None
                )
                new_epoch = int(epoch) if epoch not in (None, "") else None
            except Exception:
                existing_epoch = None
                new_epoch = None

            if new_epoch and (existing_epoch is None or new_epoch > existing_epoch):
                stocks_df.at[i, "price"] = price
                stocks_df.at[i, "pct_change"] = pct
                stocks_df.at[i, "datetime_utc"] = datetime_utc
                stocks_df.at[i, "epoch"] = epoch

    # persist
    TMP_DIR.mkdir(exist_ok=True)
    stocks_df.to_csv(storage_path, index=False)
    return stocks_df


def run(session: requests.Session):
    while True:
        now = datetime.now()
        if now.second == 0:
            df = fetch_top_list(session=session)

            if df is not None:
                updated_df = update_stocks_play(df)
                print(f"Updated stocks in play, total now: {len(updated_df)}")
                try:
                    print(updated_df)
                except Exception:
                    pass
            else:
                print("No data fetched from Trade Ideas")
            # Wait until the next minute to avoid duplicate runs
            time.sleep(1)
            while datetime.now().second == 0:
                time.sleep(1)
        else:
            time.sleep(1)


def single_run(session: requests.Session):
    df = fetch_top_list(session=session)

    if df is not None:
        updated_df = update_stocks_play(df)
        print(f"Updated stocks in play, total now: {len(updated_df)}")
        try:
            print(updated_df)
        except Exception:
            pass
    else:
        print("No data fetched from Trade Ideas")


if __name__ == "__main__":
    print("Starting scanner...")
    logging.basicConfig(level=logging.INFO)
    session = create_bc_session(
        config_obj=dict(
            barchart_username="marcelohmotta@hotmail.com",
            barchart_password="Matheus81*",
        )
    )

    run(session)
# sgle_run(session)
