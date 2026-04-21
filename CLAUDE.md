# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

30-day paper trading bot challenge. Bot executes up to 3 stock trades per trading day using Claude Opus 4.7 for decision-making, powered by Alpaca paper trading API. Goal: outperform S&P 500 buy-and-hold baseline over 30 days.

**Key constraint:** Market hours only (9:30–16:00 ET). Max 3 orders/day hard-capped.

## Architecture & Structure

```
trading-bot/
├── main.py                 # Daily orchestration (entry point)
├── config.py               # Environment, API keys, constants
├── agents/
│   └── trading_agent.py    # Claude Opus agent (decision logic)
├── broker/
│   └── alpaca.py           # Alpaca API wrapper (orders, positions, balance)
├── data/
│   └── market.py           # Market data fetcher (movers, news, technicals)
├── memory/
│   ├── lessons.md          # Cumulative lessons (prompt-cached, agent learns from)
│   ├── trades_log.md       # All executed trades + outcomes
│   └── session-summary-YYYY-MM-DD.md
├── reports/
│   └── day_XX.md           # Daily summaries (decisions, P&L, analysis)
├── benchmark.py            # SPY tracker (baseline comparison)
└── requirements.txt        # Python dependencies
```

## Key Design Decisions

### Language & Framework
- **Python** — finance standard, Alpaca SDK native
- **Claude Opus 4.7** — via Anthropic SDK with prompt caching for lessons.md
- **Alpaca API** — paper trading account + live market data

### Agent Architecture
- Agent reads: daily lessons file (cached), current portfolio state, top movers, sentiment
- Agent outputs: JSON with up to 3 trades + rationale
- Agent improves over 30 days by reading previous trade outcomes (lessons.md)

### Lessons Mechanism (Self-Teaching)
- Agent reads `lessons.md` at start of each day (prompt-cached for efficiency)
- After each trading day, append trade results + performance analysis to `lessons.md`
- This allows agent to learn from past mistakes without fine-tuning

### Constraints
- **Hard cap: 3 orders/day** — enforced in main.py before execution
- **Market hours only** — check market open/close times
- **Paper trading** — no real capital risk
- **Daily reset** — lessons file persists, but portfolio state resets if using paper account sandbox

## Setup & Environment

### Prerequisites
1. **Python 3.10+**
2. **Alpaca account** (paper trading) with API keys
3. **Claude API key** (already configured in environment)

### Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ALPACA_API_KEY=<your_key>
export ALPACA_SECRET_KEY=<your_secret>
export ALPACA_BASE_URL=https://paper-api.alpaca.markets  # Paper trading
export ANTHROPIC_API_KEY=<your_key>
```

### Get Alpaca API Keys
1. Go to https://app.alpaca.markets (create account if needed)
2. Settings → API Keys → Create New Key
3. Use paper trading base URL: `https://paper-api.alpaca.markets`
4. Export keys as environment variables (above)

## Development Workflow

### Before Implementation
1. Check `memory/session-summary-YYYY-MM-DD.md` for current blockers + next steps
2. Verify Alpaca API keys are set (test with a simple account balance call)

### When Adding Components
1. **New agent strategy** → update `agents/trading_agent.py`, test prompt in isolation first
2. **New data source** → add to `data/market.py`, validate output format before integration
3. **New trade logic** → implement in agent, test against mock data before live paper trading
4. **Lessons format** → append structured JSON/markdown to `memory/lessons.md`, agent must parse it correctly

### Daily Operations (Once Running)
```bash
python main.py  # Runs: market scan → agent decision → trade execution → log results → append lessons
```

### Testing Strategy
- Unit test broker wrapper (mock Alpaca responses)
- Unit test agent output parsing (JSON validation)
- Paper trading validation: run first day with agent disabled (manual trades only)
- Full integration: first trade with agent live on Day 1

## Key Technical Constraints

1. **Prompt Caching** — `lessons.md` will be cached by Anthropic SDK. Append-only operations only (no rewrites).
2. **Market Hours** — All trades must execute between 9:30–16:00 ET. Use `alpaca.py` to check market status before trading.
3. **Rate Limits** — Alpaca API has rate limits; batch requests where possible.
4. **State Management** — Paper trading account may reset; lessons file is persistent backup.

## Common Commands (Once Scaffolded)

```bash
python main.py                    # Run daily trading workflow
python -m pytest tests/           # Run unit tests
python benchmark.py               # Check SPY baseline vs bot P&L
```

## Blockers & Next Steps

**Current blocker:** Alpaca API keys needed before scaffolding can begin.

Once keys obtained:
1. Scaffold directory structure + `requirements.txt`
2. Implement Alpaca broker wrapper (`broker/alpaca.py`)
3. Implement market data fetcher (`data/market.py`)
4. Build trading agent (`agents/trading_agent.py`) with prompt caching
5. Implement lessons mechanism (append to `memory/lessons.md`)
6. Create daily report generator
7. Test Day 1 full workflow
8. Run 30-day challenge
