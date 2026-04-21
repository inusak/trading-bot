# Routines — Claude Code scheduled remote agents

## Prerequisites

1. **Push repo to GitHub** — remote triggers clone via git URL.
   ```bash
   gh repo create trading-bot --private --source=. --push
   ```
2. **Alpaca paper account** — API key + secret from https://app.alpaca.markets
3. **Discord webhook (optional)** — webhook URL for status pings

## Trigger setup in Claude Desktop

Create 3 scheduled triggers. All three use the **same prompt** (`routines/trade_slot.md`). Agent detects slot via `bot.py slot-now`.

### Schedules (UTC, weekdays Mon–Fri)

During US daylight saving (EDT, ~Mar–Nov) — currently active:

| Slot | ET | UTC | Cron |
|---|---|---|---|
| open | 09:35 | 13:35 | `35 13 * * 1-5` |
| midday | 12:30 | 16:30 | `30 16 * * 1-5` |
| preclose | 15:45 | 19:45 | `45 19 * * 1-5` |

After DST ends (EST, ~Nov–Mar): shift all cron hours +1.

### Common trigger config (all 3)

- **Repo**: `https://github.com/<your-org>/trading-bot`
- **Model**: `claude-opus-4-7` (better trading judgment than Sonnet)
- **Allowed tools**: `Bash`, `Read`, `Write`, `Edit`, `Glob`, `Grep`
- **Prompt**: paste full contents of `routines/trade_slot.md`

### Environment variables per trigger

Set in trigger's env config (not in repo). Required:

| Var | Value |
|---|---|
| `ALPACA_API_KEY` | your paper key (e.g. `PK...`) |
| `ALPACA_SECRET_KEY` | your paper secret |

Optional:

| Var | Value |
|---|---|
| `ALPACA_BASE_URL` | defaults to `https://paper-api.alpaca.markets` |
| `DISCORD_WEBHOOK_URL` | enables Step 6 status pings |

### Git push permissions

Triggers push state commits (Step 7) so lessons/trades/reports persist across runs. Grant push access via:
- Deploy key with write, OR
- Fine-grained PAT scoped to this repo (`contents: write`)

Set as env var `GIT_PUSH_TOKEN` OR configure git credential helper in trigger setup.

## Safety first run

Before enabling all 3 triggers:

1. Manually init baseline (local):
   ```bash
   source venv/bin/activate
   python benchmark.py --init
   git add memory/benchmark_state.json && git commit -m "seed baseline" && git push
   ```
2. Temporarily set `MAX_ORDERS_PER_DAY = 1` in `config.py`, push.
3. Enable only the `open` trigger. Wait for next market open, verify:
   - Order lands in Alpaca dashboard
   - Discord ping arrives
   - Repo has new commit with updated `memory/trades_log.md` + `reports/day_01.md`
4. Revert `MAX_ORDERS_PER_DAY = 3`, push, enable midday + preclose.

## Manual local testing

```bash
source venv/bin/activate
python bot.py slot-now              # current slot by ET time
python bot.py snapshot              # JSON state
python bot.py count-orders          # budget check
python bot.py notify --text "test"  # webhook sanity
```

## Troubleshooting

- **403 from Discord**: verify webhook URL and that User-Agent header is set (already handled in `bot.py`).
- **Alpaca auth fail**: confirm env vars in trigger config, not just local `.env`.
- **Duplicate orders**: Alpaca's `get_orders_today()` is source of truth. If duplicates appear, check clock skew.
- **State not persisting**: Step 7 must push. Verify trigger has git push creds.
