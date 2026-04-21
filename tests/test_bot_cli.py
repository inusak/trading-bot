"""bot.py CLI subcommand tests."""
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).parent.parent


def _run_cli(*args):
    """Run bot.py as subprocess. For tests that need real CLI wiring."""
    return subprocess.run(
        [sys.executable, str(ROOT / "bot.py"), *args],
        capture_output=True, text=True, cwd=ROOT,
    )


def test_slot_now_returns_valid_slot():
    r = _run_cli("slot-now")
    assert r.returncode == 0
    assert r.stdout.strip() in {"open", "midday", "preclose"}


@patch("broker.alpaca._client")
def test_count_orders_with_mock(mock_client):
    from bot import cmd_count_orders
    import argparse
    client = MagicMock()
    mock_client.return_value = client
    client.get_orders.return_value = []

    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cmd_count_orders(argparse.Namespace())
    data = json.loads(buf.getvalue())
    assert data["used"] == 0
    assert data["remaining"] == 3


@patch("broker.alpaca._client")
def test_submit_order_dry_run_writes_log(mock_client, tmp_path, monkeypatch):
    import config
    import bot

    monkeypatch.setattr(config, "TRADES_LOG_FILE", tmp_path / "trades_log.md")
    config.TRADES_LOG_FILE.write_text("| ts | slot | symbol | side | qty | type | limit | status | rationale |\n")

    client = MagicMock()
    mock_client.return_value = client
    client.get_orders.return_value = []

    import argparse
    args = argparse.Namespace(
        symbol="AAPL", side="buy", qty=5, type="limit", limit_price=175.0,
        slot="open", rationale="test", dry_run=True,
    )
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        bot.cmd_submit_order(args)
    out = json.loads(buf.getvalue())
    assert out["dry_run"] is True
    assert out["symbol"] == "AAPL"
    assert "AAPL" in config.TRADES_LOG_FILE.read_text()


def test_notify_skips_without_webhook(monkeypatch, capsys):
    import bot, config
    monkeypatch.setattr(config, "DISCORD_WEBHOOK_URL", None)
    import argparse
    bot.cmd_notify(argparse.Namespace(text="hello"))
    out = capsys.readouterr().out
    assert "skipped" in out


def test_notify_posts_to_webhook(monkeypatch, capsys):
    import bot, config
    monkeypatch.setattr(config, "DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/fake")
    captured = {}

    class FakeResp:
        status = 204
        def __enter__(self): return self
        def __exit__(self, *a): pass

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["data"] = req.data
        return FakeResp()

    monkeypatch.setattr(bot.urllib.request, "urlopen", fake_urlopen)
    import argparse
    bot.cmd_notify(argparse.Namespace(text="test msg"))
    assert captured["url"] == "https://discord.com/api/webhooks/fake"
    assert b"test msg" in captured["data"]
    out = capsys.readouterr().out
    assert "204" in out


@patch("broker.alpaca._client")
def test_submit_order_refuses_past_budget(mock_client, capsys):
    import bot
    import config
    client = MagicMock()
    mock_client.return_value = client

    def _ord(status):
        o = MagicMock()
        o.id = "x"; o.symbol = "X"; o.side.value = "buy"; o.qty = 1
        o.status.value = status
        o.submitted_at.isoformat.return_value = "t"
        return o
    client.get_orders.return_value = [_ord("filled"), _ord("filled"), _ord("filled")]

    import argparse
    args = argparse.Namespace(
        symbol="AAPL", side="buy", qty=5, type="limit", limit_price=175.0,
        slot="open", rationale="test", dry_run=True,
    )
    import pytest
    with pytest.raises(SystemExit) as exc:
        bot.cmd_submit_order(args)
    assert exc.value.code == 3
