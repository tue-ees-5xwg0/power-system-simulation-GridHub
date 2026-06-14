import pandas as pd
from pytest import MonkeyPatch

import power_system_simulation.optimal_tap_position.minimal_energy_loss as mel


def test_compute_best_tap_losses(monkeypatch: MonkeyPatch):

    def fake_aggregate(output_data, timestamps):
        return pd.DataFrame({
            "Total_Loss": [1.0, 2.0]
        })

    monkeypatch.setattr(mel, "aggregate_line_results", fake_aggregate)

    results_per_tap = {
        0: {
            "output_data": {"x": 1},
            "timestamps": [0]
        },
        1: {
            "output_data": {
                "output_data": {"y": 2},
                "timestamps": [0]
            },
            "timestamps": [999]
        },
        2: {
            "output_data": {},
            "timestamps": []
        }
    }

    result = mel.compute_best_tap_losses(results_per_tap)

    assert result in results_per_tap

def test_compute_best_tap_losses_nested(monkeypatch: MonkeyPatch):

    def fake_aggregate(output_data, timestamps):
        return pd.DataFrame({"Total_Loss": [5.0]})

    monkeypatch.setattr(mel, "aggregate_line_results", fake_aggregate)

    results_per_tap = {
        0: {
            "output_data": {
                "output_data": {"x": 1},
                "timestamps": [0]
            },
            "timestamps": [999]
        }
    }

    result = mel.compute_best_tap_losses(results_per_tap)

    assert result == 0

def test_compute_best_tap_losses_exception(monkeypatch):

    def fake_aggregate(*args, **kwargs):
        raise ValueError

    monkeypatch.setattr(mel, "aggregate_line_results", fake_aggregate)

    results_per_tap = {
        0: {
            "output_data": {"x": 1},
            "timestamps": [0]
        }
    }

    result = mel.compute_best_tap_losses(results_per_tap)

    assert result == 0
