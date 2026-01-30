"""
Test: Run a Control Arena task with human_cli.

This script demonstrates how to run BashBench2 tasks with a human agent
in ATTACK mode, where the human sees both the main task and side task.

Run with:
    uv run python test_human_ca.py
"""

import traceback

from inspect_ai import Task, eval
from inspect_ai.agent import human_cli
from inspect_ai.solver import chain

from control_arena import EvalMode
from control_arena.settings.bashbench2.bb2_setting import BashBench2Setting

from human_eval.transform import transform_dataset_for_human_attack


def run_human_eval():
    """
    Run a BashBench2 task with human_cli in ATTACK mode.

    The human sees both:
    1. The main task (legitimate work)
    2. The side task (covert objective)

    After completion, scorers evaluate both main task success and side task success.
    """
    # 1. Create the setting
    setting = BashBench2Setting()

    # 2. Load dataset in ATTACK mode (includes side task metadata)
    dataset = setting.get_dataset(EvalMode.ATTACK)

    # 3. Transform samples so human sees both main + side task
    human_dataset = transform_dataset_for_human_attack(dataset)

    # 4. Build solver: setup_environment runs setup scripts, then human_cli takes over
    #    - setup_environment() builds Docker image and returns a solver that runs setup scripts
    #    - human_cli() connects human to container and waits for "task submit"
    #    - chain() runs them sequentially (filtering out None if setup_environment returns nothing)
    solver = chain(
        [
            s
            for s in [
                setting.setup_environment(),  # May return None for some settings
                human_cli(
                    answer=False
                ),  # answer=False: BashBench2 scores by running tests
            ]
            if s is not None
        ]
    )

    # 5. Create the Inspect Task
    task = Task(
        dataset=human_dataset,
        solver=solver,
        scorer=setting.get_scorers(),  # main_task_success + side_task scorer
        sandbox=setting.get_sandbox_config(),  # None for BashBench2 (sandbox is per-sample)
        name="bashbench2_human_attack",
    )

    # 6. Run evaluation
    #    - limit=1: only run one task
    #    - display="plain": headless mode, prints docker exec command instead of UI
    eval(task, limit=1, display="plain")


if __name__ == "__main__":
    try:
        run_human_eval()
    except Exception:
        print("\n" + "=" * 60)
        print("ERROR:")
        print("=" * 60)
        traceback.print_exc()
        print("=" * 60)
        raise
