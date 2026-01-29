"""API client for the Veris CLI."""

from __future__ import annotations

import os
from typing import Any

import httpx
from httpx import HTTPStatusError
from veris_cli.errors import UpstreamServiceError

from veris_cli.errors import ConfigurationError
from veris_cli.models.engine import AgentConnnection


class ApiClient:
    """API client for the Veris CLI."""

    def __init__(
        self, base_url: str | None = None, agent_id: str | None = None, *, timeout: float = 30.0
    ):
        """Initialize API client.

        This ensures .env file is loaded and validates API key is present.
        """
        # pdb.set_trace()
        # load_dotenv(override=True)

        if not os.environ.get("VERIS_API_KEY"):
            print(
                "VERIS_API_KEY environment variable is not set. Please set it in your environment or create a .env file with VERIS_API_KEY=your-key-here"
            )
            raise ConfigurationError(
                message="VERIS_API_KEY environment variable is not set. "
                "Please set it in your environment or create a .env file with VERIS_API_KEY=your-key-here"
            )
        # Resolve base URL precedence: constructor > VERIS_API_URL > default
        if base_url:
            self.base_url = base_url
        else:
            env_url = os.environ.get("VERIS_API_URL")
            if not env_url:
                env_url = "https://simulator.api.veris.ai"
                os.environ["VERIS_API_URL"] = env_url
            self.base_url = env_url

        # Read API key from environment variable
        api_key = os.environ.get("VERIS_API_KEY")

        # Validate API key
        if api_key is None:
            raise ValueError(
                "VERIS_API_KEY environment variable is not set. "
                "Please set it in your environment or create a .env file with VERIS_API_KEY=your-key-here"
            )

        if not api_key.strip():
            raise ValueError(
                "VERIS_API_KEY environment variable is empty. Please provide a valid API key."
            )

        if agent_id:
            self.agent_id = agent_id

        default_headers: dict[str, str] = {"X-API-Key": api_key}

        self._areclient = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=default_headers,
        )

    async def _arequest(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        user_message: str | None = None,
    ) -> httpx.Response:
        """Async request helper to standardize error handling."""
        try:
            response = await self._areclient.request(
                method, path, json=json, params=params, headers=headers
            )
            response.raise_for_status()
            return response
        except HTTPStatusError as exc:
            raise UpstreamServiceError.from_httpx_error(
                exc,
                endpoint=f"{method} {path}",
                user_message=user_message or "The upstream service returned an error.",
            ) from exc

    # -----------------------------
    # SIMPLE FLOW
    # -----------------------------

    async def fetch_agent(self) -> dict[str, Any]:
        """Fetch an agent."""
        response = await self._arequest(
            "GET",
            f"/v3/agents/{self.agent_id}",
        )
        return response.json()

    async def list_scenario_sets(self) -> dict[str, Any]:
        """List scenario sets."""
        response = await self._arequest(
            "GET",
            f"/v3/agents/{self.agent_id}/scenario-sets",
        )
        return response.json()

    async def start_simulation(
        self,
        scenario_set_id: str,
        max_turns: int = 20,
        agent_connection: AgentConnnection | None = None,
        max_concurrent_sessions: int = 3,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Start a simulation."""
        response = await self._arequest(
            "POST",
            f"/v3/agents/{self.agent_id}/simulations",
            json={
                "scenario_set_id": scenario_set_id,
                "max_turns": max_turns,
                "agent_connection": agent_connection.model_dump() if agent_connection else None,
                "max_concurrent_sessions": max_concurrent_sessions,
                "tags": tags,
            },
        )
        return response.json()

    async def get_simulation_status(self, run_id: str) -> dict[str, Any]:
        """Get the status of a simulation."""
        response = await self._arequest(
            "GET",
            f"/v3/agents/{self.agent_id}/simulations/{run_id}",
        )
        return response.json()

    async def get_simulation_sessions(self, run_id: str) -> dict[str, Any]:
        """Get the logs of a simulation."""
        response = await self._arequest(
            "GET",
            f"/v3/agents/{self.agent_id}/simulations/{run_id}/sessions",
        )
        return response.json()

    async def get_simulation_session_logs(self, run_id: str, session_id: str) -> dict[str, Any]:
        """Get the logs of a simulation session."""
        response = await self._arequest(
            "GET",
            f"/v3/agents/{self.agent_id}/simulations/{run_id}/sessions/{session_id}/logs",
        )
        return response.json()

    async def kill_simulation(self, run_id: str) -> dict[str, Any]:
        """Kill a simulation."""
        response = await self._arequest(
            "POST",
            f"/v3/agents/{self.agent_id}/simulations/{run_id}/kill",
        )
        return response.json()

    async def list_evaluations(
        self, run_id: str | None = None, page: int = 1, per_page: int = 30
    ) -> dict[str, Any]:
        """List all evaluations across agent versions with pagination."""
        params = {"page": page, "per_page": per_page}
        if run_id is not None:
            params["run_id"] = run_id

        response = await self._arequest(
            "GET", f"/v3/agents/{self.agent_id}/evaluations", params=params
        )
        return response.json()

    async def get_simulation_results(self, run_id: str) -> dict[str, Any]:
        """Get the results of a simulation by listing evaluations filtered by run_id."""
        # Call the list evaluations endpoint with run_id filter
        response = await self.list_evaluations(run_id=run_id)

        # Extract the evaluations list
        evaluations = response.get("evaluations", [])

        if not evaluations:
            raise ValueError(f"No evaluations found for run_id: {run_id}")

        # Return the first evaluation
        return evaluations[0]

    # -----------------------------
    # AGENT CREATION
    # -----------------------------

    async def generate_agent_spec(self, prompt: str) -> dict[str, Any]:
        """Generate an agent specification from a natural language prompt.

        Args:
            prompt: Natural language description of the agent to create.

        Returns:
            AgentSpec with agent_config and evaluation_config.
        """
        response = await self._arequest(
            "POST",
            "/generate_agent_card",
            json={"message": prompt},
            user_message="Failed to generate agent specification from prompt.",
        )
        return response.json()

    async def create_agent(
        self,
        agent_config: dict[str, Any],
        evaluation_config: dict[str, Any] | None = None,
        version: str = "v1.0.0",
    ) -> dict[str, Any]:
        """Create a new agent with the given configuration.

        Args:
            agent_config: The agent configuration object.
            evaluation_config: Optional evaluation configuration.
            version: Version string for the agent (default: v1.0.0).

        Returns:
            The created agent object with id, version, and configs.
        """
        payload: dict[str, Any] = {
            "agent_config": agent_config,
            "version": version,
        }
        if evaluation_config:
            payload["evaluation_config"] = evaluation_config

        response = await self._arequest(
            "POST",
            "/v3/agents",
            json=payload,
            user_message="Failed to create agent.",
        )
        return response.json()

    # -----------------------------
    # SCENARIO SET CREATION
    # -----------------------------

    async def create_scenario_set(
        self,
        num_scenarios: int,
        version_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new scenario set for the agent.

        Args:
            num_scenarios: Number of scenarios to generate.
            version_id: Optional agent version ID to use.

        Returns:
            Response with scenario_set_id.
        """
        payload: dict[str, Any] = {"num_scenarios": num_scenarios}
        if version_id:
            payload["version_id"] = version_id

        response = await self._arequest(
            "POST",
            f"/v3/agents/{self.agent_id}/scenario-sets",
            json=payload,
            user_message="Failed to create scenario set.",
        )
        return response.json()
