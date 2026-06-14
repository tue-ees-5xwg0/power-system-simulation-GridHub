from power_system_simulation.optimal_tap_position.powerflow_calculation import run_powerflow_all_taps


def test_powerflow_function_exists():
    """
    Basic test to ensure the function is imported and callable.
    """

    assert run_powerflow_all_taps is not None
