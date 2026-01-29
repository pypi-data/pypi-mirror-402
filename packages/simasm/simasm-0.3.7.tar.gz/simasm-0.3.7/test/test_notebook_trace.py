"""Test the trace collection code from the notebook."""

import simasm
print(f"SimASM version: {simasm.__version__}")

# Test the trace collection code from the notebook
from simasm.converter.event_graph.schema import EventGraphSpec
from simasm.converter.event_graph.converter import convert_eg

# Warehouse EG JSON for testing
warehouse_eg_json = {
  "model_name": "warehouse_eg",
  "description": "Test",
  "state_variables": {
    "Q1": {"type": "Nat", "initial": 0},
    "Q2": {"type": "Nat", "initial": 0},
    "Q3": {"type": "Nat", "initial": 0},
    "Q4": {"type": "Nat", "initial": 0},
    "Q5": {"type": "Nat", "initial": 0},
    "Q6": {"type": "Nat", "initial": 0},
    "S1": {"type": "Nat", "initial": 4},
    "S2": {"type": "Nat", "initial": 2},
    "S3": {"type": "Nat", "initial": 3},
    "S4": {"type": "Nat", "initial": 1},
    "S5": {"type": "Nat", "initial": 3},
    "S6": {"type": "Nat", "initial": 2},
    "departures": {"type": "Nat", "initial": 0}
  },
  "parameters": {
    "Q1_max": {"type": "Nat", "value": 30}, "Q2_max": {"type": "Nat", "value": 20},
    "Q3_max": {"type": "Nat", "value": 50}, "Q4_max": {"type": "Nat", "value": 20},
    "Q5_max": {"type": "Nat", "value": 30}, "Q6_max": {"type": "Nat", "value": 20},
    "S1_capacity": {"type": "Nat", "value": 4}, "S2_capacity": {"type": "Nat", "value": 2},
    "S3_capacity": {"type": "Nat", "value": 3}, "S4_capacity": {"type": "Nat", "value": 1},
    "S5_capacity": {"type": "Nat", "value": 3}, "S6_capacity": {"type": "Nat", "value": 2},
    "iat_c1_mean": {"type": "Real", "value": 325.5}, "iat_c2_mean": {"type": "Real", "value": 527.6},
    "iat_c3_mean": {"type": "Real", "value": 226.1}, "iat_c4_mean": {"type": "Real", "value": 985.6},
    "ist_s1_mean": {"type": "Real", "value": 78.4}, "ist_s2_mean": {"type": "Real", "value": 76.2},
    "ist_s3_mean": {"type": "Real", "value": 288.8}, "ist_s4_mean": {"type": "Real", "value": 31.2},
    "ist_s5_mean": {"type": "Real", "value": 66.8}, "ist_s6_mean": {"type": "Real", "value": 1.0},
    "sim_end_time": {"type": "Real", "value": 10000.0}
  },
  "random_streams": {
    "T_c1": {"distribution": "exponential", "params": {"mean": "iat_c1_mean"}, "stream_name": "creation_za1"},
    "T_c2": {"distribution": "exponential", "params": {"mean": "iat_c2_mean"}, "stream_name": "creation_za2"},
    "T_c3": {"distribution": "exponential", "params": {"mean": "iat_c3_mean"}, "stream_name": "creation_zb1"},
    "T_c4": {"distribution": "exponential", "params": {"mean": "iat_c4_mean"}, "stream_name": "creation_zb2"},
    "T_s1": {"distribution": "exponential", "params": {"mean": "ist_s1_mean"}, "stream_name": "service_pick_a"},
    "T_s2": {"distribution": "exponential", "params": {"mean": "ist_s2_mean"}, "stream_name": "service_pick_b"},
    "T_s3": {"distribution": "exponential", "params": {"mean": "ist_s3_mean"}, "stream_name": "service_label"},
    "T_s4": {"distribution": "exponential", "params": {"mean": "ist_s4_mean"}, "stream_name": "service_scan"},
    "T_s5": {"distribution": "exponential", "params": {"mean": "ist_s5_mean"}, "stream_name": "service_pack"},
    "T_s6": {"distribution": "exponential", "params": {"mean": "ist_s6_mean"}, "stream_name": "service_release"}
  },
  "vertices": [
    {"name": "CreateZA1", "state_change": "Q1 := Q1 + 1"},
    {"name": "CreateZA2", "state_change": "Q1 := Q1 + 1"},
    {"name": "CreateZB1", "state_change": "Q2 := Q2 + 1"},
    {"name": "CreateZB2", "state_change": "Q2 := Q2 + 1"},
    {"name": "AttemptPickA", "state_change": ""},
    {"name": "AttemptPickB", "state_change": ""},
    {"name": "AttemptLabel", "state_change": ""},
    {"name": "AttemptScan", "state_change": ""},
    {"name": "AttemptPack", "state_change": ""},
    {"name": "AttemptRelease", "state_change": ""},
    {"name": "StartPickA", "state_change": "Q1 := Q1 - 1; S1 := S1 - 1"},
    {"name": "StartPickB", "state_change": "Q2 := Q2 - 1; S2 := S2 - 1"},
    {"name": "StartLabel", "state_change": "Q3 := Q3 - 1; S3 := S3 - 1"},
    {"name": "StartScan", "state_change": "Q4 := Q4 - 1; S4 := S4 - 1"},
    {"name": "StartPack", "state_change": "Q5 := Q5 - 1; S5 := S5 - 1"},
    {"name": "StartRelease", "state_change": "Q6 := Q6 - 1; S6 := S6 - 1"},
    {"name": "FinishPickA", "state_change": "S1 := S1 + 1; Q3 := Q3 + 1"},
    {"name": "FinishPickB", "state_change": "S2 := S2 + 1; Q3 := Q3 + 1"},
    {"name": "FinishLabel", "state_change": "S3 := S3 + 1; Q4 := Q4 + 1"},
    {"name": "FinishScan", "state_change": "S4 := S4 + 1; Q5 := Q5 + 1"},
    {"name": "FinishPack", "state_change": "S5 := S5 + 1; Q6 := Q6 + 1"},
    {"name": "FinishRelease", "state_change": "S6 := S6 + 1; departures := departures + 1"}
  ],
  "scheduling_edges": [
    {"from": "CreateZA1", "to": "CreateZA1", "delay": "T_c1", "condition": "true", "priority": 1},
    {"from": "CreateZA1", "to": "AttemptPickA", "delay": 0, "condition": "Q1 <= Q1_max", "priority": 1},
    {"from": "CreateZA2", "to": "CreateZA2", "delay": "T_c2", "condition": "true", "priority": 2},
    {"from": "CreateZA2", "to": "AttemptPickA", "delay": 0, "condition": "Q1 <= Q1_max", "priority": 2},
    {"from": "CreateZB1", "to": "CreateZB1", "delay": "T_c3", "condition": "true", "priority": 3},
    {"from": "CreateZB1", "to": "AttemptPickB", "delay": 0, "condition": "Q2 <= Q2_max", "priority": 3},
    {"from": "CreateZB2", "to": "CreateZB2", "delay": "T_c4", "condition": "true", "priority": 4},
    {"from": "CreateZB2", "to": "AttemptPickB", "delay": 0, "condition": "Q2 <= Q2_max", "priority": 4},
    {"from": "AttemptPickA", "to": "StartPickA", "delay": 0, "condition": "S1 > 0 and Q1 > 0", "priority": 5},
    {"from": "AttemptPickB", "to": "StartPickB", "delay": 0, "condition": "S2 > 0 and Q2 > 0", "priority": 6},
    {"from": "AttemptLabel", "to": "StartLabel", "delay": 0, "condition": "S3 > 0 and Q3 > 0", "priority": 7},
    {"from": "AttemptScan", "to": "StartScan", "delay": 0, "condition": "S4 > 0 and Q4 > 0", "priority": 8},
    {"from": "AttemptPack", "to": "StartPack", "delay": 0, "condition": "S5 > 0 and Q5 > 0", "priority": 9},
    {"from": "AttemptRelease", "to": "StartRelease", "delay": 0, "condition": "S6 > 0 and Q6 > 0", "priority": 10},
    {"from": "StartPickA", "to": "FinishPickA", "delay": "T_s1", "condition": "true", "priority": 5},
    {"from": "StartPickB", "to": "FinishPickB", "delay": "T_s2", "condition": "true", "priority": 6},
    {"from": "StartLabel", "to": "FinishLabel", "delay": "T_s3", "condition": "true", "priority": 7},
    {"from": "StartScan", "to": "FinishScan", "delay": "T_s4", "condition": "true", "priority": 8},
    {"from": "StartPack", "to": "FinishPack", "delay": "T_s5", "condition": "true", "priority": 9},
    {"from": "StartRelease", "to": "FinishRelease", "delay": "T_s6", "condition": "true", "priority": 10},
    {"from": "FinishPickA", "to": "AttemptPickA", "delay": 0, "condition": "Q1 > 0", "priority": 5},
    {"from": "FinishPickA", "to": "AttemptLabel", "delay": 0, "condition": "Q3 <= Q3_max", "priority": 7},
    {"from": "FinishPickB", "to": "AttemptPickB", "delay": 0, "condition": "Q2 > 0", "priority": 6},
    {"from": "FinishPickB", "to": "AttemptLabel", "delay": 0, "condition": "Q3 <= Q3_max", "priority": 7},
    {"from": "FinishLabel", "to": "AttemptLabel", "delay": 0, "condition": "Q3 > 0", "priority": 7},
    {"from": "FinishLabel", "to": "AttemptScan", "delay": 0, "condition": "Q4 <= Q4_max", "priority": 8},
    {"from": "FinishScan", "to": "AttemptScan", "delay": 0, "condition": "Q4 > 0", "priority": 8},
    {"from": "FinishScan", "to": "AttemptPack", "delay": 0, "condition": "Q5 <= Q5_max", "priority": 9},
    {"from": "FinishPack", "to": "AttemptPack", "delay": 0, "condition": "Q5 > 0", "priority": 9},
    {"from": "FinishPack", "to": "AttemptRelease", "delay": 0, "condition": "Q6 <= Q6_max", "priority": 10},
    {"from": "FinishRelease", "to": "AttemptRelease", "delay": 0, "condition": "Q6 > 0", "priority": 10}
  ],
  "cancelling_edges": [],
  "initial_events": [
    {"event": "CreateZA1", "time": "T_c1"},
    {"event": "CreateZA2", "time": "T_c2"},
    {"event": "CreateZB1", "time": "T_c3"},
    {"event": "CreateZB2", "time": "T_c4"}
  ],
  "stopping_condition": "sim_clocktime >= sim_end_time",
  "observables": {}
}

# Convert to SimASM
print("Converting EG JSON to SimASM...")
eg_spec = EventGraphSpec.from_dict(warehouse_eg_json)
eg_simasm_code = convert_eg(eg_spec)
print(f"Generated EG model: {len(eg_simasm_code.splitlines())} lines")

# Test trace collection function from notebook
from simasm.parser import load_string
from simasm.runtime.stepper import ASMStepper, StepperConfig

def collect_state_trace(model_source: str, seed: int = 42, end_time: float = 10000.0):
    """Run model and collect state variables at each step."""
    loaded = load_string(model_source, seed=seed)

    main_rule = loaded.rules.get(loaded.main_rule_name)
    config = StepperConfig(time_var="sim_clocktime", end_time=end_time)
    stepper = ASMStepper(
        state=loaded.state,
        main_rule=main_rule,
        rule_evaluator=loaded.rule_evaluator,
        config=config,
    )

    # State variables to track
    trace_data = {
        'time': [],
        'Q1': [], 'Q2': [], 'Q3': [], 'Q4': [], 'Q5': [], 'Q6': [],
        'S1_busy': [], 'S2_busy': [], 'S3_busy': [], 'S4_busy': [], 'S5_busy': [], 'S6_busy': [],
        'departures': []
    }

    # Collect initial state
    def record_state():
        trace_data['time'].append(stepper.sim_time)
        # Queue lengths
        trace_data['Q1'].append(loaded.state.get_var('Q1'))
        trace_data['Q2'].append(loaded.state.get_var('Q2'))
        trace_data['Q3'].append(loaded.state.get_var('Q3'))
        trace_data['Q4'].append(loaded.state.get_var('Q4'))
        trace_data['Q5'].append(loaded.state.get_var('Q5'))
        trace_data['Q6'].append(loaded.state.get_var('Q6'))
        # Busy servers = capacity - available
        s1_cap = loaded.state.get_var('S1_capacity')
        s1_avail = loaded.state.get_var('S1')
        trace_data['S1_busy'].append(s1_cap - s1_avail)
        s2_cap = loaded.state.get_var('S2_capacity')
        s2_avail = loaded.state.get_var('S2')
        trace_data['S2_busy'].append(s2_cap - s2_avail)
        s3_cap = loaded.state.get_var('S3_capacity')
        s3_avail = loaded.state.get_var('S3')
        trace_data['S3_busy'].append(s3_cap - s3_avail)
        s4_cap = loaded.state.get_var('S4_capacity')
        s4_avail = loaded.state.get_var('S4')
        trace_data['S4_busy'].append(s4_cap - s4_avail)
        s5_cap = loaded.state.get_var('S5_capacity')
        s5_avail = loaded.state.get_var('S5')
        trace_data['S5_busy'].append(s5_cap - s5_avail)
        s6_cap = loaded.state.get_var('S6_capacity')
        s6_avail = loaded.state.get_var('S6')
        trace_data['S6_busy'].append(s6_cap - s6_avail)
        trace_data['departures'].append(loaded.state.get_var('departures'))

    record_state()  # Initial state

    # Run simulation
    while stepper.sim_time < end_time:
        if not stepper.step():
            break
        record_state()

    return trace_data

print("\nCollecting EG trace (seed=42, end_time=10000)...")
eg_trace = collect_state_trace(eg_simasm_code, seed=42, end_time=10000.0)
print(f"  Collected {len(eg_trace['time'])} state snapshots")
print(f"  Final time: {eg_trace['time'][-1]:.2f}")
print(f"  Final departures: {eg_trace['departures'][-1]}")

# Test statistics computation
import numpy as np

def compute_time_weighted_average(times, values):
    """Compute time-weighted average of a trace."""
    if len(times) < 2:
        return np.mean(values)
    dt = np.diff(times)
    weighted_sum = np.sum(np.array(values[:-1]) * dt)
    total_time = times[-1] - times[0]
    return weighted_sum / total_time if total_time > 0 else 0

print("\nStation Statistics:")
stations = [
    ('S1', 'Pick Zone A', 4, 'Q1', 'S1_busy'),
    ('S2', 'Pick Zone B', 2, 'Q2', 'S2_busy'),
    ('S3', 'Label', 3, 'Q3', 'S3_busy'),
    ('S4', 'Scan', 1, 'Q4', 'S4_busy'),
    ('S5', 'Pack', 3, 'Q5', 'S5_busy'),
    ('S6', 'Release', 2, 'Q6', 'S6_busy'),
]

print(f"{'Station':<12} {'Name':<14} {'Cap':>4} {'Avg Queue':>10} {'Max Queue':>10} {'Util %':>8}")
print("-" * 70)

for station_id, name, capacity, q_key, s_key in stations:
    avg_queue = compute_time_weighted_average(eg_trace['time'], eg_trace[q_key])
    max_queue = max(eg_trace[q_key])
    avg_busy = compute_time_weighted_average(eg_trace['time'], eg_trace[s_key])
    utilization = (avg_busy / capacity) * 100
    print(f"{station_id:<12} {name:<14} {capacity:>4} {avg_queue:>10.2f} {max_queue:>10} {utilization:>7.1f}%")

# Flow conservation check
final_idx = -1
wip_queues = sum(eg_trace[f'Q{i}'][final_idx] for i in range(1, 7))
wip_service = sum(eg_trace[f'S{i}_busy'][final_idx] for i in range(1, 7))
total_wip = wip_queues + wip_service
departures = eg_trace['departures'][final_idx]

print(f"\nFlow Conservation:")
print(f"  Departures: {departures}")
print(f"  WIP (queues + service): {total_wip}")
print(f"  Total jobs entered: {departures + total_wip}")

print("\n" + "=" * 70)
print("TEST PASSED!")
print("=" * 70)
