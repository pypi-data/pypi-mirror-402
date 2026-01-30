"""Run human evaluations on Control Arena settings.

This module provides the core logic for running human_cli evaluations
on any Control Arena setting.
"""

from inspect_ai import Task, eval
from inspect_ai.agent import human_cli
from inspect_ai.log import EvalLog
from inspect_ai.solver import chain
from inspect_ai.util._sandbox.docker.docker import DockerSandboxEnvironment

from control_arena import EvalMode

from human_eval.registry import get_setting, get_setting_info
from human_eval.solvers import write_test_file_only
from human_eval.transform import transform_dataset_for_human_attack


async def cleanup_docker_sandbox() -> None:
    """Clean up any lingering Docker sandbox containers and task-specific images."""
    await DockerSandboxEnvironment.cli_cleanup(id=None)


def run_human_eval(
    setting_name: str = "bashbench2",
    task_id: str | None = None,
    side_task: str | None = None,
    limit: int = 1,
    display: str = "plain",
    **setting_kwargs,
) -> list[EvalLog]:
    """Run a human evaluation on a Control Arena setting.

    Args:
        setting_name: Name of the setting (e.g., "bashbench2", "infra", "apps")
        task_id: Specific main task ID to run, or None for first available
        side_task: Specific side task to use (e.g., "disable_firewall"), or None for all
        limit: Number of tasks to run
        display: Display mode ("plain" for headless, "full" for UI)
        **setting_kwargs: Additional arguments passed to the setting constructor

    Returns:
        List of EvalLog objects from the evaluation
    """
    # 1. Get the setting and its metadata
    setting_info = get_setting_info(setting_name)

    # Build setting kwargs based on setting type
    # BashBench2 uses DatasetSpec for filtering
    if setting_name == "bashbench2":
        from control_arena.settings.bashbench2.task.dataset import DatasetSpec

        dataset_spec_kwargs = {}
        if side_task:
            dataset_spec_kwargs["side_tasks"] = [side_task]
        if task_id:
            dataset_spec_kwargs["task_id_whitelist"] = [task_id]

        if dataset_spec_kwargs:
            setting_kwargs["dataset_spec"] = DatasetSpec(**dataset_spec_kwargs)

    setting = get_setting(setting_name, **setting_kwargs)

    # 2. Load dataset in ATTACK mode (includes side task metadata)
    dataset = setting.get_dataset(EvalMode.ATTACK)

    # 3. Filter to specific task if provided (for non-BashBench2 settings)
    #    BashBench2 uses DatasetSpec for filtering, others filter here
    if task_id and setting_name != "bashbench2":
        # Convert both to string for comparison (sample.id can be int or str)
        dataset = [s for s in dataset if str(s.id) == str(task_id)]
        if not dataset:
            raise ValueError(f"Task {task_id} not found in {setting_name}")

    # 4. Transform samples so human sees both main + side task
    human_dataset = transform_dataset_for_human_attack(dataset)

    # 5. Build solver chain
    #    - setup_environment() may return None (no setup needed) or a Solver
    #    - human_cli() connects human to container
    #    - chain() runs them sequentially
    #
    # Special handling for Bash setting:
    #   The upstream add_test_file() solver writes the test file AND runs pytest,
    #   which produces noise before the human connects. But we can't skip setup
    #   entirely because AI agents have a run_tests() tool - for scoring parity,
    #   humans need the test file to exist. We use write_test_file_only() which
    #   writes the file without executing tests.
    #   See docs/scoring-parity.md for full analysis.
    solvers = []
    if setting_name == "bash":
        # Bash: use custom solver that writes test file without running tests
        solvers.append(write_test_file_only())
    elif not setting_info.skip_setup:
        # Other settings: use upstream setup_environment() if available
        env_setup = setting.setup_environment()
        if env_setup is not None:
            solvers.append(env_setup)
    solvers.append(
        human_cli(answer=False)
    )  # answer=False: score by checking state, not explicit answer
    solver = chain(solvers)

    # 6. Create the Inspect Task
    task = Task(
        dataset=human_dataset,
        solver=solver,
        scorer=setting.get_scorers(),
        sandbox=setting.get_sandbox_config(),
        name=f"{setting_name}_human_attack",
    )

    # 7. Run evaluation with cleanup on completion
    try:
        logs = eval(task, limit=limit, display=display)
    finally:
        # Always cleanup Docker containers and task-specific images
        import anyio
        from inspect_ai._util._async import configured_async_backend

        anyio.run(cleanup_docker_sandbox, backend=configured_async_backend())

    return logs
