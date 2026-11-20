import click
import os
import requests
from aibenchmark.history import init_db, get_runs, get_latest_run_id
from aibenchmark.engine import run_all
from aibenchmark.report import generate_report, generate_trend_report
from aibenchmark.providers import PROVIDERS


PROVIDER_API_KEYS = {
    "openrouter": "OPENROUTER_API_KEY",
    "nvidia": "NVIDIA_API_KEY",
    "groq": "GROQ_API_KEY",
    "zhipu": "ZAI_API_KEY",
}

OLLAMA_HOST = "http://localhost:11434"


@click.group()
def bench():
    """AI-Benchmark v2: Personal free-tier LLM model selector."""
    init_db()


@bench.command()
@click.option("--notes", default="", help="Optional notes for this run.")
def run(notes: str):
    """Run all providers x models x categories against the current problem set."""
    click.echo("Starting benchmark run...")
    run_id = run_all(notes)
    click.echo(f"\nRun #{run_id} complete. Generating report...")
    report = generate_report(run_id)
    click.echo(report)


@bench.command()
@click.option("--last", "last_n", default=1, type=int, help="Reprint report from N runs ago.")
def report(last_n: int):
    """Reprint a markdown report from a past run."""
    runs = get_runs()
    if last_n > len(runs):
        click.echo(f"Only {len(runs)} run(s) available, but requested last {last_n}.")
        last_n = len(runs)
    if last_n <= 0:
        click.echo("No runs available. Run 'bench run' first.")
        return
    run_id = runs[last_n - 1].id
    md = generate_report(run_id)
    click.echo(md)


@bench.command()
@click.option("--category", required=True, help="Category to show trend for.")
@click.option("--model", required=True, help="Model name.")
@click.option("--provider", required=True, help="Provider name.")
def trend(category: str, model: str, provider: str):
    """Show a model's score over time for one category."""
    md = generate_trend_report("history.db", category, model, provider)
    click.echo(md)


@bench.command()
def doctor():
    """Preflight check: verify Ollama reachability + model availability, and API keys for all providers."""
    click.echo("Running preflight checks...\n")
    
    # Check Ollama - verify model is listed (generation test can be slow on first load)
    ollama_ready = False
    ollama_details = ""
    ollama_model = None
    try:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            # Check if configured model is available
            for provider_name, info in PROVIDERS.items():
                if provider_name == "ollama":
                    for model in info["models"]:
                        if model in models:
                            ollama_model = model
                            break
                    break
            
            if ollama_model:
                ollama_ready = True
                ollama_details = f"OK (model: {ollama_model})"
            else:
                ollama_details = f"Configured model not found. Available: {models}"
        else:
            ollama_details = f"HTTP {resp.status_code}"
    except Exception as e:
        ollama_details = f"Failed: {e}"
    
    # Check API keys for providers that need them
    provider_status = {}
    for provider_name, info in PROVIDERS.items():
        if provider_name == "ollama":
            continue
        key_env = PROVIDER_API_KEYS.get(provider_name)
        if key_env:
            key_present = bool(os.environ.get(key_env))
            provider_status[provider_name] = {
                "ready": key_present,
                "details": f"API key {'set' if key_present else 'MISSING'} ({key_env})",
                "models": info["models"],
            }
        else:
            provider_status[provider_name] = {
                "ready": False,
                "details": "No API key env var defined",
                "models": info["models"],
            }
    
    # Print results table
    click.echo("Provider Status:")
    click.echo("=" * 80)
    click.echo(f"{'Provider':<15} {'Ready':<8} {'Models':<40} {'Details'}")
    click.echo("-" * 80)
    
    # Ollama row
    model_display = ollama_model if ollama_model else "N/A"
    click.echo(f"{'ollama':<15} {'✓' if ollama_ready else '✗':<8} {model_display:<40} {ollama_details}")
    
    for provider_name, status in provider_status.items():
        ready_str = "✓" if status["ready"] else "✗"
        models_str = ", ".join(status["models"])
        click.echo(f"{provider_name:<15} {ready_str:<8} {models_str:<40} {status['details']}")
    
    click.echo("-" * 80)
    all_ready = ollama_ready and all(s["ready"] for s in provider_status.values())
    if all_ready:
        click.echo("\n✓ All providers ready for benchmark run")
    else:
        click.echo("\n✗ Some providers not ready — see details above")


if __name__ == "__main__":
    bench()