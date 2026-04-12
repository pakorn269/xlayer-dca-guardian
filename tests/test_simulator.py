import pytest
import matplotlib
matplotlib.use('Agg')  # non-interactive backend for headless testing
from unittest.mock import MagicMock

# Patch subprocess so onchainos CLI calls don't run (selective: only intercept onchainos)
import subprocess
orig_run = subprocess.run

@pytest.fixture(autouse=True)
def mock_subprocess(monkeypatch):
    mock_result = MagicMock()
    mock_result.stdout = '{"ok": false}'

    def fake_run(cmd, *args, **kwargs):
        if isinstance(cmd, list) and len(cmd) > 0 and cmd[0] == "onchainos":
            return mock_result
        return orig_run(cmd, *args, **kwargs)

    monkeypatch.setattr("subprocess.run", fake_run)

from simulator import DCASimulator


def test_same_token_guard_returns_zero():
    sim = DCASimulator("USDC", "USDC", 50, 7, 30)
    result = sim.run()
    assert result == 0.0


def test_prices_exposed_after_run():
    sim = DCASimulator("USDC", "ETH", 50, 7, 30)
    sim.run()
    assert hasattr(sim, "prices")
    assert len(sim.prices) > 0


def test_avg_cost_final_is_positive():
    sim = DCASimulator("USDC", "ETH", 50, 7, 30)
    sim.run()
    assert sim.avg_cost_final > 0


def test_avg_cost_in_trades():
    sim = DCASimulator("USDC", "ETH", 50, 7, 30)
    sim.run()
    assert "avg_cost" in sim.trades[0]
    assert sim.trades[0]["avg_cost"] > 0
