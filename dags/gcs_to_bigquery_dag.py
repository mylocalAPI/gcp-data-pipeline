from airflow import DAG
from airflow.providers.google.cloud.operators.pubsub import PubSubPullOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import json

# DAG Configuration
DEFAULT_ARGS = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 2, 28),  # Adjust to the current date
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# ✅ Updated with your details
GCP_PROJECT_ID = "famous-palisade-452223-g4"
BUCKET_NAME = "adevntureworkbucket"  # Fixed spelling mistake
DATASET_NAME = "mydataset"
TABLE_NAME = "adventureworks_table"
PUBSUB_SUBSCRIPTION = "trigger-airflow-sub"

def extract_filename_from_pubsub(**kwargs):
    """Extracts the filename from the Pub/Sub message."""
    ti = kwargs["ti"]
    messages = ti.xcom_pull(task_ids="wait_for_pubsub_message")  # Get message from previous task
    
    if messages and isinstance(messages, list) and len(messages) > 0:
        message_data = json.loads(messages[0]['message']['data'])  # Decode message data
        file_name = message_data["name"]  # Extract file name from message
        print(f"Extracted File Name: {file_name}")
        return file_name  # Pass the filename to next tasks
    else:
        raise ValueError("No Pub/Sub messages received")

with DAG(
    dag_id="gcs_to_bigquery_dag",
    default_args=DEFAULT_ARGS,
    schedule_interval=None,  # ✅ No fixed schedule, triggered by Pub/Sub
    catchup=False
) as dag:

    # ✅ Step 1: Wait for a Pub/Sub message
    wait_for_pubsub_message = PubSubPullOperator(
        task_id="wait_for_pubsub_message",
        project_id=GCP_PROJECT_ID,
        subscription=PUBSUB_SUBSCRIPTION,
        max_messages=1,
        ack_messages=True,
    )

    # ✅ Step 2: Extract file name from Pub/Sub message
    extract_file_name = PythonOperator(
        task_id="extract_file_name",
        python_callable=extract_filename_from_pubsub,
        provide_context=True
    )

    # ✅ Step 3: Load CSV into BigQuery dynamically
    load_csv_to_bigquery = GCSToBigQueryOperator(
        task_id="load_csv_to_bigquery",
        bucket=BUCKET_NAME,
        source_objects=["{{ task_instance.xcom_pull(task_ids='extract_file_name') }}"],  # Dynamic file name
        destination_project_dataset_table=f"{GCP_PROJECT_ID}.{DATASET_NAME}.{TABLE_NAME}",
        source_format="CSV",
        skip_leading_rows=1,
        autodetect=True,
        write_disposition="WRITE_APPEND",
    )

    # ✅ Define Task Dependencies
    wait_for_pubsub_message >> extract_file_name >> load_csv_to_bigquery
