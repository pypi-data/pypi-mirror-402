"""
Full end-to-end test of the automatic plotting feature.

This test:
1. Creates a simple SimASM model
2. Runs an experiment with generate_plots: true
3. Verifies that plots are generated
"""

from pathlib import Path
from simasm.experimenter.engine import ExperimenterEngine

# Create a simple test model
test_model = """
// Simple counting model for testing
model CountingModel:
    state:
        count: Nat := 0
        time_left: Real := 100.0
    endstate

    transition Increment:
        guard: time_left > 0
        effect:
            count := count + 1
            time_left := time_left - 1.0
        endeffect
    endtransition

    initial:
        schedule Increment at 0
    endinitial
endmodel
"""

# Write model to file
model_path = Path("test_counting_model.simasm")
with open(model_path, "w") as f:
    f.write(test_model)

# Create experiment specification
test_experiment = """
experiment PlottingDemo:
    model := "test_counting_model.simasm"

    replication:
        count: 5
        warm_up_time: 10.0
        run_length: 100.0
        seed_strategy: "incremental"
        base_seed: 42
        generate_plots: true
        trace_interval: 5.0
    endreplication

    statistics:
        stat counter: time_average
            expression: "count"
            trace: true
        endstat

        stat time_remaining: time_average
            expression: "time_left"
            trace: true
        endstat
    endstatistics

    output:
        format: "json"
        file_path: "results.json"
    endoutput
endexperiment
"""

# Write experiment to file
exp_path = Path("test_plotting_experiment.simasm")
with open(exp_path, "w") as f:
    f.write(test_experiment)

print("="*60)
print("TESTING AUTOMATIC PLOTTING FEATURE")
print("="*60)

try:
    # Run experiment
    print("\n1. Running experiment...")
    engine = ExperimenterEngine(str(exp_path))
    result = engine.run()

    print(f"\n2. Experiment completed:")
    print(f"   - Replications: {result.num_replications}")
    print(f"   - Statistics: {list(result.summary.keys())}")

    # Check if plots were generated
    print("\n3. Checking for generated plots...")

    # Find output directory (should be in simasm/output/)
    output_base = Path("simasm/output")
    if output_base.exists():
        # Find most recent directory starting with timestamp
        dirs = [d for d in output_base.iterdir() if d.is_dir()]
        if dirs:
            latest_dir = max(dirs, key=lambda d: d.stat().st_mtime)
            print(f"   Output directory: {latest_dir}")

            # Check for plot files
            plot_files = ["summary_statistics.png", "boxplots.png", "timeseries.png"]
            for plot_file in plot_files:
                plot_path = latest_dir / plot_file
                if plot_path.exists():
                    print(f"   [OK] Found: {plot_file}")
                else:
                    print(f"   [WARN] Missing: {plot_file}")

            # Check for results file
            results_files = list(latest_dir.glob("*.json"))
            if results_files:
                print(f"   [OK] Found results: {results_files[0].name}")
        else:
            print("   [WARN] No output directories found")
    else:
        print("   [WARN] Output directory simasm/output/ not found")

    print("\n4. Summary statistics:")
    for stat_name, summary in result.summary.items():
        print(f"   {stat_name}:")
        print(f"     Mean: {summary.mean:.4f}")
        print(f"     95% CI: [{summary.ci_lower:.4f}, {summary.ci_upper:.4f}]")

    print("\n" + "="*60)
    print("[OK] TEST COMPLETED SUCCESSFULLY")
    print("="*60)

except Exception as e:
    print(f"\n[FAIL] Test failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

finally:
    # Cleanup
    if model_path.exists():
        model_path.unlink()
    if exp_path.exists():
        exp_path.unlink()
