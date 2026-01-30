from setuptools import setup, find_packages

setup(
    name="dag-cost-tracker",
    version="0.1.0",
    description="A DAG cost tracking plugin for Apache Airflow",
    author="Azmat Siddique",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "apache-airflow>=2.0.0",
        "SQLAlchemy>=1.3.0,<2.0.0",
        "PyYAML>=5.1",
        "click>=7.0",
        "tabulate>=0.8.0",
    ],
    entry_points={
        "console_scripts": [
            "dag-cost=dag_cost_tracker.cli:cli",
        ],
        "airflow.plugins": [
            "dag_cost_tracker=dag_cost_tracker.plugin:DagCostTrackerPlugin",
        ],
    },
)
