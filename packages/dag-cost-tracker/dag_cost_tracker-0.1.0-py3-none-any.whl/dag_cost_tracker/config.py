import os
import yaml
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.dag_cost_tracker/config.yaml")

DEFAULT_CONFIG = {
    "warehouses": {
        "default": {
            "credits_per_hour": 1,
            "cost_per_credit": 2.5
        }
    }
}

def load_config(path=None):
    """Load configuration from YAML file."""
    config_path = path or DEFAULT_CONFIG_PATH
    
    if not os.path.exists(config_path):
        logger.warning(f"Config file not found at {config_path}. Using defaults.")
        return DEFAULT_CONFIG

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            if not config:
                return DEFAULT_CONFIG
            
            # Basic validation
            if "warehouses" not in config:
                logger.error("Invalid config: 'warehouses' key missing. Using defaults.")
                return DEFAULT_CONFIG
                
            return config
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return DEFAULT_CONFIG

def get_warehouse_pricing(config, warehouse_name):
    """Get pricing details for a specific warehouse."""
    warehouses = config.get("warehouses", {})
    # Case insensitive lookup
    for name, pricing in warehouses.items():
        if name.lower() == warehouse_name.lower():
            return pricing
            
    # Fallback to default if available
    if "default" in warehouses:
        return warehouses["default"]
        
    return None
