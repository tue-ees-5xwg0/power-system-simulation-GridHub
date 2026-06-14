import pandas as pd

import power_system_simulation.optimal_tap_position.minimal_voltage_deviation as mvd


def test_compute_best_tap_voltage(monkeypatch):

    def fake_aggregate(output_data, timestamps):
        return pd.DataFrame({
            "Max_Voltage": [1.05, 1.02],
            "Min_Voltage": [0.95, 0.98],
        })

    monkeypatch.setattr(mvd, "aggregate_voltage_results", fake_aggregate)

    results_per_tap = {
        0: {
            "output_data": {"valid": True},
            "timestamps": [0, 1]
        },
        1: {
            "output_data": {
                "output_data": {"valid": True},
                "timestamps": [0, 1]
            },
            "timestamps": [999]
        },
        2: {
            "output_data": {},
            "timestamps": []
        }
    }

    result = mvd.compute_best_tap_voltage(results_per_tap)

    assert result in results_per_tap

def test_compute_best_tap_voltage_nested(monkeypatch):

    def fake_aggregate(output_data, timestamps):
        return pd.DataFrame({
            "Max_Voltage": [1.01],
            "Min_Voltage": [0.99],
        })

    monkeypatch.setattr(mvd, "aggregate_voltage_results", fake_aggregate)

    results_per_tap = {
        0: {
            "output_data": {
                "output_data": {"x": 1},
                "timestamps": [0]
            },
            "timestamps": [999]
        }
    }

    result = mvd.compute_best_tap_voltage(results_per_tap)

    assert result == 0

def test_compute_best_tap_voltage_exception(monkeypatch):

    def fake_aggregate(*args, **kwargs):
        raise ValueError

    monkeypatch.setattr(mvd, "aggregate_voltage_results", fake_aggregate)

    results_per_tap = {
        0: {
            "output_data": {"x": 1},
            "timestamps": [0]
        }
    }

    result = mvd.compute_best_tap_voltage(results_per_tap)

    assert result == 0
