from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any, Dict

from app.models import AgentConfig, AgentFramework, Experiment, ExperimentStatus


class AgentExecutionError(Exception):
    """Raised when an agent execution fails."""


class AgentEngine:
    """Thin abstraction for executing agent experiments across frameworks."""

    def __init__(self) -> None:
        self._executors = {
            AgentFramework.crewai: self._run_crewai,
            AgentFramework.langchain: self._run_langchain,
            AgentFramework.openai: self._run_openai,
        }

    async def run(self, experiment: Experiment, agent: AgentConfig) -> Dict[str, Any]:
        experiment.status = ExperimentStatus.running
        experiment.started_at = datetime.now(timezone.utc)

        executor = self._executors.get(agent.framework)
        if not executor:
            raise AgentExecutionError(f"Unsupported framework: {agent.framework}")

        try:
            result = await executor(experiment, agent)
        except Exception as exc:  # pragma: no cover - defensive
            experiment.status = ExperimentStatus.failed
            experiment.error_message = str(exc)
            experiment.finished_at = datetime.now(timezone.utc)
            raise

        experiment.status = ExperimentStatus.completed
        experiment.finished_at = datetime.now(timezone.utc)
        experiment.result_payload = result
        return result

    async def _run_crewai(self, experiment: Experiment, agent: AgentConfig) -> Dict[str, Any]:
        # Placeholder - integrate CrewAI here. Simulated output for MVP.
        return {
            "framework": "CrewAI",
            "summary": "CrewAI simulation run completed",
            "inputs": experiment.input_payload,
            "parameters": agent.parameters,
            "score": round(random.uniform(0.6, 0.99), 3),
        }

    async def _run_langchain(self, experiment: Experiment, agent: AgentConfig) -> Dict[str, Any]:
        return {
            "framework": "LangChain",
            "chain_steps": [
                {"step": 1, "action": "Load tools", "success": True},
                {"step": 2, "action": "Execute chain", "success": True},
            ],
            "inputs": experiment.input_payload,
            "parameters": agent.parameters,
            "latency_ms": random.randint(100, 500),
        }

    async def _run_openai(self, experiment: Experiment, agent: AgentConfig) -> Dict[str, Any]:
        prompt = experiment.input_payload.get("prompt", "N/A")
        return {
            "framework": "OpenAI",
            "prompt": prompt,
            "completion": f"Simulated completion for prompt: {prompt[:50]}",
            "parameters": agent.parameters,
            "token_usage": {
                "prompt_tokens": random.randint(50, 200),
                "completion_tokens": random.randint(50, 200),
            },
        }


agent_engine = AgentEngine()
