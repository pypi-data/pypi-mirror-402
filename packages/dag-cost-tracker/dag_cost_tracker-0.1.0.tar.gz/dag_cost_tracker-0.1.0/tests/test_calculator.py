from dag_cost_tracker.cost_calculator import CostCalculator

def test_calculate_cost_simple():
    config = {
        "warehouses": {
            "default": {"credits_per_hour": 1, "cost_per_credit": 10}
        }
    }
    calc = CostCalculator(config=config)
    
    # 3600 seconds = 1 hour. 1 credit/hr * 10 $/credit = $10
    assert calc.calculate_cost(3600) == 10.0

def test_calculate_cost_custom_warehouse():
    config = {
        "warehouses": {
            "large": {"credits_per_hour": 2, "cost_per_credit": 5}
        }
    }
    calc = CostCalculator(config=config)
    
    # 1800 seconds = 0.5 hours. 2 credits/hr * 0.5 hr * 5 $/credit = $5
    assert calc.calculate_cost(1800, "large") == 5.0

def test_calculate_cost_missing_warehouse_returns_zero():
    config = {"warehouses": {}}
    calc = CostCalculator(config=config)
    assert calc.calculate_cost(3600, "missing") == 0.0
