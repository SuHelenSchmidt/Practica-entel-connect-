import logging
import os
from datetime import datetime

# Definir la ruta del log dentro del proyecto
LOG_DIR = "logs"
LOG_FILE = "app.log"

# Crear la carpeta si no existe
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Generar el nombre del archivo con la fecha y hora
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_FILE = f"app_{timestamp}.log"
LOG_PATH = os.path.join(LOG_DIR, LOG_FILE)

# Configurar el logging
logging.basicConfig(
    level=logging.INFO,  # Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),  # Guardar en archivo
        logging.StreamHandler()  # Mostrar en consola
    ]
)

# Obtener el logger para usar en otros archivos
logger = logging.getLogger("AppLogger")
