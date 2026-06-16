"""
Agent-driven test cases.

Each test states a goal in plain English. The agent generates the steps at
runtime, the executor runs them with self-healing. This shows how new test
cases are authored by describing intent rather than coding locators by hand.
"""

import pytest


GOALS = [
    "Search Wikipedia for 'Artificial intelligence' and verify the article page opens",
    "Open the Wikipedia search bar and search for 'Appium', then verify results appear",
    "Navigate to the Explore feed and verify the 'In the news' section is visible",
]


@pytest.mark.parametrize("goal", GOALS)
def test_agentic_goal(mobile, goal):
    agent, executor, driver = mobile
    steps = agent.generate_test_steps(goal)
    assert isinstance(steps, list) and len(steps) > 0, "Agent produced no steps"
    executor.run(steps)


def test_agent_generates_valid_schema(agent):
    """Pure unit-style check: no device needed, validates agent output shape."""
    steps = agent.generate_test_steps(
        "Search Wikipedia for 'Python programming language'"
    )
    assert isinstance(steps, list) and steps
    for step in steps:
        assert "action" in step
        assert step["action"] in {"tap", "input", "verify", "wait"}
        if step["action"] != "wait":
            assert "strategy" in step and "locator" in step
