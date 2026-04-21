# Routines — Claude Code scheduled agent

## Setup

Use Claude Code `/schedule` skill to create three cron triggers (US weekdays, ET):

| Slot | Cron (ET) | Prompt |
|---|---|---|
| open | `35 9 * * 1-5` | see `trade_slot.md` |
| midday | `30 12 * * 1-5` | see `trade_slot.md` |
| preclose | `45 15 * * 1-5` | see `trade_slot.md` |

Each trigger's prompt: paste contents of `trade_slot.md`. Agent infers current slot via `bot.py slot-now` — same prompt works for all three.

## First-time init

Before scheduling, run once manually during market hours:

```bash
source venv/bin/activate
python benchmark.py --init          # saves Day 0 baseline
python bot.py snapshot              # verify state fetch
```

## Manual slot run (for debugging)

```bash
source venv/bin/activate
python bot.py slot-now              # prints current slot
python bot.py snapshot              # JSON state
python bot.py count-orders          # budget check
```

## Safety first run

Temporarily set `MAX_ORDERS_PER_DAY = 1` in `config.py`, run one live slot, verify order lands in Alpaca dashboard, revert to 3.
