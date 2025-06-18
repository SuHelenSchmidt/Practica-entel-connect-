import pysftp
from credential.sftp import sftp_credential

# Configuración de la conexión
sftp_config = sftp_credential

# Configuración de opciones de conexión (omitimos la verificación de la clave)
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None  # Desactiva la verificación de la clave del host

def test_connection_sftp():
    try:
        # Conexión al servidor SFTP
        with pysftp.Connection(**sftp_config, cnopts=cnopts) as sftp:
            print("¡Conexión exitosa al SFTP!")
            return True
    except Exception as e:
        print(f"Error al conectar al SFTP: {e}")
        return False


