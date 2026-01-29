"""Scenario generation commands."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import typer
import yaml
from rich import print as rprint
from rich.json import JSON

from veris_cli.api import ApiClient
from veris_cli.fs import ensure_veris_dir

scenario_app = typer.Typer(add_completion=False, no_args_is_help=False)


@scenario_app.command("list")
def list_scenario_sets(
    agent_id: str | None = typer.Option(None, "--agent-id", help="Agent ID"),
):
    """List scenario sets for an agent."""
    # Use provided agent_id or fall back to environment variable
    if agent_id is None:
        agent_id = os.environ.get("VERIS_AGENT_ID")
        if not agent_id:
            rprint("[red]Error:[/red] No agent ID provided.")
            rprint("Either pass --agent-id or set VERIS_AGENT_ID environment variable.")
            raise typer.Exit(1)

    try:
        client = ApiClient(agent_id=agent_id)
        scenario_sets_data = asyncio.run(client.list_scenario_sets())

        rprint(f"\n[bold]Scenario Sets for Agent: {agent_id}[/bold]\n")
        rprint(JSON.from_data(scenario_sets_data))
    except Exception as e:
        rprint(f"[red]Error listing scenario sets:[/red] {e}")
        raise typer.Exit(1)


@scenario_app.command("create")
def create_scenario_set(
    num_scenarios: int = typer.Option(
        ..., "--num-scenarios", help="Number of scenarios to generate"
    ),
    agent_id: str | None = typer.Option(None, "--agent-id", help="Agent ID"),
    version_id: str | None = typer.Option(None, "--version-id", help="Agent version ID to use"),
):
    """Create a new scenario set for an agent."""
    # Use provided agent_id or fall back to environment variable
    if agent_id is None:
        agent_id = os.environ.get("VERIS_AGENT_ID")
        if not agent_id:
            rprint("[red]Error:[/red] No agent ID provided.")
            rprint("Either pass --agent-id or set VERIS_AGENT_ID environment variable.")
            raise typer.Exit(1)

    try:
        client = ApiClient(agent_id=agent_id)

        rprint("[cyan]Creating scenario set...[/cyan]")
        rprint(f"  Agent ID: {agent_id}")
        rprint(f"  Number of scenarios: {num_scenarios}")
        if version_id:
            rprint(f"  Version ID: {version_id}")

        result = asyncio.run(
            client.create_scenario_set(
                num_scenarios=num_scenarios,
                version_id=version_id,
            )
        )

        scenario_set_id = result.get("scenario_set_id")
        rprint("\n[green]✓[/green] Scenario set created successfully")
        rprint(f"  Scenario Set ID: [bold]{scenario_set_id}[/bold]")
        rprint(JSON.from_data(result))

        # Auto-save scenario_set_id to config
        project_dir = Path.cwd()
        veris_dir = ensure_veris_dir(project_dir)
        config_path = veris_dir / "config.yaml"

        config = {}
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}

        config["VERIS_SCENARIO_SET_ID"] = scenario_set_id
        os.environ["VERIS_SCENARIO_SET_ID"] = scenario_set_id

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)

        rprint("\n[green]✓[/green] Scenario Set ID saved to [bold].veris/config.yaml[/bold]")
        rprint("\nTo run a simulation: veris simulation launch")

    except Exception as e:
        rprint(f"[red]Error creating scenario set:[/red] {e}")
        raise typer.Exit(1)
