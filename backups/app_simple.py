import os
from suno import Suno, ModelVersions
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

# Obtener el cookie de ambiente
COOKIE = os.getenv("SUNO_COOKIE")

# Inicializar el cliente Suno
client = Suno(
    cookie=COOKIE, 
    model_version=ModelVersions.CHIRP_V3_5
)

# Generar una canción con parámetros adicionales
songs = client.generate(
    prompt="Feliz cumpleaños mi amor",    # Ejemplo de descripción o letra
    is_custom=False,                      # Indicar si es letra personalizada o descripción
    tags="Spanish, romantic",             # Etiquetas o características deseadas (opcional)
    title="Cumpleaños de Amor",           # Título de la canción (opcional)
    make_instrumental=True,               # Generar versión instrumental (opcional)
    wait_audio=True                       # Esperar a que esté listo el audio
)

# Descargar las canciones generadas
for song in songs:
    try:
        file_path = client.download(song=song)
        print(f"Song downloaded to: {file_path}")
    except Exception as e:
        print(f"Failed to download song: {str(e)}")
