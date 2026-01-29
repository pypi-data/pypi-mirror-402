import csv
from google.cloud import bigquery

class PiExporter:
    @staticmethod
    def to_csv(data, filename):
        if not data:
            print("No data to export.")
            return
        
        if not filename.endswith('.csv'):
            filename += '.csv'
            
        keys = data[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
        print(f"Successfully saved {len(data)} rows to {filename}")

    @staticmethod
    def to_bigquery(data, project_id, dataset_id, table_id):
        if not data:
            print("No data to upload.")
            return

        client = bigquery.Client(project=project_id)
        table_ref = f"{project_id}.{dataset_id}.{table_id}"
        
        print(f"Uploading {len(data)} rows to BigQuery table {table_ref}...")
        
        # Auto-detect schema is usually fine for JSON inserts, 
        # but explicit schema is safer. For generic use, we try auto-detect first.
        job_config = bigquery.LoadJobConfig(
            autodetect=True,
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND
        )

        try:
            # --- CHANGE STARTED HERE ---
            # Old Code (Caused SSL Error):
            # errors = client.insert_rows_json(table_ref, data)
            
            # New Code (Uses Batch Load + your job_config):
            job = client.load_table_from_json(
                data, 
                table_ref, 
                job_config=job_config
            )
            
            # Wait for the job to complete (this is required for batch loads)
            job.result() 
            
            print(f"Upload successful. Loaded {job.output_rows} rows.")
            # --- CHANGE ENDED HERE ---

        except Exception as e:
            print(f"BigQuery Upload Failed: {e}")
            # Optional: Print detailed error list if available in exception
            if hasattr(e, 'errors'):
                print(e.errors)