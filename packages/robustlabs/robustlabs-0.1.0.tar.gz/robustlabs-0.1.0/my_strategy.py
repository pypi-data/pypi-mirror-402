from robustlabs.domain import StrategySpec

strategy = StrategySpec(
    strategy_id="test_strat_01",
    name="Local Test Strategy",
    description="A simple strategy for verifying local runs.",
    asset_class="equities",
    horizon="daily",
    universe="S&P 500",
    constraints=["Long only"]
)
