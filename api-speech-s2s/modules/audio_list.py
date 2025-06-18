from google.cloud import storage
import os
from google.oauth2 import service_account


# credentials = service_account.Credentials.from_service_account_file(r"d:\ECC\Proyectos\BANCO_RIPLEY\api-speech-s2s\credential\speech-s2s-927193d16d57.json")
# credentials = service_account.Credentials.from_service_account_file(r"c:\Desarrollo\Proyectos\bcoripley\api-speech-s2s\credential\speech-s2s-927193d16d57.json")
# credentials = service_account.Credentials.from_service_account_file(r"c:\Users\Practicante\dev\api-speech-s2s\credential\speech-s2s-927193d16d57.json")
credentials = service_account.Credentials.from_service_account_file(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

#Comentario de dev previo: esta parte es lo que debió usarse en el módulo "extraction_from_audio" en la función "run_extract_entities_from_audio".
#Por temas de tiempo no lo arreglaré, pero sería bueno incluír todo lo que se hizo en "run_extract_entities_from_audio" a este módulo para que no quede en desuso.
def extract_file_info_from_gcs(audio_filename):
    """Extrae información del nombre del archivo de audio almacenado en GCS y devuelve un diccionario."""
    parts = audio_filename.split('_')

    if len(parts) >= 7:
        return {
            "date": parts[0],  # Fecha
            "time": parts[1],  # Hora
            "skill": parts[2],  # Habilidad
            "company": parts[3],  # Compañía
            "project": parts[4],  # Proyecto
            "user_id": parts[5],  # ID de usuario
            "phone_number": parts[-1].split('.')[0],  # Número de teléfono
        }
    return None  # Si no tiene suficiente información

def get_audio_info_from_gcs(nombre_bucket, audio_filename):
    """Obtiene un archivo de audio desde GCS y extrae la información del título."""
    storage_client = storage.Client(credentials=credentials, project="speech-s2s")
    bucket = storage_client.bucket(nombre_bucket)
    blob = bucket.blob(audio_filename)

    # Verificar si el archivo existe en el bucket
    if not blob.exists():
        print(f"El archivo {audio_filename} no existe en el bucket {nombre_bucket}.")
        return None

    # Extraer la información del nombre del archivo (sin descargar el archivo completo)
    file_info = extract_file_info_from_gcs(audio_filename)

    if file_info:
        print(f"Información extraída para {audio_filename}: {file_info}")
        return file_info
    else:
        print(f"No se pudo extraer información válida del archivo {audio_filename}.")
        return None


from google.cloud import storage


def get_files(nombre_bucket: str, prefix: str = "") -> list:
    """Obtiene la lista de archivos de un bucket de GCS con un prefijo específico y extrae su información relevante."""
    cliente = storage.Client(credentials=credentials, project="speech-s2s")
    blobs = cliente.list_blobs(nombre_bucket, prefix=prefix)  # Filtra archivos por prefijo

    data_list = []

    for blob in blobs:
        full_path = blob.name
        extension = full_path.split('.')[-1].lower()

        # Verifica que sea un archivo de audio válido
        if extension in ["wav", "mp3"]:
            ruta_archivo = f"gs://{nombre_bucket}/{full_path}"

            # Extraer información del archivo
            file_info = {
                "ruta_archivo": ruta_archivo,
                "nombre_archivo": blob.name,
            }
            data_list.append(file_info)

    return data_list


