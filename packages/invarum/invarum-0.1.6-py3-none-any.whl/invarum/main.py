# invarum-cli/invarum/main.py
import typer
import time
from rich.console import Console
from rich.table import Table
from invarum import config
from invarum.client import InvarumClient
from invarum import __version__
import json 
from pathlib import Path 
from rich.panel import Panel
from enum import Enum

class ExportFormat(str, Enum):
    json = "json"
    pdf = "pdf"

app = typer.Typer(
    name="invarum",
    help="Invarum CLI: Quality Engineering for LLMs",
    add_completion=False,
    no_args_is_help=True
)
console = Console()

@app.command()
def login(
    key: str = typer.Option(..., prompt=True, hide_input=True, help="Your Invarum API Key")
):
    """
    Save your API key to a local configuration file.
    """
    if not key.startswith("inv_sk_"):
        console.print("[red]Error:[/red] Key must start with 'inv_sk_'")
        raise typer.Exit(1)

    config.save_api_key(key)
    console.print(f"[bold green]Success![/bold green] API Key saved to {config.CONFIG_FILE}")

@app.command()
def run(
    prompt: str = typer.Argument(None, help="The prompt text"),
    file: Path = typer.Option(None, "--file", "-f", help="Path to a text file containing the prompt", exists=True),    
    task: str = typer.Option("default", "--task", "-t"),
    domain: str = typer.Option("general", "--domain", "-d"),
    
    # --- NEW FLAGS ---
    reference: str = typer.Option(None, "--reference", "-r", help="Reference text for comparison"),
    reference_file: Path = typer.Option(None, "--reference-file", "-rf", help="Path to reference text file", exists=True),
    # -----------------
    temperature: float = typer.Option(None, "--temp", help="Set generation temperature (0.0 - 1.0)"),
    json_out: bool = typer.Option(False, "--json", help="Output raw JSON"),
    output: Path = typer.Option(None, "--output", "-o", help="Save the full evidence bundle to a JSON file"),
    strict: bool = typer.Option(False, "--strict", help="Exit with code 1 if policy fails"),
):
    """
    Run a prompt through the Invarum engine.
    """
    # 1. Input Processing (Prompt)
    if file:
        prompt_text = file.read_text(encoding="utf-8")
    elif prompt:
        prompt_text = prompt
    else:
        console.print("[red]Error: Must provide either PROMPT argument or --file[/red]")
        raise typer.Exit(1)

    # 1b. Input Processing (Reference)
    reference_text = None
    if reference_file:
        reference_text = reference_file.read_text(encoding="utf-8")
    elif reference:
        reference_text = reference

    # 2. Auth
    key = config.get_api_key()
    if not key:
        console.print("[red]Error:[/red] Not logged in. Run [bold]invarum login[/bold] first.")
        raise typer.Exit(1)

    client = InvarumClient(key)

    # 3. Submit
    try:
        with console.status(f"[bold green]Submitting to engine (Task: {task})..."):
            response_data = client.submit_run(
                prompt=prompt_text, 
                task=task, 
                domain=domain, 
                reference=reference_text,
                temperature=temperature 
            )
            
            run_id = response_data["run_id"]
            
            # Check for update message
            if "system_message" in response_data:
                msg = response_data["system_message"]
                # Use a simple print if Panel causes import issues, or keep Panel if imported
                console.print(Panel(msg["text"], style="yellow", title="Update Available"))

        if not json_out:
             console.print(f"Run ID: [cyan]{run_id}[/cyan]")
             
    except ValueError as e:
        console.print(f"[red]Auth Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        # This catches the connection error and prints it clearly
        console.print(f"[red]Connection Error:[/red] {e}")
        raise typer.Exit(1)

    # 4. Poll
    try:
        if not json_out:
            with console.status("[bold green]Running physics engine..."):
                result = client.wait_for_run(run_id)
        else:
            result = client.wait_for_run(run_id)
    except Exception as e:
        console.print(f"[red]Run Failed:[/red] {e}")
        raise typer.Exit(1)

    # ---Save Logic ---
    if output:
        # Fetch the full bundle (which includes text if <24h)
        evidence = client.get_run_evidence(run_id)
        
        # Write to disk
        output.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        console.print(f"[green]Evidence bundle saved to:[/green] {output}")

    # 5. JSON Output Mode
    if json_out:
        evidence = client.get_run_evidence(run_id)
        result["evidence"] = evidence 
        print(json.dumps(result))
        # Logic check for CI/CD
        if strict and result.get("policy_pass") is False:
             raise typer.Exit(code=1)
        return

    # 6. Human Friendly Display 
    # --- UPDATED: Fetch & Display Response ---
    evidence = client.get_run_evidence(run_id)
    
    # Look in top level (old way) OR inside artifacts (new DB way)
    artifacts = evidence.get("artifacts") or {}
    
    response_text = (
        evidence.get("final_response") or 
        evidence.get("io", {}).get("response", "") or
        artifacts.get("final_response") or       
        artifacts.get("io", {}).get("response")  
    )
    
    if response_text:
        console.print(Panel(response_text, title="LLM Response", border_style="green"))
    else:
        # Debugging helper if it's still missing
        console.print(evidence) 
        console.print("[dim]No response text available.[/dim]")
    # -------------------------------------

    metrics = result.get("metrics") or result
    
    table = Table(title=f"Run ID: {result.get('run_id')}")
    table.add_column("Metric", style="cyan")
    table.add_column("Score", justify="right")

    def fmt(val):
        try:
            return f"{float(val):.3f}"
        except (ValueError, TypeError):
            return "0.000"

    table.add_row("Alpha (Task)",      fmt(metrics.get('alpha')))
    table.add_row("Beta (Coherence)",  fmt(metrics.get('beta')))
    table.add_row("Gamma (Entropy)",   fmt(metrics.get('gamma')))
    table.add_row("Delta (Efficiency)",fmt(metrics.get('delta')))
    
    console.print(table)
    
    pass_status = result.get("policy_pass")
    
    if pass_status is True:
        console.print(f"\n[bold green]PASSED POLICY GATES[/bold green]")
    elif pass_status is False:
        console.print(f"\n[bold red]FAILED POLICY GATES[/bold red]")
    else:
        console.print(f"\n[bold yellow]POLICY STATUS UNKNOWN[/bold yellow]")

    console.print(f"\nView full details: https://app.invarum.com/runs/{run_id}")

    if strict and pass_status is False:
         console.print("\n[bold red]Strict mode enabled: Exiting with code 1 due to policy failure.[/bold red]")
         raise typer.Exit(code=1)

def version_callback(value: bool):
    if value:
        print(f"Invarum CLI Version: {__version__}")
        raise typer.Exit()

@app.callback()
def main(
    version: bool = typer.Option(
        None, 
        "--version", 
        "-v", 
        callback=version_callback, 
        is_eager=True,
        help="Show the version and exit."
    )
):
    return

@app.command()
def export(
    run_id: str = typer.Argument(..., help="The Run ID to export"),
    format: ExportFormat = typer.Option(ExportFormat.json, "--format", "-f", help="Output format (json or pdf)"),
    output: Path = typer.Option(None, "--output", "-o", help="File path to save the output. If omitted, prints JSON to stdout."),
):
    """
    Export the Evidence Bundle or Audit PDF for a specific run.
    """
    # 1. Auth Check
    key = config.get_api_key()
    if not key:
        console.print("[red]Error:[/red] Not logged in.")
        raise typer.Exit(1)

    client = InvarumClient(key)

    try:
        # --- PDF EXPORT ---
        if format == ExportFormat.pdf:
            with console.status("[bold green]Generating Audit PDF..."):
                pdf_bytes = client.get_audit_pdf(run_id)
            
            if output:
                output.write_bytes(pdf_bytes)
                console.print(f"[green]PDF saved to:[/green] {output}")
            else:
                console.print("[red]Error: --output file is required for PDF export.[/red]")
                raise typer.Exit(1)

        # --- JSON EXPORT ---
        else:
            with console.status("[bold green]Fetching Evidence Bundle..."):
                data = client.get_run_evidence(run_id)
                
            if not data:
                console.print("[red]Error:[/red] Evidence not found.")
                raise typer.Exit(1)

            json_str = json.dumps(data, indent=2)

            if output:
                output.write_text(json_str, encoding="utf-8")
                console.print(f"[green]JSON saved to:[/green] {output}")
            else:
                # Print raw JSON to stdout so it can be piped
                print(json_str)

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Connection Error:[/red] {e}")
        raise typer.Exit(1)