import pytest
from src.agent import MobileTestAgent
from src.framework import create_driver, StepExecutor


@pytest.fixture(scope="session")
def agent():
    return MobileTestAgent()


@pytest.fixture
def mobile(agent):
    driver, cfg = create_driver()
    executor = StepExecutor(driver, cfg, agent)
    yield agent, executor, driver
    driver.quit()
