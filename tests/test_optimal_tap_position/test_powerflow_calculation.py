def test_run_powerflow_all_taps(monkeypatch):

    import power_system_simulation.optimal_tap_position.powerflow_calculation as pfc

    def fake_construct_model(input_data):
        return "model"

    def fake_create_batch_update(active_profile=None, reactive_profile=None):
        return {}, [0]

    def fake_run_power_flow(model=None, input_data=None, update_data=None):
        return {}

    monkeypatch.setattr(
        "power_system_simulation.optimal_tap_position.powerflow_calculation.construct_model",
        fake_construct_model,
        raising=False
    )

    monkeypatch.setattr(
        "power_system_simulation.optimal_tap_position.powerflow_calculation.create_batch_update",
        fake_create_batch_update,
        raising=False
    )

    monkeypatch.setattr(
        "power_system_simulation.optimal_tap_position.powerflow_calculation.run_power_flow",
        fake_run_power_flow,
        raising=False
    )

    input_data = {
        "transformer": {
            "tap_pos": [0, 0]
        }
    }

    tap_positions = [-1, 0, 1]

    results = pfc.run_powerflow_all_taps(
        model=None,
        tap_positions=tap_positions,
        input_data=input_data,
        active_profile=None,
        reactive_profile=None,
    )

    assert len(results) == 3
