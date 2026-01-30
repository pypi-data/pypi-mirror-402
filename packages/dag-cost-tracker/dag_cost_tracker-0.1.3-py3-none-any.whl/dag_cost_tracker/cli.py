import click
import logging
from datetime import datetime, timedelta, timezone
from tabulate import tabulate
from sqlalchemy import desc
from dag_cost_tracker.db import init_db, get_session
from dag_cost_tracker.models import DagRun, TaskCost

@click.group()
def cli():
    """DAG Cost Tracker CLI"""
    # Initialize DB (safe to run usually)
    init_db()

@cli.command()
@click.option('--top', default=10, help='Show top N most expensive DAGs')
@click.option('--period', default='7d', help='Time period (e.g. 7d, 30d)')
@click.option('--format', type=click.Choice(['table', 'csv']), default='table', help='Output format')
def report(top, period, format):
    """Generate a cost report."""
    session = get_session()
    
    # Parse period
    days = 7
    if period.endswith('d'):
        try:
            days = int(period[:-1])
        except ValueError:
            pass
    
    since_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    try:
        # Group by DAG ID and sum cost
        # Logic: select dag_id, sum(total_cost), count(*) from dag_runs where execution_date > since group by dag_id 
        # SQLAlchemy group by
        from sqlalchemy import func
        
        results = session.query(
            DagRun.dag_id,
            func.sum(DagRun.total_cost).label('total_cost'),
            func.count(DagRun.id).label('run_count'),
            func.avg(DagRun.total_cost).label('avg_cost')
        ).filter(
            DagRun.execution_date >= since_date
        ).group_by(
            DagRun.dag_id
        ).order_by(
            desc('total_cost')
        ).limit(top).all()
        
        data = []
        for r in results:
            data.append([
                r.dag_id,
                r.run_count,
                f"${r.total_cost:.2f}",
                f"${r.avg_cost:.2f}"
            ])
            
        headers = ["DAG ID", "Runs", "Total Cost", "Avg Cost/Run"]
        
        if format == 'table':
            click.echo(f"Top {top} Expensive DAGs (Last {days} days)")
            click.echo(tabulate(data, headers=headers, tablefmt="grid"))
        elif format == 'csv':
            import csv
            import sys
            writer = csv.writer(sys.stdout)
            writer.writerow(headers)
            writer.writerows(data)
            
    except Exception as e:
        click.echo(f"Error generating report: {e}", err=True)
    finally:
        session.close()

@cli.command()
@click.argument('dag_id')
def inspect(dag_id):
    """Inspect costs for a specific DAG."""
    session = get_session()
    try:
        # Get recent runs
        runs = session.query(DagRun).filter_by(dag_id=dag_id)\
            .order_by(desc(DagRun.execution_date)).limit(10).all()
            
        if not runs:
            click.echo(f"No runs found for DAG '{dag_id}'")
            return
            
        click.echo(f"Recent Runs for {dag_id}:")
        run_data = []
        for r in runs:
            run_data.append([
                r.run_id,
                r.execution_date.strftime("%Y-%m-%d %H:%M"),
                f"${r.total_cost:.4f}",
                f"{r.duration_seconds}s"
            ])
        click.echo(tabulate(run_data, headers=["Run ID", "Date", "Cost", "Duration"], tablefmt="simple"))
        
        # Breakdown by task (aggregated across these recent runs or all time? Let's do all time recent 30 days likely better but MVP can be simple)
        # Let's show most expensive tasks for this DAG in last 30 days
        since_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        from sqlalchemy import func
        task_stats = session.query(
            TaskCost.task_id,
            func.avg(TaskCost.cost).label('avg_cost'),
            func.max(TaskCost.cost).label('max_cost')
        ).join(DagRun).filter(
            DagRun.dag_id == dag_id,
            DagRun.execution_date >= since_date
        ).group_by(TaskCost.task_id).order_by(desc('avg_cost')).limit(10).all()
        
        if task_stats:
            click.echo("\nMost Expensive Tasks (Avg over last 30 days):")
            task_data = [[t.task_id, f"${t.avg_cost:.4f}", f"${t.max_cost:.4f}"] for t in task_stats]
            click.echo(tabulate(task_data, headers=["Task ID", "Avg Cost", "Max Cost"], tablefmt="simple"))

    except Exception as e:
        click.echo(f"Error inspecting DAG: {e}", err=True)
    finally:
        session.close()

if __name__ == '__main__':
    cli()
