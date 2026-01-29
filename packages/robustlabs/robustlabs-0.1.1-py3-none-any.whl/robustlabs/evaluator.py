from __future__ import annotations
from uuid import uuid4

from .domain import RunSpec, EvalOutput, Artifact
from .plugins import EvidencePlugin

class Evaluator:
    def __init__(self) -> None:
        self.plugins: list[EvidencePlugin] = []

    def register_plugin(self, plugin: EvidencePlugin) -> None:
        self.plugins.append(plugin)

    def evaluate(self, run_spec: RunSpec, existing_artifacts: list[Artifact] = []) -> EvalOutput:
        artifacts = list(existing_artifacts)
        for plugin in self.plugins:
            # In a real system, we might handle errors per plugin here
            plugin_artifacts = plugin.run(run_spec)
            artifacts.extend(plugin_artifacts)
            
        return EvalOutput(
            run_id=str(uuid4()),
            artifacts=artifacts
        )
