from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta


default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 5, 7, 0, 0), 
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
        dag_id='initialize_and_run_scripts', 
        default_args=default_args, 
        schedule_interval= '*/5 * * * *', #'@hourly',
        catchup=False, 
        is_paused_upon_creation=False
    ) as dag:

    # Task 1: Run ingestion script
    run_ingest_csv_to_pg = BashOperator(
        task_id='run_ingest_csv_to_pg',
        bash_command=
        """
            source /opt/airflow/dags/scripts/venv/bin/activate && \
            python /opt/airflow/dags/scripts/ingest_csv_to_pg.py
        """
    )

    # Task 2: Run transformation script
    run_transformation = BashOperator(
        task_id='run_transformation',
        bash_command=
        """
            source /opt/airflow/dags/scripts/venv/bin/activate && \
            python /opt/airflow/dags/scripts/transformation.py
        """
    )

    # Set task dependencies
    run_ingest_csv_to_pg >> run_transformation

