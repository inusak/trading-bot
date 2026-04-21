"""SPY baseline tracker. Run daily to compare bot equity vs SPY buy-and-hold."""
import argparse
import json
from dataclasses import asdict
from pathlib import Path

import config
from broker import alpaca
from data import market

STATE_FILE = Path(config.MEMORY_DIR) / "benchmark_state.json"


def init_baseline():
    spy = market.get_spy_snapshot()
    account = asdict(alpaca.get_account())
    state = {
        "day0_equity": account["equity"],
        "day0_spy_close": spy["last"],
    }
    STATE_FILE.write_text(json.dumps(state, indent=2))
    print(f"Baseline saved: equity ${state['day0_equity']:,.2f}  SPY ${state['day0_spy_close']}")


def status():
    if not STATE_FILE.exists():
        print("No baseline. Run: python benchmark.py --init")
        return
    state = json.loads(STATE_FILE.read_text())
    account = asdict(alpaca.get_account())
    spy = market.get_spy_snapshot()
    bot_return = (account["equity"] - state["day0_equity"]) / state["day0_equity"] * 100
    spy_return = (spy["last"] - state["day0_spy_close"]) / state["day0_spy_close"] * 100
    delta = bot_return - spy_return
    print(f"Bot: {bot_return:+.2f}%   SPY: {spy_return:+.2f}%   Delta: {delta:+.2f}%")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--init", action="store_true", help="set Day 0 baseline")
    args = p.parse_args()
    if args.init:
        init_baseline()
    else:
        status()


if __name__ == "__main__":
    main()
