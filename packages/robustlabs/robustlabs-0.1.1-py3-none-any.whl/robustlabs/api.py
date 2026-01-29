from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from .domain import (
    Report,
    EvalInput,
)
from .evaluator import Evaluator
from .plugins import BasicMetricsPlugin, RegimeSlicingPlugin, TimingSensitivityPlugin
from .amt import map_assumptions
from .rg import generate_report


# ----------------------------
# Persistence (MVP: filesystem)
# ----------------------------


class FileRunLedger:
    def __init__(self, root: Path) -> None:
        self.root = root

    def save_report(self, report: Report) -> Path:
        run_dir = self.root / report.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "report.md").write_text(report.markdown, encoding="utf-8")
        (run_dir / "report.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
        return run_dir


# ----------------------------
# FastAPI
# ----------------------------


app = FastAPI(title="robustlabs-api", version="0.1.0")


class GenerateReportRequest(BaseModel):
    eval_input: EvalInput


class GenerateReportResponse(BaseModel):
    run_id: str
    report: Report
    saved_path: str


@app.post("/reports/generate", response_model=GenerateReportResponse)
def reports_generate(req: GenerateReportRequest) -> GenerateReportResponse:
    # MVP: Ledger root in current working directory / runs
    ledger = FileRunLedger(root=Path.cwd() / "runs")
    
    # Use the new Evaluator with Plugins
    evaluator = Evaluator()
    evaluator.register_plugin(BasicMetricsPlugin())
    evaluator.register_plugin(RegimeSlicingPlugin())
    evaluator.register_plugin(TimingSensitivityPlugin())
    
    out = evaluator.evaluate(req.eval_input.run, existing_artifacts=req.eval_input.artifacts)
    
    assumption_map = map_assumptions(
        strategy=req.eval_input.run.strategy,
        artifacts=out.artifacts,
    )
    report = generate_report(
        run_id=out.run_id,
        run=req.eval_input.run,
        artifacts=out.artifacts,
        assumption_map=assumption_map,
    )
    saved_path = ledger.save_report(report)
    return GenerateReportResponse(run_id=out.run_id, report=report, saved_path=str(saved_path))


# ----------------------------
# Dashboard Endpoints
# ----------------------------

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Enable CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunSummary(BaseModel):
    run_id: str
    as_of: str
    strategy_name: str

@app.get("/runs", response_model=list[RunSummary])
def list_runs() -> list[RunSummary]:
    # MVP: List directories in runs/
    # In a real app, this would query a DB
    root = Path.cwd() / "runs"
    runs: list[RunSummary] = []
    if root.exists():
        for d in root.iterdir():
            if d.is_dir() and (d / "report.json").exists():
                try:
                    report_json = (d / "report.json").read_text()
                    # Parse minimally to get strategy name
                    import json
                    data = json.loads(report_json)
                    strategy_name = data.get("data", {}).get("strategy", {}).get("name", "Unknown")
                    as_of = data.get("created_at", "")
                    runs.append(RunSummary(run_id=d.name, as_of=as_of, strategy_name=strategy_name))
                except Exception:
                    continue
    # Sort by recent first (heuristic)
    return sorted(runs, key=lambda r: r.as_of, reverse=True)

@app.get("/runs/{run_id}", response_model=Report)
def get_run(run_id: str) -> Report:
    root = Path.cwd() / "runs"
    report_path = root / run_id / "report.json"
    if not report_path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Run not found")
    
    return Report.model_validate_json(report_path.read_text())

# Serve static files (production build)
# app.mount("/", StaticFiles(directory="web/dist", html=True), name="static")
