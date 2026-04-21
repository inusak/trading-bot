"""Broker budget-cap tests using mock client."""
from unittest.mock import MagicMock, patch


def _mock_order(status="filled", side="buy"):
    o = MagicMock()
    o.id = "abc"
    o.symbol = "AAPL"
    o.side.value = side
    o.qty = 1
    o.status.value = status
    o.submitted_at.isoformat.return_value = "2026-04-22T09:35:00"
    return o


@patch("broker.alpaca._client")
def test_orders_today_excludes_canceled(mock_client):
    from broker import alpaca
    client = MagicMock()
    mock_client.return_value = client
    client.get_orders.return_value = [
        _mock_order(status="filled"),
        _mock_order(status="canceled"),
        _mock_order(status="new"),
        _mock_order(status="rejected"),
    ]
    orders = alpaca.get_orders_today()
    assert len(orders) == 2
    assert all(o["status"] in ("filled", "new") for o in orders)


@patch("broker.alpaca._client")
def test_submit_limit_order_requires_price(mock_client):
    from broker import alpaca
    import pytest
    with pytest.raises(ValueError, match="limit_price"):
        alpaca.submit_order("AAPL", "buy", 1, order_type="limit", limit_price=None)


@patch("broker.alpaca._client")
def test_submit_market_order_roundtrip(mock_client):
    from broker import alpaca
    client = MagicMock()
    mock_client.return_value = client
    client.submit_order.return_value = _mock_order(status="accepted")
    out = alpaca.submit_order("AAPL", "buy", 1, order_type="market")
    assert out["symbol"] == "AAPL"
    assert out["status"] == "accepted"
    client.submit_order.assert_called_once()
