import sys
from pathlib import Path

# Updated imports
from robustlabs.domain import (
    StrategySpec,
    RunSpec,
    EvalInput,
)
from robustlabs.evaluator import Evaluator
from robustlabs.plugins import (
    BasicMetricsPlugin, 
    RegimeSlicingPlugin, 
    TimingSensitivityPlugin
)
# Explicit module usage
from robustlabs.amt import map_assumptions
from robustlabs.rg import generate_report
from robustlabs.api import FileRunLedger


def main():
    print("Initializing Strategy...")
    strat = StrategySpec(
        strategy_id="demo_mark2",
        name="Robustlabs Mark 2 Demo",
        description="Refactored demo using robustlabs package.",
        asset_class="equities",
        horizon="daily",
        universe="S&P 500",
        constraints=["Long only"]
    )

    print("Creating RunSpec...")
    run = RunSpec(
        strategy=strat,
        data_window="2015-01-01 to 2024-01-01",
        notes="Testing new package structure (AMT/RG split)"
    )

    print("Running Evaluation (with Plugins)...")
    evaluator = Evaluator()
    evaluator.register_plugin(BasicMetricsPlugin())
    evaluator.register_plugin(RegimeSlicingPlugin())
    evaluator.register_plugin(TimingSensitivityPlugin())
    
    eval_output = evaluator.evaluate(run)
    print(f"Generated {len(eval_output.artifacts)} artifacts.")

    print("Mapping Assumptions (AMT Module)...")
    assumption_map = map_assumptions(
        strategy=strat,
        artifacts=eval_output.artifacts
    )
    print(f"Mapped {len(assumption_map.assumptions)} assumptions.")
    
    print("Generating Report (RG Module)...")
    report = generate_report(
        run_id=eval_output.run_id,
        run=run,
        artifacts=eval_output.artifacts,
        assumption_map=assumption_map
    )

    print("Saving to Ledger...")
    ledger = FileRunLedger(root=Path("runs"))
    saved_path = ledger.save_report(report)
    print(f"Report saved to: {saved_path}")
    
    print("\n--- Report Preview ---\n")
    print(report.markdown[:500] + "...")

if __name__ == "__main__":
    main()
