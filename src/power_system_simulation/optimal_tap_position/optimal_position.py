from .minimal_energy_loss import compute_best_tap_losses
from .minimal_voltage_deviation import compute_best_tap_voltage
from .powerflow_calculation import run_powerflow_all_taps


def get_optimal_tap(model, tap_positions, criterion, input_data, active_profile, reactive_profile):

    """
    Determine the optimal transformer tap position.

    Parameters:
        criterion (str):
            "losses"   minimal total energy loss of all the lines and the whole time period
            "voltage"  minimal (averaged) deviation of (max and min) p.u. node voltages with respect to 1 p.u.
        power flow calculation inputs:
            "model"     the grid model
            "tap_positions" list of tap positions to evaluate
            "input_data" dict with necessary input data for power flow calculation (e.g. source
                            node, busbar, transformer, feeders, etc.)
            "active_profile" pandas DataFrame with active power profile (index: timestamps, columns: node ids)
            "reactive_profile" pandas DataFrame with reactive power profile (index: timestamps, columns

    Returns:
        best_tap (int): tap position that optimizes the criterion
    """

    # validate criterion
    if criterion not in ["losses", "voltage"]:
        raise ValueError("criterion must be 'losses' or 'voltage'")

    # run power flow for each tap position
    results_per_tap = run_powerflow_all_taps(model, tap_positions, input_data, active_profile, reactive_profile)

    # choose best tap
    if criterion == "losses":
        best_tap = compute_best_tap_losses(results_per_tap)

    elif criterion == "voltage":
        best_tap = compute_best_tap_voltage(results_per_tap)

    return best_tap
