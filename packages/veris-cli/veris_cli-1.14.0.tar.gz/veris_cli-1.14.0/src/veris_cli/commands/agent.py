"""Agent management commands."""

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

agent_app = typer.Typer(add_completion=False, no_args_is_help=True)


@agent_app.command("show")
def show_agent(
    agent_id: str | None = typer.Option(None, "--agent-id", help="Agent ID to fetch"),
):
    """Show agent information."""
    # Use provided agent_id or fall back to environment variable
    if agent_id is None:
        agent_id = os.environ.get("VERIS_AGENT_ID")
        if not agent_id:
            rprint("[red]Error:[/red] No agent ID provided.")
            rprint("Either pass --agent-id or set VERIS_AGENT_ID environment variable.")
            raise typer.Exit(1)

    try:
        client = ApiClient(agent_id=agent_id)
        agent_data = asyncio.run(client.fetch_agent())

        rprint(f"\n[bold]Agent: {agent_id}[/bold]\n")
        rprint(JSON.from_data(agent_data))
    except Exception as e:
        rprint(f"[red]Error fetching agent:[/red] {e}")
        raise typer.Exit(1)


@agent_app.command("create")
def create_agent(
    prompt: str = typer.Option(..., "--prompt", help="Natural language description of the agent"),
    version: str = typer.Option("v1.0.0", "--version", help="Version string for the agent"),
):
    """Create a new agent from a natural language prompt."""
    try:
        client = ApiClient()

        rprint("[cyan]Generating agent specification from prompt...[/cyan]")
        rprint(f"  Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

        # Generate agent spec from prompt
        agent_spec = asyncio.run(client.generate_agent_spec(prompt))

        agent_config = agent_spec.get("agent_config")
        evaluation_config = agent_spec.get("evaluation_config")

        if not agent_config:
            rprint("[red]Error:[/red] Failed to generate agent configuration from prompt.")
            raise typer.Exit(1)

        rprint("[cyan]Creating agent...[/cyan]")

        # Create the agent
        agent_data = asyncio.run(
            client.create_agent(
                agent_config=agent_config,
                evaluation_config=evaluation_config,
                version=version,
            )
        )

        agent_id = agent_data.get("id")
        rprint("\n[green]✓[/green] Agent created successfully")
        rprint(f"  Agent ID: [bold]{agent_id}[/bold]")
        rprint(f"  Version: {agent_data.get('version', version)}")
        rprint("\n[bold]Agent Configuration:[/bold]")
        rprint(JSON.from_data(agent_data))

        # Auto-save agent_id to config
        project_dir = Path.cwd()
        veris_dir = ensure_veris_dir(project_dir)
        config_path = veris_dir / "config.yaml"

        config = {}
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}

        config["VERIS_AGENT_ID"] = agent_id
        os.environ["VERIS_AGENT_ID"] = agent_id

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)

        rprint("\n[green]✓[/green] Agent ID saved to [bold].veris/config.yaml[/bold]")

    except Exception as e:
        rprint(f"[red]Error creating agent:[/red] {e}")
        raise typer.Exit(1)
