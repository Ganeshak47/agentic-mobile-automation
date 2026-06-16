"""Appium driver factory. Reads capabilities from config + env."""

import os
import yaml
from appium import webdriver
from appium.options.android import UiAutomator2Options
from dotenv import load_dotenv

load_dotenv()


def _load_config(path: str = "config/config.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def create_driver(config_path: str = "config/config.yaml"):
    cfg = _load_config(config_path)
    caps = dict(cfg["appium"])

    caps["deviceName"] = os.environ.get("DEVICE_NAME", "emulator-5554")
    caps["platformVersion"] = os.environ.get("PLATFORM_VERSION", "13.0")
    caps["appPackage"] = os.environ.get("APP_PACKAGE", "org.wikipedia")
    caps["appActivity"] = os.environ.get("APP_ACTIVITY", "org.wikipedia.main.MainActivity")

    app_path = os.environ.get("APP_PATH")
    if app_path and os.path.exists(app_path):
        caps["app"] = os.path.abspath(app_path)

    server = os.environ.get("APPIUM_SERVER_URL", "http://127.0.0.1:4723")
    options = UiAutomator2Options().load_capabilities(caps)

    driver = webdriver.Remote(server, options=options)
    driver.implicitly_wait(cfg["framework"].get("implicit_wait", 10))
    return driver, cfg
