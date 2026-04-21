Session Summary — 2026-04-21

  Session date: 2026-04-21
  Working directory: /Users/nilanka/ClaudeProjects/Projects/trading-bot
  Session focus: Scaffold scheduled agentic trading bot — Alpaca paper + Claude Opus 4.7

  Project Overview

  30-day paper trading challenge. Bot runs 3 slots per trading day (9:35 / 12:30 / 15:45 ET) with hard cap of 3 orders/day total. Claude Opus 4.7 agent decides trades from watchlist, lessons.md provides self-learning across sessions. Goal: outperform SPY over 30 days.

  Key Decisions

  - Scheduler-agnostic CLI (`python main.py --slot open|midday|preclose`) — any scheduler (openclaw, cron, launchd, GH Actions) can drive same entry point
  - Three daily slots instead of single daily run — agent reacts to intraday moves, preclose slot handles risk-off
  - Order budget enforced via Alpaca `get_orders_today()` not local state — authoritative, survives restarts
  - Prompt caching on system prompt + lessons.md (ephemeral `cache_control`) — append-only lessons preserve cache hits
  - LLM judgment + Python guardrails, not mechanical rules — agent picks from 20-ticker watchlist, Python enforces 3-order cap, 15% position cap, JSON schema validation

  Tech Stack & Architecture

  Language: Python 3.14
  Framework/APIs: alpaca-py (paper trading + market data), anthropic SDK (Claude Opus 4.7 w/ prompt caching), pandas/numpy (RSI + SMA), pytest
  Key structure:
  trading-bot/
  ├── main.py                    # CLI orchestration per slot
  ├── config.py                  # env, constants, watchlist
  ├── broker/alpaca.py           # clock, account, positions, orders_today, submit_order
  ├── data/market.py             # bars, RSI, SPY, watchlist snapshot, movers
  ├── agents/
  │   ├── prompts.py             # system prompt + user payload builder
  │   └── trading_agent.py       # Anthropic client, JSON parse + validate
  ├── memory/
  │   ├── lessons.md             # seeded Day-0 priors, append-only
  │   └── trades_log.md          # executed orders table
  ├── reports/                   # daily markdown summaries
  ├── benchmark.py               # SPY baseline tracker
  └── tests/                     # test_agent_parse + test_broker (11 tests)

  Plan Details

  Plan: /Users/nilanka/.claude/plans/i-want-to-create-glimmering-puzzle.md
  Status: Approved + fully implemented. Scaffolding complete, 11/11 unit tests pass, Alpaca broker verified live (paper account $100k, market open, SPY $709.20).

  Files & Changes

  - Created: requirements.txt, .env, .env.example, .gitignore, config.py, main.py, benchmark.py
  - Created: broker/alpaca.py, data/market.py
  - Created: agents/prompts.py, agents/trading_agent.py
  - Created: memory/lessons.md (seeded), memory/trades_log.md (header)
  - Created: tests/test_broker.py, tests/test_agent_parse.py
  - Created: reports/.gitkeep
  - venv created, deps installed
  Memory: lessons.md, trades_log.md, session-summary-2026-04-21.md

  Next Steps

  - Obtain Anthropic API key from console.anthropic.com and update .env (ANTHROPIC_API_KEY still placeholder)
  - Run full dry-run: `python main.py --slot open --dry-run` — exercises agent JSON path without submitting orders
  - Set SPY baseline: `python benchmark.py --init`
  - Wire scheduler (openclaw) to call main.py at 09:35 / 12:30 / 15:45 ET weekdays
  - Day-1 live run with safety cap temporarily set to MAX_ORDERS_PER_DAY=1 to validate end-to-end submission
  - Revert cap to 3, start 30-day challenge

  Resources & Blockers

  Resources available:
  - Alpaca paper API keys — exported in .env, verified working (account balance $100k)
  - Alpaca paper account — $100k starting capital, market currently open

  Blockers: Anthropic API key missing — full dry-run + live trading blocked until user generates key at https://console.anthropic.com/settings/keys

  Open questions:
  - Scheduler choice (openclaw vs launchd vs GH Actions) — user mentioned openclaw, wiring deferred
  - Start date for 30-day challenge — deferred until scaffolding validated
  - Watchlist scope — current 20 large-cap; user may want different universe
  - SPY RSI14 returning 97 in initial probe — may reflect limited bar history in free Alpaca data tier; validate with longer window if signals look off
