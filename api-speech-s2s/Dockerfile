# Usa una imagen base oficial de Python
FROM python:3.12-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos necesarios
COPY . /app

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exportar el puerto 8080 para Cloud Run
EXPOSE 8080

# Configurar la variable de entorno GOOGLE_APPLICATION_CREDENTIALS
ENV GOOGLE_APPLICATION_CREDENTIALS="/app/credential/speech-s2s-927193d16d57.json"

# Comando para iniciar la aplicación
CMD ["python", "app.py"]