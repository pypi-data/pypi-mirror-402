import logging
import threading
from datetime import datetime
from airflow.listeners import hookimpl
from dag_cost_tracker.cost_calculator import CostCalculator
from dag_cost_tracker.db import get_session
from dag_cost_tracker.models import DagRun, TaskCost

logger = logging.getLogger(__name__)

def _save_task_cost(task_instance, start_date, end_date):
    """
    Background worker to calculate and save cost to DB.
    Run in a separate thread to avoid blocking Airflow.
    """
    try:
        if not start_date or not end_date:
            logger.warning("Task instance missing start or end date. Skipping cost tracking.")
            return

        duration = (end_date - start_date).total_seconds()
        
        # Extract metadata
        dag_id = task_instance.dag_id
        run_id = task_instance.run_id
        task_id = task_instance.task_id
        execution_date = task_instance.execution_date
        
        # Attempt to get warehouse from task params or operator
        # This depends on how users define it. We'll look for 'warehouse' in params first.
        warehouse_name = None
        if hasattr(task_instance, 'executor_config') and task_instance.executor_config:
             warehouse_name = task_instance.executor_config.get("warehouse")
        
        # If not in executor_config, check if the operator has a 'warehouse' attribute (e.g. SnowflakeOperator)
        if not warehouse_name and hasattr(task_instance, 'task') and hasattr(task_instance.task, 'warehouse'):
            warehouse_name = task_instance.task.warehouse

        # Calculate cost
        calculator = CostCalculator()
        cost = calculator.calculate_cost(duration, warehouse_name)

        # Database operations
        session = get_session()
        try:
            # Upsert DagRun
            dag_run = session.query(DagRun).filter_by(dag_id=dag_id, run_id=run_id).first()
            if not dag_run:
                dag_run = DagRun(
                    dag_id=dag_id,
                    run_id=run_id,
                    execution_date=execution_date,
                    total_cost=0,
                    duration_seconds=0,
                    task_count=0
                )
                session.add(dag_run)
                session.flush() # Flush to get ID

            # Update DagRun stats
            dag_run.total_cost += cost
            dag_run.duration_seconds += int(duration)
            dag_run.task_count += 1
            
            # Create TaskCost
            task_cost = TaskCost(
                dag_run_id=dag_run.id,
                task_id=task_id,
                warehouse_name=warehouse_name,
                duration_seconds=int(duration),
                cost=cost,
                start_time=start_date,
                end_time=end_date
            )
            session.add(task_cost)
            session.commit()
            logger.info(f"Recorded cost ${cost} for task {dag_id}.{task_id}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving cost data: {e}")
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Top-level error in cost tracking worker: {e}")


@hookimpl
def on_task_instance_success(previous_state, task_instance, session):
    """Called when task instance succeeds."""
    start_date = task_instance.start_date
    end_date = task_instance.end_date
    
    # Run in thread
    t = threading.Thread(target=_save_task_cost, args=(task_instance, start_date, end_date))
    t.start()

@hookimpl
def on_task_instance_failed(previous_state, task_instance, session):
    """Called when task instance fails."""
    start_date = task_instance.start_date
    end_date = task_instance.end_date
    
    # Run in thread
    t = threading.Thread(target=_save_task_cost, args=(task_instance, start_date, end_date))
    t.start()
