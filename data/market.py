"""Market data fetcher: bars, RSI, SPY snapshot, movers."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame

import config

ET = ZoneInfo("America/New_York")


def _data_client() -> StockHistoricalDataClient:
    config.assert_env()
    return StockHistoricalDataClient(
        api_key=config.ALPACA_API_KEY,
        secret_key=config.ALPACA_SECRET_KEY,
    )


def get_bars(symbol: str, days: int = 30) -> pd.DataFrame:
    end = datetime.now(ET) - timedelta(minutes=20)
    start = end - timedelta(days=days)
    req = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
    )
    bars = _data_client().get_stock_bars(req).df
    if bars.empty:
        return bars
    if "symbol" in bars.index.names:
        bars = bars.xs(symbol, level="symbol")
    return bars


def compute_rsi(closes: pd.Series, period: int = 14) -> float | None:
    if len(closes) < period + 1:
        return None
    delta = closes.diff().dropna()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)
    val = rsi.iloc[-1]
    return None if pd.isna(val) else float(val)


def get_latest_quote(symbol: str) -> dict | None:
    req = StockLatestQuoteRequest(symbol_or_symbols=symbol)
    q = _data_client().get_stock_latest_quote(req).get(symbol)
    if not q:
        return None
    return {
        "bid": float(q.bid_price) if q.bid_price else None,
        "ask": float(q.ask_price) if q.ask_price else None,
        "ts": q.timestamp.isoformat() if q.timestamp else None,
    }


def get_ticker_snapshot(symbol: str) -> dict:
    bars = get_bars(symbol, days=30)
    if bars.empty:
        return {"symbol": symbol, "error": "no bars"}
    closes = bars["close"]
    last = float(closes.iloc[-1])
    prev = float(closes.iloc[-2]) if len(closes) >= 2 else last
    day_change_pct = (last - prev) / prev * 100 if prev else 0.0
    sma20 = float(closes.tail(20).mean()) if len(closes) >= 20 else None
    return {
        "symbol": symbol,
        "last": last,
        "prev_close": prev,
        "day_change_pct": round(day_change_pct, 2),
        "sma20": round(sma20, 2) if sma20 else None,
        "rsi14": round(compute_rsi(closes), 1) if compute_rsi(closes) else None,
        "volume": int(bars["volume"].iloc[-1]),
    }


def get_watchlist_snapshot() -> list[dict]:
    out = []
    for sym in config.WATCHLIST:
        try:
            out.append(get_ticker_snapshot(sym))
        except Exception as e:
            out.append({"symbol": sym, "error": str(e)})
    return out


def get_spy_snapshot() -> dict:
    return get_ticker_snapshot(config.SPY_SYMBOL)


def get_top_movers(snapshots: list[dict], n: int = 5) -> dict:
    valid = [s for s in snapshots if "day_change_pct" in s]
    gainers = sorted(valid, key=lambda s: s["day_change_pct"], reverse=True)[:n]
    losers = sorted(valid, key=lambda s: s["day_change_pct"])[:n]
    return {"gainers": gainers, "losers": losers}
