from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os

app = FastAPI(title="Robustlabs Dashboard")

# Determine base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Ensure templates struct exists even if we haven't created it yet
if not os.path.exists(TEMPLATES_DIR):
    os.makedirs(TEMPLATES_DIR)

templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Mount static files if needed (e.g. customized css/js)
# app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

from robustlabs.api import FileRunLedger
from robustlabs.domain import Report
from pathlib import Path
import markdown

# ... (Previous imports)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    ledger = FileRunLedger(root=Path("runs"))
    latest_path = None
    
    # Simple naive latest finder (assuming filename sorts somewhat chronologically or we inspect mtime)
    # The Ledger currently saves by run_id, so we might need to inspect files.
    # For MVP, we list files and sort by mtime
    runs_dir = Path("runs")
    if runs_dir.exists():
        files = list(runs_dir.glob("*.json"))
        if files:
            latest_path = max(files, key=lambda p: p.stat().st_mtime)

    content_html = "<p class='text-gray-400'>No active analysis found. Use the CLI to run a robustness check.</p>"
    run_id = "N/A"
    title_text = "Dashboard"

    if latest_path:
        # Load the report
        try:
            with open(latest_path, "r") as f:
                # We use pydantic to parse it back? Or just json load.
                # Report model has a 'data' dict.
                # Ideally we use the Ledger to load it if it supports it, but FileRunLedger only has save_report shown in demo.
                # Let's rely on JSON loading or Pydantic.
                import json
                data = json.load(f)
                # Ensure it matches Report structure roughly or just grab markdown
                if "markdown" in data:
                     # Convert markdown to HTML
                     content_html = markdown.markdown(data["markdown"], extensions=['tables', 'fenced_code'])
                     run_id = data.get("run_id", "Unknown")
                     title_text = f"Report {run_id[:8]}"
        except Exception as e:
            content_html = f"<p class='text-red-400'>Error loading report: {e}</p>"

    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request, 
            "title": title_text,
            "run_id": run_id,
            "content": content_html
        }
    )

@app.get("/health")
def health_check():
    return {"status": "ok"}
