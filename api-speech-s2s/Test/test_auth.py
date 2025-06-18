from google.cloud import storage

def test_auth():
    project_id = "speech-s2s"  # Reemplaza con el ID de tu proyecto
    storage_client = storage.Client(project=project_id)  # Especifica el proyecto
    buckets = list(storage_client.list_buckets())
    print("¡Conexión exitosa a Google Cloud!")

    # print("Buckets disponibles:")
    # for bucket in buckets:
    #     print(bucket.name)
