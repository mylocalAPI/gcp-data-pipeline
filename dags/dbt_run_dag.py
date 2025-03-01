from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 3, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'dbt_run_dag',
    default_args=default_args,
    description='Run dbt transformations in BigQuery',
    schedule_interval='@daily',  # Adjust as needed
)

run_dbt = BashOperator(
    task_id='run_dbt',
    bash_command='cd /home/rajashekarbathine1994/my_dbt_project && dbt run',
    dag=dag,
)

run_dbt
