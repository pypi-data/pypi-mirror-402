import os
import pytest
from dag_cost_tracker.config import load_config, get_warehouse_pricing

def test_load_config_defaults():
    config = load_config("/non/existent/path.yaml")
    assert "warehouses" in config
    assert "default" in config["warehouses"]

def test_get_warehouse_pricing_case_insensitive():
    config = {
        "warehouses": {
            "SMALL": {"val": 1}
        }
    }
    assert get_warehouse_pricing(config, "small") == {"val": 1}
    assert get_warehouse_pricing(config, "SMALL") == {"val": 1}

def test_get_warehouse_pricing_fallback():
    config = {
        "warehouses": {
            "default": {"val": 1}
        }
    }
    assert get_warehouse_pricing(config, "unknown") == {"val": 1}
