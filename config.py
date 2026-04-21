"""Central config: env vars, constants, watchlist."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent
MEMORY_DIR = ROOT / "memory"
REPORTS_DIR = ROOT / "reports"
LESSONS_FILE = MEMORY_DIR / "lessons.md"
TRADES_LOG_FILE = MEMORY_DIR / "trades_log.md"

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
ALPACA_PAPER = "paper" in ALPACA_BASE_URL

MAX_ORDERS_PER_DAY = 3
MAX_POSITION_PCT = 0.15

SLOTS = {"open", "midday", "preclose"}

WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
    "AMD", "NFLX", "CRM", "ADBE", "AVGO", "QCOM", "INTC",
    "JPM", "V", "MA", "UNH", "JNJ", "WMT",
]
SPY_SYMBOL = "SPY"


def assert_env():
    missing = [k for k, v in {
        "ALPACA_API_KEY": ALPACA_API_KEY,
        "ALPACA_SECRET_KEY": ALPACA_SECRET_KEY,
    }.items() if not v]
    if missing:
        raise RuntimeError(f"Missing env vars: {missing}")
