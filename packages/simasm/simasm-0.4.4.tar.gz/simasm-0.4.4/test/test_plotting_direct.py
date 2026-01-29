"""
Test the plotting module directly with real experiment results.
"""
from pathlib import Path
from simasm.experimenter.engine import ExperimenterEngine

# Run experiment
exp_path = Path("simasm/input/experiments/mm5_eg_littles_law_with_plots.simasm")
print(f"Running experiment: {exp_path}")

engine = ExperimenterEngine(str(exp_path))
result = engine.run()

print(f"\nExperiment complete!")
print(f"Replications: {result.num_replications}")
print(f"Statistics: {len(result.summary)}")

# Check if plots were generated
output_base = Path("simasm/output")
if output_base.exists():
    dirs = sorted([d for d in output_base.iterdir() if d.is_dir()],
                 key=lambda d: d.stat().st_mtime, reverse=True)
    if dirs:
        latest_dir = dirs[0]
        print(f"\nOutput directory: {latest_dir}")

        plot_files = list(latest_dir.glob("*.png"))
        print(f"Plot files generated: {len(plot_files)}")
        for pf in plot_files:
            print(f"  - {pf.name}")

print("\nDone!")
