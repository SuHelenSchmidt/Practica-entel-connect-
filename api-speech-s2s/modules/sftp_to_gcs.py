import pysftp
from google.cloud import storage
import os
import datetime
from credential.sftp import sftp_credential
from google.oauth2 import service_account

# Configuración de SFTP y GCS
sftp_config = sftp_credential
bucket_name = "speech_s2s_bucket"
audio_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg']

# Configuración de opciones de conexión (omitimos la verificación de la clave)
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None  # Desactiva la verificación de la clave del host

# Inicializar cliente de GCS
# credentials = service_account.Credentials.from_service_account_file(r"d:\ECC\Proyectos\BANCO_RIPLEY\api-speech-s2s\credential\speech-s2s-927193d16d57.json")
# credentials = service_account.Credentials.from_service_account_file(r"c:\Desarrollo\Proyectos\bcoripley\api-speech-s2s\credential\speech-s2s-927193d16d57.json")
# credentials = service_account.Credentials.from_service_account_file(r"c:\Users\Practicante\dev\api-speech-s2s\credential\speech-s2s-927193d16d57.json")
credentials = service_account.Credentials.from_service_account_file(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
storage_client = storage.Client(credentials=credentials, project="speech-s2s")


def upload_to_gcs(bucket_name, folder, filename, file_data):
    """Sube un archivo a GCS desde datos en memoria, evitando duplicados."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(f"{folder}/{filename}")

    # Verificar si el archivo ya existe en GCS
    if blob.exists():
        print(f"Archivo ya existe en GCS: {folder}/{filename}")
        return  # No subir el archivo duplicado

    # Subir archivo si no existe
    blob.upload_from_string(file_data)
    print(f"Archivo subido a GCS: {folder}/{filename}")


def transfer_files_sftp_to_gcs():
    try:
        with pysftp.Connection(**sftp_config, cnopts=cnopts) as sftp:
            print("Conexión al SFTP establecida.")

            # Obtener la fecha actual para acceder a la carpeta correspondiente
            #current_date = datetime.datetime.now().strftime("%d_%m_%Y")
            current_date= "02_02_2025"
            remote_path = f"/workdir/GrabacionesECC/{current_date}"
            print(current_date)
            print(remote_path)
            # Cambiar al directorio remoto
            sftp.cwd(remote_path)
            print(f"Accediendo a la carpeta remota: {remote_path}")

            # Iterar sobre los archivos en el directorio
            for archivo in sftp.listdir():
                if any(archivo.lower().endswith(ext) for ext in audio_extensions):
                    print(f"Procesando archivo: {archivo}")

                    # Leer archivo de audio como bytes
                    with sftp.open(archivo, mode='rb') as remote_file:
                        audio_data = remote_file.read()

                    # Subir archivo de audio a GCS
                    audio_folder = f"audios/{current_date}"
                    upload_to_gcs(bucket_name, audio_folder, archivo, audio_data)

                    # Eliminar el archivo del servidor SFTP
                    sftp.remove(archivo)
                    print(f"Archivo eliminado del SFTP: {archivo}")

            # Eliminar la carpeta remota correspondiente a la fecha actual
            sftp.cwd("..")  # Subir un nivel para poder eliminar la carpeta
            sftp.rmdir(remote_path)
            print(f"Carpeta remota eliminada: {remote_path}")

            print("¡Transferencia y limpieza completa de archivos desde SFTP a GCS!")

    #except Exception as e:
        #print(f"Error durante la transferencia: {e}")

    except FileNotFoundError:
        print("❌ La carpeta no existe en SFTP")
    except PermissionError:
        print("⚠️ No tienes permisos para acceder a la carpeta en SFTP")
    except Exception as e:
        print(f"🔴 Error desconocido al acceder a la carpeta: {e}")
