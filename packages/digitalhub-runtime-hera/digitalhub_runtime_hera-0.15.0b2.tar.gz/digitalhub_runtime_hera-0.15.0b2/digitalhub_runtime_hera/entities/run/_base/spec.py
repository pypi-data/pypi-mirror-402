# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.run._base.spec import RunSpec, RunValidator


class RunSpecHeraRun(RunSpec):
    """RunSpecHeraRun specifications."""

    def __init__(
        self,
        task: str,
        local_execution: bool = False,
        function: str | None = None,
        workflow: str | None = None,
        volumes: list[dict] | None = None,
        resources: dict | None = None,
        envs: list[dict] | None = None,
        secrets: list[str] | None = None,
        profile: str | None = None,
        source: dict | None = None,
        build: dict | None = None,
        parameters: dict | None = None,
        inputs: dict | None = None,
        outputs: dict | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            task,
            local_execution,
            function,
            workflow,
            volumes,
            resources,
            envs,
            secrets,
            profile,
            **kwargs,
        )
        self.source = source
        self.build = build
        self.parameters = parameters
        self.inputs = inputs
        self.outputs = outputs


class RunValidatorHeraRun(RunValidator):
    """RunValidatorHeraRun validator."""

    # Workflow parameters
    source: dict = None
    build: dict = None

    # Run parameters
    parameters: dict = None

    # NOT USED
    inputs: dict = None
    outputs: dict = None
