import pytest

import power_system_simulation.optimal_tap_position.optimal_position as op


def test_get_optimal_tap_losses(monkeypatch):

    monkeypatch.setattr(
        op,
        "run_powerflow_all_taps",
        lambda *args, **kwargs: {
            1: {"output_data": {}, "timestamps": []}
        }
    )

    monkeypatch.setattr(op, "compute_best_tap_losses", lambda x: 1)

    result = op.get_optimal_tap(None, [1], "losses", None, None, None)

    assert result == 1


def test_get_optimal_tap_voltage(monkeypatch):

    monkeypatch.setattr(
        op,
        "run_powerflow_all_taps",
        lambda *args, **kwargs: {
            2: {"output_data": {}, "timestamps": []}
        }
    )

    monkeypatch.setattr(op, "compute_best_tap_voltage", lambda x: 2)

    result = op.get_optimal_tap(None, [2], "voltage", None, None, None)

    assert result == 2

def test_get_optimal_tap_invalid():

    from power_system_simulation.optimal_tap_position.optimal_position import get_optimal_tap

    with pytest.raises(ValueError):
        get_optimal_tap(None, [0], "invalid", None, None, None)
