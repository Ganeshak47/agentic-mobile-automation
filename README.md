# Agentic AI — Mobile Automation Framework

A demo framework showing how **Agentic AI** drives **mobile test automation**.
Instead of hand-coding locators and steps, you describe a test goal in plain
English; an LLM agent generates the executable steps, and the framework runs
them on a real device/emulator via **Appium**. When a locator breaks, the agent
**self-heals** it at runtime from the live UI hierarchy.

App under test: the open-source **Wikipedia Android app** (license-free, public).

---

## Why "Agentic"?

A traditional automation script is static — every tap, every locator is written
by a human and breaks the moment the UI changes. Here the AI acts as an *agent*
in two ways:

1. **Test generation** — it reasons about a goal ("search for X and verify the
   article opens") and produces structured, runnable steps.
2. **Self-healing** — at runtime, when an element isn't found, it inspects the
   current screen's XML and proposes a corrected locator, then retries.

The human supplies *intent*; the agent supplies *implementation*.

---

## Architecture

```
            ┌──────────────────────────────────────────────┐
            │              Natural-language goal             │
            └───────────────────────┬──────────────────────┘
                                    │
                       ┌────────────▼────────────┐
                       │   MobileTestAgent (LLM)  │
                       │  • generate_test_steps   │
                       │  • heal_locator          │
                       └────────────┬─────────────┘
                                    │ JSON steps
                       ┌────────────▼────────────┐
                       │      StepExecutor        │
                       │  tap / input / verify    │
                       │  + self-healing retry    │
                       └────────────┬─────────────┘
                                    │ Appium commands
                       ┌────────────▼────────────┐
                       │   Appium (UiAutomator2)  │
                       │   Android emulator/device│
                       └──────────────────────────┘
```

### Components

| Layer | File | Responsibility |
|-------|------|----------------|
| Agent | `src/agent/agent.py` | Goal → JSON steps; broken locator → fixed locator |
| Driver | `src/framework/driver_factory.py` | Builds Appium capabilities from config + env |
| Executor | `src/framework/executor.py` | Runs steps, performs self-healing |
| Runner | `run_demo.py` | CLI end-to-end demo |
| Tests | `tests/test_agentic_flows.py` | Pytest cases authored as goals |

---

## Prerequisites

- Python 3.11+
- Node.js + Appium 2.x server (`npm i -g appium && appium driver install uiautomator2`)
- Android SDK + an emulator (or a connected device)
- An Anthropic API key
- The Wikipedia APK in `./apps/wikipedia.apk` (or installed on the device)

---

## Setup

```bash
git clone https://github.com/<you>/agentic-mobile-automation.git
cd agentic-mobile-automation

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # then edit .env with your API key + device info
```

Start the Appium server and emulator in separate terminals:

```bash
appium                       # terminal 1
emulator -avd Pixel_API_33   # terminal 2
```

---

## Run the demo

```bash
python run_demo.py "Search Wikipedia for 'Artificial intelligence' and verify the article opens"
```

You'll see the agent print the generated steps, then watch them execute on the
device. Generated steps are saved to `generated/` so they can be reviewed or
replayed.

## Run the test suite

```bash
pytest                       # full suite -> report.html
pytest tests/test_agentic_flows.py::test_agent_generates_valid_schema   # no device needed
```

---

## How a test case is created (the demo highlight)

Old way:
```python
driver.find_element(AppiumBy.ID, "org.wikipedia:id/search_container").click()
driver.find_element(AppiumBy.ID, "org.wikipedia:id/search_src_text").send_keys("AI")
# ...brittle, manual, breaks on UI change
```

Agentic way:
```python
steps = agent.generate_test_steps(
    "Search Wikipedia for 'Artificial intelligence' and verify the article opens"
)
executor.run(steps)   # locators auto-heal if the UI shifted
```

You author tests by describing **what** to verify, not **how** to find each
widget.

---

## AI tooling insights / feedback

See [`docs/INSIGHTS.md`](docs/INSIGHTS.md) for an honest assessment of what
worked, what didn't, and where agentic approaches help vs. hurt in mobile
automation.

---

## Project layout

```
agentic-mobile-automation/
├── run_demo.py
├── requirements.txt
├── pytest.ini
├── .env.example
├── config/config.yaml
├── src/
│   ├── agent/agent.py
│   └── framework/{driver_factory.py, executor.py}
├── tests/{conftest.py, test_agentic_flows.py}
├── docs/{INSIGHTS.md, DEMO_SCRIPT.md}
└── .github/workflows/ci.yml
```

## License

MIT — for demo/educational use.
