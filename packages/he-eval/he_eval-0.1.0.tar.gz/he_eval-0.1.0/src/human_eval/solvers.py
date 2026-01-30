"""Custom solvers for human evaluation.

This module contains solvers that adapt Control Arena settings for human evaluation,
addressing cases where upstream solvers have behaviors unsuitable for human use.
"""

from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.util import sandbox


@solver
def write_test_file_only() -> Solver:
    """Write test file to sandbox without executing tests.

    This solver is a human-eval-specific replacement for the Bash setting's
    `add_test_file()` solver. The upstream solver writes the test file AND
    immediately runs pytest, which is problematic for human evaluation:

    1. Running tests during setup produces noise before the human connects
    2. The tests will fail (task not yet completed), showing confusing output
    3. It affects timing measurements

    However, we can't simply skip setup entirely (skip_setup=True) because
    that breaks scoring parity. The AI agent has access to a `run_tests()`
    tool that runs pytest against `test_task.py`. For fair comparison,
    humans need the test file to exist so they can run `pytest test_task.py`
    manually.

    This solver writes the test file without executing it, giving humans
    the same verification capability as AI agents.

    See docs/scoring-parity.md for the full parity analysis.

    Returns:
        A solver that writes test_task.py to the sandbox.
    """
    from control_arena.settings.bash.task.dataset import BashTask

    async def solve(state: TaskState, _generate: Generate) -> TaskState:
        metadata = state.metadata_as(BashTask)
        verifiable_code = metadata.task_verifiable
        await sandbox().write_file("test_task.py", verifiable_code)
        return state

    return solve
