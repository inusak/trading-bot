"""Alpaca paper trading wrapper."""
from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    LimitOrderRequest,
    MarketOrderRequest,
    GetOrdersRequest,
)
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus

import config

ET = ZoneInfo("America/New_York")


def _client() -> TradingClient:
    config.assert_env()
    return TradingClient(
        api_key=config.ALPACA_API_KEY,
        secret_key=config.ALPACA_SECRET_KEY,
        paper=config.ALPACA_PAPER,
    )


@dataclass
class AccountSnapshot:
    cash: float
    equity: float
    buying_power: float
    portfolio_value: float


def get_account() -> AccountSnapshot:
    a = _client().get_account()
    return AccountSnapshot(
        cash=float(a.cash),
        equity=float(a.equity),
        buying_power=float(a.buying_power),
        portfolio_value=float(a.portfolio_value),
    )


def is_market_open() -> bool:
    return _client().get_clock().is_open


def get_positions() -> list[dict]:
    return [
        {
            "symbol": p.symbol,
            "qty": float(p.qty),
            "avg_entry_price": float(p.avg_entry_price),
            "market_value": float(p.market_value),
            "unrealized_pl": float(p.unrealized_pl),
            "unrealized_plpc": float(p.unrealized_plpc),
            "current_price": float(p.current_price),
        }
        for p in _client().get_all_positions()
    ]


def get_orders_today() -> list[dict]:
    """Authoritative daily order count — queries Alpaca for today ET midnight onward."""
    now_et = datetime.now(ET)
    start = datetime.combine(now_et.date(), time.min, tzinfo=ET)
    req = GetOrdersRequest(status=QueryOrderStatus.ALL, after=start)
    orders = _client().get_orders(filter=req)
    return [
        {
            "id": str(o.id),
            "symbol": o.symbol,
            "side": o.side.value,
            "qty": float(o.qty) if o.qty else None,
            "status": o.status.value,
            "submitted_at": o.submitted_at.isoformat() if o.submitted_at else None,
        }
        for o in orders
        if o.status.value not in ("canceled", "rejected", "expired")
    ]


def submit_order(
    symbol: str,
    side: str,
    qty: float,
    order_type: str = "limit",
    limit_price: float | None = None,
) -> dict:
    side_enum = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
    if order_type == "limit":
        if limit_price is None:
            raise ValueError("limit_price required for limit orders")
        req = LimitOrderRequest(
            symbol=symbol,
            qty=qty,
            side=side_enum,
            time_in_force=TimeInForce.DAY,
            limit_price=limit_price,
        )
    else:
        req = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=side_enum,
            time_in_force=TimeInForce.DAY,
        )
    o = _client().submit_order(req)
    return {
        "id": str(o.id),
        "symbol": o.symbol,
        "side": o.side.value,
        "qty": float(o.qty) if o.qty else qty,
        "status": o.status.value,
        "limit_price": limit_price,
    }
