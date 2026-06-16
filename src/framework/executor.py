"""
Executor: runs the JSON steps produced by the agent against a live driver.

If an element lookup fails and self_healing is enabled, it asks the agent to
propose a new locator from the current page source, then retries.
"""

import time
from typing import List, Dict, Any

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from src.agent import MobileTestAgent

_STRATEGY_MAP = {
    "id": AppiumBy.ID,
    "xpath": AppiumBy.XPATH,
    "accessibility_id": AppiumBy.ACCESSIBILITY_ID,
    "text": AppiumBy.ANDROID_UIAUTOMATOR,  # handled specially below
}


class StepExecutor:
    def __init__(self, driver, cfg: dict, agent: MobileTestAgent = None):
        self.driver = driver
        self.cfg = cfg
        self.agent = agent or MobileTestAgent()
        self.self_healing = cfg["framework"].get("self_healing", True)
        self.max_heal = cfg["framework"].get("max_heal_attempts", 2)

    # ---- locator resolution ----
    def _by_and_value(self, strategy: str, locator: str):
        if strategy == "text":
            return AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{locator}")'
        return _STRATEGY_MAP[strategy], locator

    def _find(self, step: Dict[str, Any]):
        strategy, locator = step["strategy"], step["locator"]
        by, value = self._by_and_value(strategy, locator)
        try:
            return self.driver.find_element(by, value)
        except (NoSuchElementException, TimeoutException):
            if not self.self_healing:
                raise
            return self._heal_and_find(step)

    def _heal_and_find(self, step: Dict[str, Any]):
        for attempt in range(self.max_heal):
            print(f"  [self-heal] attempt {attempt + 1} for: {step.get('desc', step)}")
            page = self.driver.page_source
            fix = self.agent.heal_locator(step, page)
            if not fix:
                continue
            print(f"  [self-heal] new locator -> {fix['strategy']}={fix['locator']} ({fix.get('reason','')})")
            by, value = self._by_and_value(fix["strategy"], fix["locator"])
            try:
                el = self.driver.find_element(by, value)
                step["strategy"], step["locator"] = fix["strategy"], fix["locator"]  # persist
                return el
            except (NoSuchElementException, TimeoutException):
                continue
        raise NoSuchElementException(
            f"Self-healing failed for step: {step.get('desc', step)}"
        )

    # ---- run ----
    def run(self, steps: List[Dict[str, Any]]):
        for i, step in enumerate(steps, 1):
            action = step["action"]
            desc = step.get("desc", action)
            print(f"Step {i}: {desc}")

            if action == "wait":
                time.sleep(step.get("seconds", 1))
                continue

            if action == "tap":
                self._find(step).click()

            elif action == "input":
                el = self._find(step)
                el.clear()
                el.send_keys(step["value"])

            elif action == "verify":
                el = self._find(step)
                assert el.is_displayed(), f"Verification failed: {desc}"

            else:
                raise ValueError(f"Unknown action: {action}")

            time.sleep(0.5)
