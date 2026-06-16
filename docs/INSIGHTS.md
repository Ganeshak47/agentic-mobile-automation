# Insights & Feedback — Agentic AI for Mobile Automation

Honest notes from building this demo, useful for the walkthrough discussion.

## What works well

- **Intent-level authoring.** Describing a goal in English and letting the agent
  produce steps dramatically lowers the cost of writing and maintaining tests.
  Non-SDETs (BAs, manual QAs) can contribute test cases.
- **Self-healing locators.** The single biggest source of flakiness in mobile
  automation is locators breaking after UI changes. Feeding the live page source
  to the model and asking for a corrected locator recovers many of these failures
  without human intervention.
- **Readable artifacts.** Generated steps are plain JSON — reviewable, diffable,
  and replayable without re-calling the model, which keeps cost and flakiness down.

## What to watch out for

- **Non-determinism.** LLM output varies. Mitigations used here: `temperature=0`,
  strict JSON schema, and persisting generated steps so a known-good run can be
  replayed deterministically.
- **Locator quality.** The model proposes good locators only when the UI tree is
  informative. Apps with generic/duplicated resource-ids still need human hints
  (`screen_hint`).
- **Token cost & latency.** Page source can be huge; we trim to ~12k chars before
  sending. Healing on every step would be slow/expensive — we only heal on failure.
- **Verification is shallow.** "Element is displayed" is a weak oracle. Real suites
  still need explicit assertions on text/content, which the agent can be prompted
  to add.
- **Security.** Never send sensitive screen content (PII, tokens) to an external
  model without review. For regulated apps, use a self-hosted/redacted pipeline.

## Tool comparison (mobile automation + AI)

| Tool | Strength | Limitation |
|------|----------|------------|
| Appium + LLM (this repo) | Open, cross-platform, full control | You build the agent glue |
| Appium classic | Mature, free | Brittle locators, high maintenance |
| Commercial AI tools (e.g. test.ai-style, low-code) | Visual self-healing out of the box | Closed, costly, less control |
| LLM step-gen only | Fast authoring | No execution/healing without a framework |

## Recommended adoption path

1. Start with **agent-generated steps reviewed by a human** (assisted authoring).
2. Add **self-healing on failure** once you trust the locator suggestions.
3. Persist & version generated steps; replay deterministically in CI.
4. Keep the model out of the hot path for stable, high-value regression tests —
   use it for authoring and recovery, not every single run.

## Bottom line

Agentic AI is most valuable at the **edges** of automation — authoring new tests
and recovering from breakage — rather than as a real-time decision-maker inside
every test run. Used that way, it cuts maintenance significantly while keeping
runs fast and deterministic.
