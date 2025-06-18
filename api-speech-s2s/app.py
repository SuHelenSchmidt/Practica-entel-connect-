import os
import json
import uuid
import threading
from datetime import datetime
from google.cloud import bigquery
from flask import Flask, request, jsonify, Response
from modules.logger_config import logger
from modules.audio_list import get_files
from modules.extraction_from_audio import run_extract_entities_from_audio
from Test import test_sftp, test_auth
from modules.sftp_to_gcs import transfer_files_sftp_to_gcs
from google.oauth2 import service_account
from concurrent.futures import ThreadPoolExecutor, as_completed

# -- CREDENCIALES --
# Crear la instancia de la aplicación Flask
app = Flask(__name__)

# credentials = service_account.Credentials.from_service_account_file(r"d:\ECC\Proyectos\BANCO_RIPLEY\api-speech-s2s\credential\speech-s2s-927193d16d57.json")
# credentials = service_account.Credentials.from_service_account_file(r"c:\Desarrollo\Proyectos\bcoripley\api-speech-s2s\credential\speech-s2s-927193d16d57.json")
# credentials = service_account.Credentials.from_service_account_file(r"c:\Users\Practicante\dev\api-speech-s2s\credential\speech-s2s-927193d16d57.json")
credentials = service_account.Credentials.from_service_account_file(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
client = bigquery.Client(credentials=credentials, project="speech-s2s")
table_ejecucion_id = 'speech-s2s.bancoripley.ejecucion_procesos_audios'

# -- FUNCIONES --

def strip_json(string_to_strip: str) -> dict:
    """Limpia y convierte un string JSON en un diccionario."""
    if not string_to_strip.strip():  # Verificar si el string está vacío
        logger.error("El string JSON proporcionado está vacío o no es válido.")
        raise ValueError("El string JSON proporcionado está vacío o no es válido.")

    cleaned_json = string_to_strip.rstrip().rstrip('```').lstrip().lstrip('```json')
    try:
        data = json.loads(cleaned_json)
        logger.info("El JSON ha sido parseado correctamente.")
    except json.JSONDecodeError as e:
        logger.error("Error al decodificar el JSON: %s", e)
        raise
    return data

def log_error_to_bigquery(cliente, nombre_error: str, proceso_fallido: str):
    """Registra el error en la tabla de BigQuery "errores_procesos"""
    error_data = [{
        "nombre_error": nombre_error,
        "fecha_hora_error": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "proceso_fallido": proceso_fallido
    }]
    table_id = "speech-s2s.bancoripley.errores_procesos"
    try:
        errors = cliente.insert_rows_json(table_id, error_data)
        if errors:
            logger.error("Error al registrar datos a BigQuery: %s", nombre_error)
        else:
            logger.info("Error registrado en BigQuery: %s", nombre_error)
    except Exception as e:
        logger.critical("Error crítico al insertar datos a BigQuery: %s", e)

def process_audio(file_info, bucket_name, table_id, process_id, idx, total_files):
    ruta_archivo = file_info.get('ruta_archivo')
    if not ruta_archivo:
        logger.error("El archivo %s no tiene una ruta válida.", ruta_archivo)
        log_error_to_bigquery(client, f"El archivo {ruta_archivo} no tiene una ruta válida.", "Procesamiento de audios")
        return None

    logger.info("Procesando audio %s/%s: %s", idx, total_files, ruta_archivo)
    try:
        gemini_output = run_extract_entities_from_audio(ruta_archivo, bucket_name)
        json_gemini = json.loads(gemini_output)

        if "error" in json_gemini:
            logger.error("Error en el modelo para %s:%s", ruta_archivo, json_gemini['error'])
            log_error_to_bigquery(client, f"Error en el modelo para {ruta_archivo}:{json_gemini['error']}", f"Procesamiento audio {ruta_archivo}")
            return None

        return json_gemini
    except Exception as e:
        logger.error("Error procesando el audio %s:%s", ruta_archivo, repr(e))
        log_error_to_bigquery(client, f"Error procesando el audio {ruta_archivo}:{repr(e)}", f"Procesamiento de audio {ruta_archivo}")
        return None

def process_audios_and_upload_to_bigquery(dateFolder, process_id):
    """Procesa audios desde una carpeta específica en un bucket de GCS y sube datos procesados a BigQuery."""
    # Generar el nombre de la carpeta en base a la fecha actual

    #Cambio temporal de variable "today".
    #today= "02_02_2025"
    estado = 1
    try:
        target_folder = f"audios/{dateFolder}"  # Carpeta dinámica con la fecha actual

        # Filtrar archivos en la carpeta específica
        bucket_name = "speech_s2s_bucket"
        table_id = "speech-s2s.bancoripley.leads_coaching"

        logger.info("Iniciando procesamiento de audios en: %s", target_folder)
        file_list = get_files(bucket_name, prefix=target_folder)

        logger.info("Archivos encontrados en %s", target_folder)

        if not file_list:
            logger.warning("No se encontraron archivos en la carpeta: %s", target_folder)
            log_error_to_bigquery(client, f"No se encontraron archivos en la carpeta: {target_folder}", "Procesamiento de audios")
            return

        my_list = []
        continue_process = True
        try:
            query = f"""
            UPDATE `{table_ejecucion_id}`
                SET 
                    TOTAL = {len(file_list)}
                WHERE ID = '{process_id}'
            """
            query_job = client.query(query)
            query_job.result()
        except Exception as err:
            logger.error("Ocurrio un error inesperado:%s", repr(err))
            log_error_to_bigquery(client, f"Ocurrio un error inesperado:{repr(err)}", f"Ocurrio un error inesperado")
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(process_audio, file_info, bucket_name, table_id, process_id, idx, len(file_list)): file_info for idx, file_info in enumerate(file_list, start=1)}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    my_list.append(result)
                    if len(my_list) >= 5:
                        try:
                            errors = client.insert_rows_json(table_id, my_list)
                            if not errors:
                                logger.info("Datos cargados exitosamente a BigQuery.")
                            else:
                                logger.info("Errores encontrados al cargar a BigQuery: ")
                                for error in errors:
                                    logger.error(error)
                                    log_error_to_bigquery(client, str(error), "Subida a BigQuery")
                        except Exception as e:
                            logger.error("Error al subir los datos a BigQuery: %s", e)
                            log_error_to_bigquery(client, f"Error al subir los datos a BigQuery: {e}", "Subida a BigQuery")
                        my_list = []

        if my_list:
            try:
                errors = client.insert_rows_json(table_id, my_list)
                if not errors:
                    logger.info("Datos cargados exitosamente a BigQuery.")
                else:
                    logger.info("Errores encontrados al cargar a BigQuery: ")
                    for error in errors:
                        logger.error(error)
                        log_error_to_bigquery(client, str(error), "Subida a BigQuery")
            except Exception as e:
                logger.error("Error al subir los datos a BigQuery: %s", e)
                log_error_to_bigquery(client, f"Error al subir los datos a BigQuery: {e}", "Subida a BigQuery")
    except Exception as e:
        logger.error("Ocurrio un error inesperado:%s", repr(e))
        log_error_to_bigquery(client, f"Ocurrio un error inesperado:{repr(e)}", f"Ocurrio un error inesperado")
        estado = 2
    if estado != 3:
        try:
            query = f"""
            UPDATE `{table_ejecucion_id}`
                SET 
                    ESTADO = {estado}, 
                    FECHA_FIN = '{datetime.now().isoformat()}'
                WHERE ID = '{process_id}'
            """
            query_job = client.query(query)
            query_job.result()
        except Exception as err:
            logger.error("Ocurrio un error inesperado:%s", repr(err))
            log_error_to_bigquery(client, f"Ocurrio un error inesperado:{repr(err)}", f"Ocurrio un error inesperado")
        
def check_process_and_start(dateFolder):
    """Procesa audios desde una carpeta específica en un bucket de GCS y sube datos procesados a BigQuery."""
    # Generar el nombre de la carpeta en base a la fecha actual

    #Cambio temporal de variable "today".
    #today= "02_02_2025"
    result = None
    process_id = str(uuid.uuid4())
    try:
        query = f"""
            SELECT ID 
            FROM {table_ejecucion_id}
            WHERE ESTADO = 0
        """
        query_job = client.query(query)
        rows = query_job.result()
        first_row = next(iter(rows), None)
        if first_row:
            result = { "mensaje": "Ya existe un proceso en curso" }
        else:
            row = {
                "ID": process_id, 
                "FECHA_INICIO": datetime.now().isoformat(),
                "ESTADO": 0,
                "TOTAL": 0,
                "PROCESADOS": 0
            }

            # Insertar en la tabla
            load_job = client.load_table_from_json([row],table_ejecucion_id)
            load_job.result()
            result = { "mensaje": "Proceso generado correctamente", "id": process_id }
            thread = threading.Thread(target=process_audios_and_upload_to_bigquery, args=(dateFolder,process_id,))
            thread.start()
    except Exception as e:
        logger.error("Ocurrio un error inesperado:%s", repr(e))
        log_error_to_bigquery(client, f"Ocurrio un error inesperado:{repr(e)}", f"Ocurrio un error inesperado")
        result = { "mensaje": repr(e) }
        try:
            query = f"""
            UPDATE `{table_ejecucion_id}`
                SET 
                    ESTADO = 2, 
                    FECHA_FIN = '{datetime.now().isoformat()}'
                WHERE ID = '{process_id}'
            """
            query_job = client.query(query)
            query_job.result()
        except Exception as err:
            logger.error("Ocurrio un error inesperado:%s", repr(err))
            log_error_to_bigquery(client, f"Ocurrio un error inesperado:{repr(err)}", f"Ocurrio un error inesperado")
    return result

@app.route('/procesar_audios/<date>', methods=['POST'])
def procesar_audios(date):
    """Ruta que recibe un POST para procesar audios y subir a BigQuery."""
# curl -X POST http://127.0.0.1:8081/procesar_audios#
    def generate_progress(dateFolder):
        try:
            # # Etapa 1: Transferencia de archivos desde SFTP a GCS
            # yield "Iniciando transferencia de archivos desde SFTP a GCS...\n"
            # #transfer_files_and_handle_errors()  # Ejecutar transferencia de archivos
            # yield "Transferencia de archivos desde SFTP a GCS completada.\n"
            # Etapa 2: Procesamiento de audios
            result = check_process_and_start(dateFolder)
            return jsonify(result)
        except Exception as e:
            return jsonify({ "mensaje": f"Error: {str(e)}" })

    return generate_progress(date)


@app.route('/check_process/<process_id>', methods=['POST'])
def check_process(process_id):
    """Ruta que recibe un POST para consultar estado de proceso en bigquery."""
    result = None
    try:
        try:
            # # Etapa 1: Transferencia de archivos desde SFTP a GCS
            # yield "Iniciando transferencia de archivos desde SFTP a GCS...\n"
            # #transfer_files_and_handle_errors()  # Ejecutar transferencia de archivos
            # yield "Transferencia de archivos desde SFTP a GCS completada.\n"
            # Etapa 2: Procesamiento de audios
            query = f"""
                SELECT PROCESADOS, TOTAL 
                FROM {table_ejecucion_id}
                WHERE ID = '{process_id}'
            """
            query_job = client.query(query)
            rows = query_job.result()
            first_row = next(iter(rows), None)
            if first_row:
                result = { "mensaje": f"{first_row["PROCESADOS"]}/{first_row["TOTAL"]} audios procesados." }
            else:
                result = { "mensaje": "Proceso no existe" }
        except Exception as e:
            result ={ "mensaje": f"Error: {str(e)}" }
    except Exception as e:
        result =  { "mensaje": f"Error: {str(e)}" }
    
    return jsonify(result)


@app.route('/stop_process/<process_id>', methods=['POST'])
def stop_process(process_id):
    """Ruta que recibe un POST para consultar estado de proceso en bigquery."""
    result = None
    try:
        try:
            query = f"""
            UPDATE `{table_ejecucion_id}`
                SET 
                    ESTADO = 3, 
                    FECHA_FIN = '{datetime.now().isoformat()}'
                WHERE ID = '{process_id}'
            """
            query_job = client.query(query)
            query_job.result()
            result = { "mensaje": f"Proceso finalizado correctamente" }
        except Exception as err:
            logger.error("Ocurrio un error inesperado:%s", repr(err))
            log_error_to_bigquery(client, f"Ocurrio un error inesperado:{repr(err)}", f"Ocurrio un error inesperado")
            result = { "mensaje": "Ocurrio un error inesperado:{repr(err)}" }
    except Exception as e:
        result =  { "mensaje": f"Error: {str(e)}" }

    return jsonify(result)

if __name__ == '__main__':
    logger.info("Iniciando la aplicación en el puerto 8080.")
    app.run(debug=True, host='0.0.0.0', port=8080)
