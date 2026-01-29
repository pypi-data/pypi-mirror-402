"""
Test plotting directly by running the experiment and checking what happens.
"""
from pathlib import Path
import sys

# Add detailed logging
import logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

from simasm.experimenter.engine import ExperimenterEngine

exp_path = Path("simasm/input/experiments/mm5_eg_littles_law_with_plots.simasm")
print(f"Running experiment: {exp_path}")

engine = ExperimenterEngine(str(exp_path))

result = engine.run()

print(f"\nExperiment complete!")
print(f"  Replications: {result.num_replications}")
print(f"  Statistics: {len(result.summary)}")

# Check output directory
output_base = Path("simasm/output")
if output_base.exists():
    dirs = sorted([d for d in output_base.iterdir() if d.is_dir()],
                 key=lambda d: d.stat().st_mtime, reverse=True)
    if dirs:
        latest_dir = dirs[0]
        print(f"\nLatest output directory: {latest_dir}")

        all_files = list(latest_dir.iterdir())
        print(f"Files in directory: {len(all_files)}")
        for f in all_files:
            print(f"  - {f.name} ({f.stat().st_size} bytes)")

print("\nDone!")
