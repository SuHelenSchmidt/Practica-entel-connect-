from google.cloud import bigquery

def create_table(table_id:str):
# Construct a BigQuery client object.
    client = bigquery.Client()
    # table_id = "your-project.your_dataset.your_table_name"
    dataset_id = get_dataset_id_from_table_id(table_id)
    print(f"dataset_id: {dataset_id}")
    try:
        dataset = client.get_dataset(dataset_id)  # Make an API request.
        print("Dataset {} already exists.".format(dataset_id))
    except Exception as e:
        dataset = bigquery.Dataset(dataset_id)  # Make an API request.
        dataset = client.create_dataset(dataset)  # Make an API request.
        print("Created dataset {}.{}".format(dataset.project, dataset.dataset_id))

    schema = [
        
        bigquery.SchemaField("nombre_cliente", "STRING"),
        bigquery.SchemaField("rut_cliente", "STRING"),
        bigquery.SchemaField("nombre_agente", "STRING"),
        bigquery.SchemaField("duracion_llamada", "STRING"),
        bigquery.SchemaField("transcripcion", "STRING")
]

    try:
        table = client.get_table(table_id)  # Make an API request.
    except Exception as e:

        table = bigquery.Table(table_id, schema=schema)
        table = client.create_table(table)  # Make an API request.
        print(
            "Created table {}.{}.{}".format(table.project, table.dataset_id, table.table_id)
        )


    

def get_dataset_id_from_table_id(table_id):
    """
    Extracts the dataset ID from a table ID.

    Args:
        table_id (str): The table ID in the format "project.dataset.table".

    Returns:
        str: The dataset ID.
    """

    # Split the table ID into its components.
    project_id, dataset_id, table_id = table_id.split(".")

    # Return the dataset ID.
    return (project_id + "." + dataset_id)