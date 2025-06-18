from google.cloud import bigquery


def create_table(table_id: str):
    # Construct a BigQuery client object
    client = bigquery.Client()
    dataset_id = get_dataset_id_from_table_id(table_id)
    print(f"dataset_id: {dataset_id}")

    try:
        dataset = client.get_dataset(dataset_id)  # Check if dataset exists
        print(f"Dataset {dataset_id} already exists.")
    except Exception as e:
        dataset = bigquery.Dataset(dataset_id)
        dataset = client.create_dataset(dataset)
        print(f"Created dataset {dataset.project}.{dataset.dataset_id}")

    schema = [
        # Leads fields
        bigquery.SchemaField("Contexto", "STRING"),
        bigquery.SchemaField("Nombrecliente", "STRING"),
        bigquery.SchemaField("ExisteOfrecimiento", "BOOLEAN"),
        bigquery.SchemaField("Oferta", "STRING"),
        bigquery.SchemaField("PodriamosOfrecerSimilar", "BOOLEAN"),
        bigquery.SchemaField("EsUnPotencialClienteParaOfertar", "STRING"),
        bigquery.SchemaField("MotivoDeLlamada", "STRING"),
        bigquery.SchemaField("SentimientoInicial", "STRING"),
        bigquery.SchemaField("SentimientoFinal", "STRING"),
        bigquery.SchemaField("DuracionDeLaLlamada", "STRING"),

        #Data del titulo del audio
        bigquery.SchemaField("FechaHora", "STRING"),
        bigquery.SchemaField("Habilidad", "STRING"),
        bigquery.SchemaField("ConndID", "STRING"),
        bigquery.SchemaField("LoginAgente", "STRING"),
        bigquery.SchemaField("Telefono", "STRING"),

        # Coaching fields
        bigquery.SchemaField("Tipificacion", "STRING"),
        bigquery.SchemaField("Realizado", "STRING", mode="REPEATED"),
        bigquery.SchemaField("PorHacer", "STRING", mode="REPEATED")
    ]

    try:
        table = client.get_table(table_id)
        print(f"Table {table_id} already exists.")
    except Exception as e:
        table = bigquery.Table(table_id, schema=schema)
        table = client.create_table(table)
        print(f"Created table {table.project}.{table.dataset_id}.{table.table_id}")


def get_dataset_id_from_table_id(table_id):
    """
    Extracts the dataset ID from a table ID.
    Args:
        table_id (str): The table ID in the format "project.dataset.table".
    Returns:
        str: The dataset ID.
    """
    project_id, dataset_id, _ = table_id.split(".")
    return f"{project_id}.{dataset_id}"