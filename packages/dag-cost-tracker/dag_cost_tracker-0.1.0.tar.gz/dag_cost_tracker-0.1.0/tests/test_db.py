from datetime import datetime, timezone
from dag_cost_tracker.models import DagRun, TaskCost

def test_dag_run_creation(session):
    dag_run = DagRun(
        dag_id="test_dag",
        run_id="run_1",
        execution_date=datetime.now(timezone.utc)
    )
    session.add(dag_run)
    session.commit()
    
    saved = session.query(DagRun).first()
    assert saved.dag_id == "test_dag"
    assert saved.total_cost == 0.0

def test_task_cost_relationship(session):
    dag_run = DagRun(
        dag_id="test_dag_2",
        run_id="run_2",
        execution_date=datetime.now(timezone.utc)
    )
    session.add(dag_run)
    session.flush()
    
    task_cost = TaskCost(
        dag_run_id=dag_run.id,
        task_id="task_1",
        duration_seconds=100,
        cost=5.0
    )
    session.add(task_cost)
    session.commit()
    
    saved_run = session.query(DagRun).filter_by(dag_id="test_dag_2").first()
    assert len(saved_run.task_costs) == 1
    assert saved_run.task_costs[0].cost == 5.0
