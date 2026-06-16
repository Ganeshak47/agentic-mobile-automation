"""
Agentic AI core.

Two responsibilities:
  1. Test-case generation  -> turn a plain-English goal into structured,
     executable test steps (JSON) the framework can run.
  2. Self-healing locators  -> when an element can't be found at runtime,
     hand the current screen's UI tree to the model and ask it to propose
     a working locator instead of failing the test.

The agent talks to Anthropic's Messages API. All output is constrained to
strict JSON so the framework can consume it deterministically.
"""

import os
import json
import re
from typing import List, Dict, Any, Optional

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class MobileTestAgent:
    def __init__(self, model: Optional[str] = None, temperature: float = 0.0):
        self.client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.model = model or os.environ.get("AGENT_MODEL", "claude-sonnet-4-6")
        self.temperature = temperature

    # ---------- internal helper ----------
    def _ask(self, system: str, user: str, max_tokens: int = 2000) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=self.temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in resp.content if b.type == "text")

    @staticmethod
    def _extract_json(text: str) -> Any:
        """Strip markdown fences and parse the first JSON object/array."""
        cleaned = re.sub(r"```(?:json)?", "", text).strip()
        match = re.search(r"(\[.*\]|\{.*\})", cleaned, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON found in model output:\n{text}")
        return json.loads(match.group(1))

    # ---------- 1. test generation ----------
    def generate_test_steps(self, goal: str, screen_hint: str = "") -> List[Dict[str, Any]]:
        """
        Convert a natural-language goal into executable steps.

        Each step is one of:
          {"action": "tap",   "strategy": "id|xpath|accessibility_id|text", "locator": "...", "desc": "..."}
          {"action": "input", "strategy": "...", "locator": "...", "value": "...", "desc": "..."}
          {"action": "verify","strategy": "...", "locator": "...", "desc": "..."}
          {"action": "wait",  "seconds": 2, "desc": "..."}
        """
        system = (
            "You are a senior mobile test automation engineer. "
            "You translate test goals into precise, executable Appium steps for an "
            "Android app. Respond with ONLY a JSON array of step objects. "
            "Allowed actions: tap, input, verify, wait. "
            "Allowed strategies: id, xpath, accessibility_id, text. "
            "Use resource-ids when known, otherwise text or accessibility_id. "
            "Keep steps minimal and atomic."
        )
        user = f"App: Wikipedia Android app.\nGoal: {goal}\n"
        if screen_hint:
            user += f"\nCurrent screen UI elements:\n{screen_hint}\n"
        user += "\nReturn the JSON array of steps."

        raw = self._ask(system, user)
        steps = self._extract_json(raw)
        if not isinstance(steps, list):
            raise ValueError("Expected a JSON array of steps.")
        return steps

    # ---------- 2. self-healing ----------
    def heal_locator(self, failed_step: Dict[str, Any], page_source: str) -> Optional[Dict[str, str]]:
        """
        Given a step whose locator failed and the current XML page source,
        propose a new {strategy, locator} that should match the intended element.
        Returns None if nothing plausible is found.
        """
        system = (
            "You are a self-healing locator engine for Appium/UiAutomator2. "
            "Given a failed step and the current screen's XML hierarchy, find the "
            "element the step intended to interact with and return a new locator. "
            "Respond with ONLY a JSON object: "
            '{"strategy": "id|xpath|accessibility_id|text", "locator": "...", "reason": "..."} '
            "or {} if no suitable element exists."
        )
        # Trim very large trees to stay within token budget
        trimmed = page_source[:12000]
        user = (
            f"Failed step:\n{json.dumps(failed_step)}\n\n"
            f"Current screen XML:\n{trimmed}\n\n"
            "Return the corrected locator JSON."
        )
        raw = self._ask(system, user, max_tokens=600)
        result = self._extract_json(raw)
        if isinstance(result, dict) and result.get("locator"):
            return result
        return None
