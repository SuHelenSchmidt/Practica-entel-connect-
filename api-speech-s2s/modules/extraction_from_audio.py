import base64
import vertexai
from vertexai.generative_models import GenerativeModel, Part
import vertexai.preview.generative_models as generative_models
import json
import os
from google.cloud import storage
from google.oauth2 import service_account
from datetime import datetime

# credentials = service_account.Credentials.from_service_account_file(r"d:\ECC\Proyectos\BANCO_RIPLEY\api-speech-s2s\credential\speech-s2s-927193d16d57.json")
# credentials = service_account.Credentials.from_service_account_file(r"c:\Desarrollo\Proyectos\bcoripley\api-speech-s2s\credential\speech-s2s-927193d16d57.json")
# credentials = service_account.Credentials.from_service_account_file(r"c:\Users\Practicante\dev\api-speech-s2s\credential\speech-s2s-927193d16d57.json")
# credentials = service_account.Credentials.from_service_account_file("d:\\ECC\\Proyectos\\BANCO_RIPLEY\\banco_ripley_audio_extraction_cloud\\speech_s2s\\credential\\speech-s2s-927193d16d57.json")
credentials = service_account.Credentials.from_service_account_file(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
vertexai.init(project="speech-s2s", location="us-central1",credentials=credentials,)

# Inicializar el modelo
model = GenerativeModel("gemini-1.5-pro-001")

safety_settings = {
    generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

generation_config = {
    "max_output_tokens": 8192,
    "temperature": 1,
    "top_p": 0.95,
}


# Prompt para el modelo
template_prompt = """
Eres un agente experto en el ofrecimiento de créditos de consumo para una marca de banco que trabaja en Chile y Perú. Dentro de tus labores principales está revisar el siguiente texto:

  {
        # Leads
        bigquery.SchemaField("Contexto", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("NombreCliente", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("ExisteOfrecimiento", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("Oferta", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("PodriamosOfrecerSimilar", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("EsUnPotencialClienteParaOfertar", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("LeadNoConcretado", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("MotivoDeLlamada", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("SentimientoInicial", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("SentimientoFinal", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("DuracionDeLaLlamada", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("CanalContacto", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("ProductoDeInteres", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("PrioridadDeContacto", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("RiesgoFinancieroCliente", "STRING", mode="NULLABLE"),
        
        # Data del título del audio
        bigquery.SchemaField("Habilidad", "STRING"),
        bigquery.SchemaField("FechaDeLlamada", "DATE"),
        bigquery.SchemaField("HoraDeLlamada", "TIME"),
        bigquery.SchemaField("ConndID", "STRING"),
        bigquery.SchemaField("Telefono", "STRING"),
        bigquery.SchemaField("LoginAgente", "STRING"),

        # Data del proceso de ejecución.
        bigquery.SchemaField("FechaDeConsulta", "DATE"),
        bigquery.SchemaField("HoraDeConsulta", "TIME")
        
        
        # Coaching
        bigquery.SchemaField("Tipificacion", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("HabilidadPersuasiva", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("ManejoDeObjeciones", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("AccionesNoRealizadas", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("RetroalimentacionPersonalizada", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("NivelSatisfaccionCliente", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("AgenteRealizaOfrecimiento", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("SpeechVentasMejorado", "STRING")
        bigquery.SchemaField("NotaDeAtencion", "INTEGER", mode="NULLABLE")
    }

Debes retornar en formato JSON los siguientes campos sin agruparlos:

- Contexto: un resumen de no más de 15 palabras de lo hablado en la llamada. El objetivo es mencionar los temas más importantes de los que necesitaba conversar el cliente con el ejecutivo.
- Nombrecliente: el nombre del cliente identificado en la conversación. El objetivo es obtener el/los nombre(s) y apellido(s) del cliente en caso de ser mencionados en la llamada.
- ExisteOfrecimiento: ¿hubo ofrecimiento de un producto o interés del cliente? Responde 1 si es un "sí" y un 0 si es un "no". Debes responer en formato integer de JSON. El objetivo es identificar si se habló de un producto/servicio de la empresa, y/o el cliente demostró interés en alguno de ellos.
- Oferta: la oferta presentada, si existe. El objetivo es identificar si el ejecutivo ofreció algún producto o servicio al cliente.
- OfertaNoDetectada: ¿el cliente solicita una oferta o hace pedido de producto que al agente no logra detectar o realizar? descríbelo.
- PodriamosOfrecerSimilar: ¿se podría ofrecer una oferta similar? Responde 1 si es un "sí" y un 0 si es un "no". Debes responer en formato integer de JSON. El objetivo es identificar si el cliente demostró alguna necesidad que puede ser cubierta por otro de nuestros servicios, por la que eventualmente podríamos notificarle.
- EsUnPotencialClienteParaOfertar: explica en 5 palabras por qué es un cliente potencial. El objetivo es identificar las necesidades que demuestra el cliente y analizarlas para determinar si podría ser un cliente potencial.
- LeadNoConcretado: ¿se identificó un lead de compra o consulta sobre algún producto que no fue atendido o concretado en la llamada? Responde 1 si es un "sí" y un 0 si es un "no". Debes responer en formato integer de JSON.
- MotivoDeLlamada: describe el motivo en 3 palabras. El objetivo es identificar el motivo por el que el cliente llamó.
- SentimientoInicial: sentimiento inicial en 1 palabra.
- SentimientoFinal: sentimiento final en 1 palabra.
- DuracionDeLaLlamada: especifica la duración de la llamada. Debe estar en formato "hora : minutos : segundos", sin dejar de ser un string.
- CanalContacto: especifica el canal utilizado para la llamada (Ej: telefónico, WhatsApp, correo electrónico).
- ProductoDeInteres: detallar si el cliente mostró interés en un producto específico. El objetivo es identificar si el cliente demostró interés por un producto en específico y decir cuál fue el producto.
- PrioridadDeContacto: ¿el cliente debería ser contactado nuevamente pronto? Responde si la prioridad de contacto es "Alta", "Media" o "Baja". El objetivo es analizar la complejidad del problema evidenciado y determinar el nivel de urgencia para realizar otra llamada al mismo cliente.
- RiesgoFinancieroCliente: evalúa si el cliente tiene un posible riesgo financiero. Responde "Alto", "Moderado" o "Bajo".
- FechaDeLlamada: <FECHADELLAMADA>
- HoraDeLlamada: <HORADELLAMADA>
- Habilidad: <HABILIDAD>
- ConndID: <CONND_ID>
- LoginAgente: <ID_AGENTE>
- Telefono: <TELEFONO>
- FechaDeConsulta: <FECHA_ACTUAL>
- HoraDeConsulta: <HORA_ACTUAL>

Debes también incluir los siguientes datos relacionados con el coaching:

- Tipificacion: describe en 2 palabras la tipificación con la que cerrarías la llamada.
- HabilidadPersuasiva: evalúa si el ejecutivo utilizó técnicas de persuasión efectivas durante la llamada. Responde si la persuasión fue "Alta", "Moderada" o "Baja". Las técnicas de persuasión efectivas para un ejecutivo de un call center de servicios financieros deben centrarse en la confianza, la claridad y la personalización.
- ManejoDeObjeciones: ¿el ejecutivo manejó adecuadamente las objeciones del cliente? Responde 1 si es un "sí" y un 0 si es un "no". Debes responer en formato integer de JSON. El ejecutivo debió demostrar respeto y responder a cada una de sus dudas, dejando al cliente satisfecho con sus respuestas.
- AccionesNoRealizadas: menciona alguna acción importante que el ejecutivo no realizó y que podría haber mejorado la interacción. 
- RetroalimentacionPersonalizada: especifica una recomendación para mejorar la próxima interacción del ejecutivo.
- NivelSatisfaccionCliente: ¿cuál es la percepción estimada del cliente respecto al servicio recibido? Responde "Alta", "Media" o "Baja". El objetivo es identificar si el cliente quedó satisfecho con lo conversado en la llamada.
- AgenteRealizaOfrecimiento: ¿el agente realiza de un ofrecimiento de manera que capture la atención del cliente? descríbelo.
- SpeechVentasMejorado: ¿cómo debería haber realizado el ofrecimiento o el speech de ventas mejorado?, debes entregar un ejemplo como si fueses el agente de como debió haber realizado el ofrecimiento mejorado
- NotaDeAtencion: determina en una escala de 0 a 5 (donde 0 es muy malo y 5 es excelente) la calificación que debería tener el agente en base a la atención realizada, según tu juicio como experto.

### Reglas para Responder
- Todas las respuestas deben ser precisas y basadas en el texto analizado. No debes imaginar datos.
- En el nodo coaching, las prácticas sugeridas deben enfocarse en mejorar estrategias de *cross-selling* y *up-selling*, además de fortalecer las habilidades de cierre del ejecutivo.
- Usa un lenguaje claro, profesional y conciso.
- Los datos deben estar en formato string solo si no se especificó como otro tipo de dato (null, integer o boolean).
- Si no hay información disponible para un campo, el valor debe ser null (sin comillas, como en JSON). No uses "null" como string.

---

### Objetivo
El objetivo de este análisis es identificar oportunidades de venta cruzada y venta adicional, evaluar la calidad de la atención y proponer estrategias de mejora en la interacción con clientes.

Todas tus respuestas deben ser precisas y no debes imaginar más allá de lo evidenciado en la llamada.
"""


def strip_json(string_to_strip: str) -> str:
    """Limpia el JSON recibido del modelo y valida que sea correcto."""
    cleaned_json = string_to_strip.strip().replace('```json', '').replace('```', '')
    try:
        data = json.loads(cleaned_json)  # Validar si es JSON válido
        return json.dumps(data)  # Retornar como JSON limpio
    except json.JSONDecodeError as e:
        print(f"Error al decodificar JSON: {e}")
        return json.dumps({"error": "Respuesta no válida", "detalles": str(e)})

from google.cloud import storage

def check_file_exists(bucket_name, file_path):
    """Verifica si el archivo existe en el bucket de GCS."""
    client = storage.Client(credentials=credentials, project="speech-s2s")
    bucket = client.bucket(bucket_name)

    # Ajustar ruta eliminando "gs://<bucket_name>" si está presente
    prefix = file_path.replace(f"gs://{bucket_name}/", "")

    # Crear blob y verificar existencia
    blob = bucket.blob(prefix)

    if blob.exists():
        print(f"El archivo {file_path} existe en el bucket.")
        return True
    else:
        print(f"El archivo {file_path} NO existe en el bucket.")

        # Listar archivos en la carpeta del bucket
        #folder_prefix = "/".join(prefix.split("/")[:-1]) + "/"
        #print("Archivos disponibles en la carpeta:")
        #blobs = client.list_blobs(bucket_name, prefix=folder_prefix)
        #for b in blobs:
            #print(b.name)

        return False

def run_extract_entities_from_audio(path_to_file: str, bucket_name: str) -> str:
    """Extrae las entidades del audio utilizando el modelo de Gemini."""
    try:
        # Verificar si el archivo existe en GCS antes de procesarlo
        if not check_file_exists(bucket_name, path_to_file):
            raise FileNotFoundError(f"El archivo {path_to_file} no existe en el bucket {bucket_name}.")

        # Extraer solo el nombre del archivo sin la ruta
        nombre_archivo = path_to_file.split("/")[-1]
        #print("Este es el nombre del archivo: " ,nombre_archivo)

        nombre_archivo = nombre_archivo.replace(".mp3", "")
        #print(f"nombre_archivo al procesar el nombre_archivo {nombre_archivo}")

        # Separar por el delimitador "\_"
        partes = nombre_archivo.split("_")
        #print("partes al procesar el partes")

        if len(partes) != 9:
            raise ValueError("El nombre del archivo no contiene el formato esperado.") 

        global template_prompt
        #Limpiar datos.
        telefono = ""
        fechaarchivo = ""
        horaarchivo = ""
        habilidad = ""
        connid = ""
        id_agente = ""
        
        #Extracción datos del nombre del archivo.
        fechaarchivo = partes[0]
        horaarchivo = partes[1]
        habilidad = f"{partes[2]}{partes[3]}{partes[4]}{partes[5]}"
        connid = partes[6]
        id_agente = partes[7]
        telefono = str(partes[8])

        #Agregar formato a la fecha y hora de cada archivo.
        fecha_formateada = f"{fechaarchivo[:4]}-{fechaarchivo[4:6]}-{fechaarchivo[6:]}"  # De 'YYYYMMDD' a 'YYYY-MM-DD'
        hora_formateada = f"{horaarchivo[:2]}:{horaarchivo[2:4]}:{horaarchivo[4:]}"       # De 'HHMMSS' a 'HH:MM:SS'

        #Fecha y hora en la que se hizo la ejecución.
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        hora_actual = datetime.now().strftime("%H:%M:%S")

        #Reemplazar en prompt.
        template_prompt_format = template_prompt
        template_prompt_format = template_prompt_format.replace("<TELEFONO>", telefono)\
                                .replace("<HABILIDAD>", habilidad)\
                                .replace("<CONND_ID>", connid)\
                                .replace("<ID_AGENTE>", id_agente)\
                                .replace("<FECHA_ACTUAL>", fecha_actual)\
                                .replace("<HORA_ACTUAL>", hora_actual)\
                                .replace("<FECHADELLAMADA>", fecha_formateada)\
                                .replace("<HORADELLAMADA>", hora_formateada)
        #print(f"telefono al procesar el telefono {telefono}")
        #print(f"hora al procesar la hora del archivo {fecha_hora_llamada}")
        #print(template_prompt_format)
        
        # Procesar el audio desde GCS
        audio_part = Part.from_uri(mime_type="audio/mpeg", uri=path_to_file)

        response = model.generate_content(
            [template_prompt_format, audio_part],
            generation_config=generation_config,
            safety_settings=safety_settings
        )

        # Validar si la respuesta contiene texto
        if not response.text or not response.text.strip():
            print(f"No se recibió respuesta del modelo para el audio {path_to_file}")
            return json.dumps({"error": "Respuesta vacía del modelo", "audio": path_to_file})

        # Limpiar y validar el JSON retornado
        return strip_json(response.text)

    except Exception as e:
        print(f"Error al procesar el audio {path_to_file}: {e}")
        return json.dumps({"error": str(e), "audio": path_to_file})
