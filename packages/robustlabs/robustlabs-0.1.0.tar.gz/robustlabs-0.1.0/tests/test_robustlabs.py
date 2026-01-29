from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from robustlabs.api import app
from robustlabs.amt import map_assumptions
from robustlabs.domain import (
    StrategySpec,
    RunSpec,
    EvalInput,
    Artifact,
    ArtifactType,
)
from robustlabs.evaluator import Evaluator
from robustlabs.plugins import BasicMetricsPlugin, RegimeSlicingPlugin

client = TestClient(app)

@pytest.fixture
def basic_run_spec():
    return RunSpec(
        strategy=StrategySpec(
            strategy_id="test-strat",
            name="Test Strategy",
            asset_class="equities",
            horizon="daily",
            universe="SP500",
        ),
        data_window="2020..2024",
    )

def test_evaluator_plugins(basic_run_spec):
    ev = Evaluator()
    ev.register_plugin(BasicMetricsPlugin())
    ev.register_plugin(RegimeSlicingPlugin())
    
    out = ev.evaluate(basic_run_spec)
    assert len(out.artifacts) > 0
    names = {a.name for a in out.artifacts}
    assert "cagr" in names
    assert "tail_amplification" in names
    assert "regime_performance" in names

def test_map_assumptions_logic(basic_run_spec):
    # Case: High tail amplification
    artifacts = [
        Artifact(
            artifact_id="1",
            type=ArtifactType.METRIC,
            name="tail_amplification",
            payload={"value": 3.0} # > 2.5
        )
    ]
    am = map_assumptions(strategy=basic_run_spec.strategy, artifacts=artifacts)
    
    # Check A1
    a1 = next(a for a in am.assumptions if a.assumption_id == "A1")
    assert a1.severity == "critical"
    
    # Check Triggers
    assert len(am.triggers) >= 1
    t1 = am.triggers[0]
    assert t1.title == "Tail amplification breach"

def test_api_generate_report(basic_run_spec, tmp_path, monkeypatch):
    # Monkeypatch cwd to throw data in tmp_path
    monkeypatch.chdir(tmp_path)
    
    req_data = {
        "eval_input": {
            "run": basic_run_spec.model_dump(mode="json"),
            "artifacts": []
        }
    }
    
    response = client.post("/reports/generate", json=req_data)
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert "saved_path" in data
    
    # Verify file creation
    import os
    saved_path = data["saved_path"]
    assert os.path.exists(os.path.join(saved_path, "report.md"))
    assert os.path.exists(os.path.join(saved_path, "report.json"))
