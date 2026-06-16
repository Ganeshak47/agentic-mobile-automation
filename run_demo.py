"""
End-to-end demo runner.

Usage:
    python run_demo.py "Search Wikipedia for 'Artificial intelligence' and open the article"

Flow:
    1. Agent converts the goal into JSON test steps (Agentic test generation).
    2. Framework spins up the Appium driver.
    3. Executor runs the steps, self-healing locators when needed.
    4. Generated steps are saved to ./generated/ for review & reuse.
"""

import sys
import json
import os
from datetime import datetime

from src.agent import MobileTestAgent
from src.framework import create_driver, StepExecutor


def main():
    if len(sys.argv) < 2:
        print('Usage: python run_demo.py "<natural language test goal>"')
        sys.exit(1)

    goal = sys.argv[1]
    print(f"\n=== Agentic Mobile Automation ===\nGoal: {goal}\n")

    # 1. Generate steps with the AI agent
    agent = MobileTestAgent()
    print("Generating test steps with the agent...")
    steps = agent.generate_test_steps(goal)
    print(json.dumps(steps, indent=2))

    # Persist generated steps
    os.makedirs("generated", exist_ok=True)
    fname = f"generated/steps_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(fname, "w") as f:
        json.dump({"goal": goal, "steps": steps}, f, indent=2)
    print(f"\nSaved steps -> {fname}\n")

    # 2 + 3. Drive the device
    driver, cfg = create_driver()
    try:
        executor = StepExecutor(driver, cfg, agent)
        executor.run(steps)
        print("\n PASSED")
    except Exception as e:
        if cfg["framework"].get("screenshot_on_failure", True):
            os.makedirs("screenshots", exist_ok=True)
            shot = f"screenshots/fail_{datetime.now():%Y%m%d_%H%M%S}.png"
            driver.save_screenshot(shot)
            print(f"Screenshot saved -> {shot}")
        print(f"\n FAILED: {e}")
        raise
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
