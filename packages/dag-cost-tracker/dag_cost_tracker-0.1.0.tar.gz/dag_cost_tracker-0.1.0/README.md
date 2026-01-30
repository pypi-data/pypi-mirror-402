# 💰 DAG Cost Tracker

![PyPI - Version](https://img.shields.io/pypi/v/dag-cost-tracker)
![Python Version](https://img.shields.io/pypi/pyversions/dag-cost-tracker)
![License](https://img.shields.io/github/license/azmatsiddique/dag-cost-tracker)

**DAG Cost Tracker** is a powerful observability and FinOps tool designed for **Apache Airflow**. It tracks execution time and compute resource usage to provide granular cost estimates for individual DAG runs, helping engineering teams optimize their data pipeline spending.

---

## 🚀 Features

- **Granular Cost Tracking**: Track costs at the DAG and task level.
- **Customizable Pricing**: Configure warehouse rates (e.g., Snowflake credits) to match your contract.
- **CLI Reporting**: Generate beautiful cost reports and inspect expensive DAGs from your terminal.
- **Seamless Integration**: Plugs directly into Airflow task hooks—no DAG code changes required.
- **Lightweight**: Stores cost history in a local SQLite database (zero external infrastructure dependencies).

## 📦 Installation

Install easily via pip:

```bash
pip install dag-cost-tracker
```

## ⚙️ Configuration

1. **Create Config File**:
   Create a `config.yaml` at `~/.dag_cost_tracker/config.yaml` to define your compute pricing.

   ```yaml
   warehouses:
     COMPUTE_WH_SMALL:
       credits_per_hour: 1
       cost_per_credit: 3.00
     COMPUTE_WH_LARGE:
       credits_per_hour: 4
       cost_per_credit: 3.00
   ```

2. **Enable Plugin**:
   The plugin auto-registers with Airflow upon installation. Restart your Airflow Scheduler and Webserver to start tracking.

## 📊 Usage

### Generate a Cost Report

See your most expensive DAGs at a glance:

```bash
dag-cost report --top 10 --period 30d
```

**Output:**
```
+-------------------+--------+--------------+----------------+
| DAG ID            |   Runs | Total Cost   | Avg Cost/Run   |
+===================+========+==============+================+
| etl_daily         |      7 | $148.66      | $21.24         |
+-------------------+--------+--------------+----------------+
| ml_training       |      7 | $115.77      | $16.54         |
+-------------------+--------+--------------+----------------+
```

### Inspect a Specific DAG

Drill down to find which tasks are driving up costs:

```bash
dag-cost inspect etl_daily
```

## 🛠️ Development

1. Clone the repository.
2. Install dependencies: `pip install -e .`
3. Run tests: `pytest`

---

## 👤 Author

**Azmat Siddique**

If you found this tool useful, consider buying me a coffee!

<a href="https://www.buymeacoffee.com/azmatsiddiz" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>
