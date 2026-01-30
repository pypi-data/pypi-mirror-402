from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

Base = declarative_base()

class DagRun(Base):
    __tablename__ = 'dag_runs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    dag_id = Column(String, nullable=False, index=True)
    run_id = Column(String, nullable=False)
    execution_date = Column(DateTime, nullable=False, index=True)
    total_cost = Column(Float, default=0.0)
    duration_seconds = Column(Integer, default=0)
    task_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint('dag_id', 'run_id', name='_dag_run_uc'),)

    task_costs = relationship("TaskCost", back_populates="dag_run", cascade="all, delete-orphan")

class TaskCost(Base):
    __tablename__ = 'task_costs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    dag_run_id = Column(Integer, ForeignKey('dag_runs.id'), nullable=False, index=True)
    task_id = Column(String, nullable=False)
    warehouse_name = Column(String)
    duration_seconds = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    dag_run = relationship("DagRun", back_populates="task_costs")
