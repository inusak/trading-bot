"""Trading bot CLI — pure I/O. Reasoning lives in routines/trade_slot.md.

Subcommands:
  snapshot        Print JSON state (account, positions, market data, budget).
  submit-order    Submit one order via Alpaca. Writes to trades_log.md.
  append-lesson   Append EOD lesson to memory/lessons.md.
  append-report   Append slot block to reports/day_XX.md.
  count-orders    Print orders used today.
  slot-now        Print current slot based on ET time.
"""
import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

import config
from broker import alpaca
from data import market

ET = ZoneInfo("America/New_York")


def _now_et_iso() -> str:
    return datetime.now(ET).strftime("%Y-%m-%d %H:%M:%S")


def _slot_from_now() -> str:
    t = datetime.now(ET).time()
    if t < time(11, 30):
        return "open"
    if t < time(14, 30):
        return "midday"
    return "preclose"


def cmd_snapshot(_args):
    config.assert_env()
    orders_today = alpaca.get_orders_today()
    used = len(orders_today)
    remaining = max(0, config.MAX_ORDERS_PER_DAY - used)
    watchlist = market.get_watchlist_snapshot()
    out = {
        "now_et": _now_et_iso(),
        "slot": _slot_from_now(),
        "market_open": alpaca.is_market_open(),
        "orders_today_count": used,
        "remaining_budget": remaining,
        "orders_today": orders_today,
        "account": asdict(alpaca.get_account()),
        "positions": alpaca.get_positions(),
        "spy": market.get_spy_snapshot(),
        "watchlist": watchlist,
        "top_movers": market.get_top_movers(watchlist),
        "max_orders_per_day": config.MAX_ORDERS_PER_DAY,
        "max_position_pct": config.MAX_POSITION_PCT,
    }
    print(json.dumps(out, indent=2, default=str))


def cmd_submit_order(args):
    config.assert_env()
    orders_today = alpaca.get_orders_today()
    if len(orders_today) >= config.MAX_ORDERS_PER_DAY:
        print(json.dumps({"error": "budget_exhausted", "used": len(orders_today)}), file=sys.stderr)
        sys.exit(3)

    if args.dry_run:
        result = {
            "dry_run": True,
            "symbol": args.symbol,
            "side": args.side,
            "qty": args.qty,
            "order_type": args.type,
            "limit_price": args.limit_price,
        }
    else:
        result = alpaca.submit_order(
            symbol=args.symbol,
            side=args.side,
            qty=args.qty,
            order_type=args.type,
            limit_price=args.limit_price,
        )

    rationale = (args.rationale or "").replace("|", "/").replace("\n", " ")
    line = (
        f"| {_now_et_iso()} | {args.slot} | {args.symbol} | {args.side} | "
        f"{args.qty} | {args.type} | {args.limit_price or ''} | "
        f"{result.get('status', 'dry_run')} | {rationale} |\n"
    )
    with open(config.TRADES_LOG_FILE, "a") as f:
        f.write(line)

    print(json.dumps(result, indent=2, default=str))


def cmd_append_lesson(args):
    date = datetime.now(ET).strftime("%Y-%m-%d")
    block = (
        f"\n## Day {args.day} — {date}\n"
        f"- SPY delta today: {args.spy_delta:+.2f}%\n"
        f"- Cumulative vs SPY: {args.cumulative:+.2f}%\n"
        f"- Lesson: {args.text}\n"
    )
    with open(config.LESSONS_FILE, "a") as f:
        f.write(block)
    print(json.dumps({"appended": True, "day": args.day}))


def cmd_append_report(args):
    path = Path(config.REPORTS_DIR) / f"day_{args.day:02d}.md"
    date = datetime.now(ET).strftime("%Y-%m-%d")
    header = f"# Day {args.day} — {date}\n\n" if not path.exists() else ""
    body = f"\n## Slot: {args.slot} — {_now_et_iso()}\n{args.text}\n"
    with open(path, "a") as f:
        f.write(header + body)
    print(json.dumps({"appended": True, "path": str(path)}))


def cmd_count_orders(_args):
    orders = alpaca.get_orders_today()
    print(json.dumps({
        "used": len(orders),
        "remaining": max(0, config.MAX_ORDERS_PER_DAY - len(orders)),
        "orders": orders,
    }, indent=2, default=str))


def cmd_slot_now(_args):
    print(_slot_from_now())


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("snapshot").set_defaults(func=cmd_snapshot)

    s = sub.add_parser("submit-order")
    s.add_argument("--symbol", required=True)
    s.add_argument("--side", required=True, choices=["buy", "sell"])
    s.add_argument("--qty", required=True, type=float)
    s.add_argument("--type", required=True, choices=["limit", "market"])
    s.add_argument("--limit-price", type=float)
    s.add_argument("--slot", required=True, choices=sorted(config.SLOTS))
    s.add_argument("--rationale", default="")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(func=cmd_submit_order)

    s = sub.add_parser("append-lesson")
    s.add_argument("--day", required=True, type=int)
    s.add_argument("--spy-delta", required=True, type=float)
    s.add_argument("--cumulative", required=True, type=float)
    s.add_argument("--text", required=True)
    s.set_defaults(func=cmd_append_lesson)

    s = sub.add_parser("append-report")
    s.add_argument("--day", required=True, type=int)
    s.add_argument("--slot", required=True, choices=sorted(config.SLOTS))
    s.add_argument("--text", required=True)
    s.set_defaults(func=cmd_append_report)

    sub.add_parser("count-orders").set_defaults(func=cmd_count_orders)
    sub.add_parser("slot-now").set_defaults(func=cmd_slot_now)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
