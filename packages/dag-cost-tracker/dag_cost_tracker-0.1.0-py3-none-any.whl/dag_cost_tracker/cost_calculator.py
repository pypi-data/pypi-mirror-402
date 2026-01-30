from dag_cost_tracker.config import load_config, get_warehouse_pricing

class CostCalculator:
    def __init__(self, config=None):
        self.config = config or load_config()

    def calculate_cost(self, duration_seconds, warehouse_name=None):
        """
        Calculate cost based on duration and warehouse pricing.
         Formula: (duration / 3600) * credits_per_hour * cost_per_credit
        """
        if duration_seconds is None or duration_seconds < 0:
            return 0.0

        wh_name = warehouse_name or "default"
        pricing = get_warehouse_pricing(self.config, wh_name)

        if not pricing:
            # If no pricing found and no default, assume 0 cost (or log warning)
            return 0.0

        credits_per_hour = pricing.get("credits_per_hour", 0)
        cost_per_credit = pricing.get("cost_per_credit", 0)

        hours = duration_seconds / 3600.0
        cost = hours * credits_per_hour * cost_per_credit
        return round(cost, 4)
