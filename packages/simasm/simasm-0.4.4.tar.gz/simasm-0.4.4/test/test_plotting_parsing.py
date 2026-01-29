"""
Test script to verify plotting configuration parsing.

This tests that the new fields (generate_plots, trace_interval, trace)
are correctly parsed from the experiment specification.
"""

from pathlib import Path
from simasm.experimenter.transformer import ExperimentParser

def test_plotting_config_parsing():
    """Test that plotting config fields are parsed correctly."""

    spec_path = Path("test_plotting_config.simasm")
    if not spec_path.exists():
        print(f"Error: {spec_path} not found")
        return False

    print("Parsing test specification...")
    parser = ExperimentParser()

    try:
        spec = parser.parse_file(str(spec_path))
        print(f"[OK] Parsed successfully: {spec.name}")

        # Check replication settings
        rep = spec.replication
        print(f"\nReplication settings:")
        print(f"  count: {rep.count}")
        print(f"  warm_up_time: {rep.warm_up_time}")
        print(f"  run_length: {rep.run_length}")
        print(f"  generate_plots: {rep.generate_plots}")
        print(f"  trace_interval: {rep.trace_interval}")

        # Verify new fields
        assert rep.generate_plots == True, "generate_plots should be True"
        assert rep.trace_interval == 0.5, "trace_interval should be 0.5"
        print("[OK] Replication settings parsed correctly")

        # Check statistics
        print(f"\nStatistics ({len(spec.statistics)}):")
        for stat in spec.statistics:
            print(f"  {stat.name}: {stat.stat_type}")
            print(f"    expression: {stat.expression}")
            print(f"    trace: {stat.trace}")

        # Verify trace flags
        test_avg = next((s for s in spec.statistics if s.name == "test_avg"), None)
        assert test_avg is not None, "test_avg statistic not found"
        assert test_avg.trace == True, "test_avg should have trace=True"

        test_util = next((s for s in spec.statistics if s.name == "test_util"), None)
        assert test_util is not None, "test_util statistic not found"
        assert test_util.trace == False, "test_util should have trace=False"

        print("[OK] Statistics parsed correctly")

        print("\n" + "="*50)
        print("[OK] ALL TESTS PASSED")
        print("="*50)
        return True

    except Exception as e:
        print(f"[FAIL] Parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_plotting_config_parsing()
    exit(0 if success else 1)
