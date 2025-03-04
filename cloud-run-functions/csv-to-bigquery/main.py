import functions_framework
from google.cloud import bigquery, pubsub_v1
import os
import json

PROJECT_ID = "famous-palisade-452223-g4"  # Project ID
DATASET_NAME = "mydataset"  #  dataset name
TABLE_NAME = "adventureworks_table"  # table name
PUBSUB_TOPIC = "trigger-airflow-dag"  #  Pub/Sub topic name

@functions_framework.cloud_event
def csv_to_bigquery(cloud_event):
    """Triggered when a CSV file is uploaded to GCS. Loads it into BigQuery and sends a Pub/Sub message."""

    file_data = cloud_event.data
    bucket_name = file_data["bucket"]
    file_name = file_data["name"]

    if not file_name.endswith(".csv"):
        print(f"Skipping non-CSV file: {file_name}")
        return

    client = bigquery.Client()
    table_id = f"{PROJECT_ID}.{DATASET_NAME}.{TABLE_NAME}"  # table reference
    uri = f"gs://{bucket_name}/{file_name}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True
    )

    print(f"Loading {file_name} into {table_id} from {uri}")
    load_job = client.load_table_from_uri(uri, table_id, job_config=job_config)
    load_job.result()

    print(f"File {file_name} successfully loaded into {table_id}.")

    # Publish message to Pub/Sub
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC)
    message_json = json.dumps({"bucket": bucket_name, "file": file_name})
    future = publisher.publish(topic_path, message_json.encode("utf-8"))
    print(f"Pub/Sub message sent: {message_json}")
