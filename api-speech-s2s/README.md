# Speech-to-Speech Processing Project

Este proyecto tiene como objetivo procesar archivos de audio almacenados en un servidor SFTP el cual se encuentra en una carpeta con la fecha actual con la siguiente estructura "DD_MM_YYYY",
y subirlos a Google Cloud Storage, permitiendo una integración eficiente con servicios de análisis y almacenamiento en la nube.

---

## 🛠️ **Características**
- Descarga de archivos de audio desde un servidor SFTP.
- Subida de los archivos procesados a un bucket de Google Cloud Storage.
- Mantenimiento de la estructura de carpetas del servidor SFTP en el bucket.
- Manejo seguro de credenciales y configuraciones mediante archivos de entorno.

---

## ⚙️ **Configuración**

### **1. Variables de Entorno**
Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```env
# Credenciales del servidor SFTP
SFTP_HOST=tu_sftp_host
SFTP_PORT=22
SFTP_USER=tu_usuario
SFTP_PASSWORD=tu_contraseña

# Configuración de Google Cloud
GCP_PROJECT_ID=speech-s2s
GCP_BUCKET_NAME=speech_s2s_bucket
GOOGLE_APPLICATION_CREDENTIALS= Usar google CLI
```

### **2. Crear y Activar el Entorno Virtual**

Antes de instalar las dependencias, es recomendable crear y activar un entorno virtual para el proyecto:

1. **Crear el entorno virtual**:

   Ejecuta el siguiente comando para crear un entorno virtual en tu proyecto:

   ```bash
   python3 -m venv venv
   ```

2. **Activar el entorno virtual**:

   Una vez creado el entorno virtual, actívalo con el siguiente comando:

   - **En macOS o Linux:**
     ```bash
     source venv/bin/activate
     ```

   - **En Windows (PowerShell):**
     ```bash
     .\venv\Scripts\Activate
     ```

   Verás que el prompt de tu terminal cambia a algo como esto:
   ```bash
   (venv) jonatanhernandezopazo@Laptop-de-Jonatan speech_s2s %
   ```

### **3. Instalación de Dependencias**
Con el entorno virtual activado, instala las dependencias del proyecto ejecutando:

```bash
pip install -r requirements.txt
```

---

## 🚀 **Cómo Usar**

### **Ejecutar el proceso principal**
Luego de descargar las dependencias necesarias, y de haber configurado donde apunta el bucket, debes ejecutar primeramente leadscoaching_bigquery_table_test.py, para crear la tabla donde se insertaran los datos
Finalmente debes ejecutar el main, de la siguiente manera:

```bash
python leadscoaching_biguery_table_test.py

*Se crea la tabla*
```

```bash
python main.py
```

---

## 🛡️ **Mejoras Futuras**
- Integrar Flask para levantar como HTTP, empaquetarlo en Docker y subirlo a Cloud Run para ejecutar con `curl` usando el método POST del HTTP levantado.
- Manejo de errores más robusto, incluyendo reintentos automáticos.

---

## 🤝 **Contribuciones**
Si deseas contribuir a este proyecto, ¡serás bienvenido! Abre un issue o envía un pull request con tus mejoras.

---

## 📝 **Licencia**
Este proyecto está bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.

---

