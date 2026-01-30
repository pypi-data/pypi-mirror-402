from airflow.plugins_manager import AirflowPlugin
import dag_cost_tracker.listener

class DagCostTrackerPlugin(AirflowPlugin):
    name = "dag_cost_tracker"
    listeners = [dag_cost_tracker.listener]
