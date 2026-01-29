import typer
from rich.console import Console
from rich.panel import Panel
import uvicorn
from pathlib import Path

app = typer.Typer(help="Robustlabs: Investment Strategy Robustness & Reporting CLI")
console = Console()

from pathlib import Path
import sys
import importlib.util

from robustlabs.domain import StrategySpec, RunSpec
from robustlabs.evaluator import Evaluator
from robustlabs.plugins import BasicMetricsPlugin, RegimeSlicingPlugin, TimingSensitivityPlugin
from robustlabs.amt import map_assumptions
from robustlabs.rg import generate_report
from robustlabs.api import FileRunLedger

@app.command()
def run(
    strategy_file: str = typer.Argument(..., help="Path to the strategy python file (must export a 'strategy' variable of type StrategySpec)."),
    output_dir: str = typer.Option("runs", help="Directory to save run artifacts."),
):
    """
    Run a robustness analysis on a given strategy.
    
    The strategy file must resolve to a Python module that defines a variable named `strategy` 
    which is an instance of `robustlabs.domain.StrategySpec`.
    """
    console.print(Panel(f"Running analysis on [bold cyan]{strategy_file}[/bold cyan]...", title="Robustlabs"))
    
    # 1. Load StrategySpec from file
    p = Path(strategy_file)
    if not p.exists():
        console.print(f"[bold red]Error:[/bold red] File {strategy_file} not found.")
        raise typer.Exit(code=1)
        
    try:
        spec = importlib.util.spec_from_file_location("user_strategy", p)
        if spec is None or spec.loader is None:
             raise ImportError(f"Could not load spec from {p}")
        module = importlib.util.module_from_spec(spec)
        sys.modules["user_strategy"] = module
        spec.loader.exec_module(module)
        
        if not hasattr(module, "strategy"):
             console.print(f"[bold red]Error:[/bold red] Module must define a 'strategy' variable.")
             raise typer.Exit(code=1)
             
        strat: StrategySpec = module.strategy
        console.print(f"Loaded Strategy: [green]{strat.name}[/green] ({strat.strategy_id})")
        
    except Exception as e:
        console.print(f"[bold red]Error loading strategy:[/bold red] {e}")
        raise typer.Exit(code=1)

    # 2. Run Analysis
    console.print("[yellow]Initializing evaluation...[/yellow]")
    
    # Default settings for now
    run_spec = RunSpec(
        strategy=strat,
        data_window="2015-01-01 to 2024-01-01", # TODO: Make configurable via CLI
        notes=f"CLI Run from {strategy_file}"
    )

    evaluator = Evaluator()
    evaluator.register_plugin(BasicMetricsPlugin())
    evaluator.register_plugin(RegimeSlicingPlugin())
    evaluator.register_plugin(TimingSensitivityPlugin())
    
    with console.status("[bold green]Running plugins...[/bold green]"):
        eval_output = evaluator.evaluate(run_spec)
        
    console.print(f"Generated {len(eval_output.artifacts)} artifacts.")

    # 3. Map Assumptions
    console.print("Mapping Assumptions...")
    assumption_map = map_assumptions(strategy=strat, artifacts=eval_output.artifacts)
    
    # 4. Generate Report
    console.print("Generating Report...")
    report = generate_report(
        run_id=eval_output.run_id,
        run=run_spec,
        artifacts=eval_output.artifacts,
        assumption_map=assumption_map
    )
    
    # 5. Save
    ledger = FileRunLedger(root=Path(output_dir))
    saved_path = ledger.save_report(report)
    
    console.print(Panel(f"Analysis Complete!\nReport saved to: [bold underline]{saved_path}[/bold underline]\n\nRun [bold white]robustlabs dashboard[/bold white] to view.", title="Success", border_style="green"))

@app.command()
def dashboard(
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = False,
):
    """
    Start the Robustlabs dashboard server.
    """
    console.print(Panel(f"Starting dashboard at [bold green]http://{host}:{port}[/bold green]", title="Robustlabs Dashboard"))
    
    # We import here to avoid circular imports or heavy load if just running --help
    uvicorn.run("robustlabs.web.server:app", host=host, port=port, reload=reload)

if __name__ == "__main__":
    app()
