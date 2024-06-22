import os
import json
import time
from suno import Suno, ModelVersions
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

# Obtener el cookie de ambiente
COOKIE = os.getenv("SUNO_COOKIE")

# Ruta base donde se almacenarán todas las canciones descargadas
BASE_DOWNLOAD_PATH = "canciones_descargadas"

# Inicializar el cliente Suno
client = Suno(
    cookie=COOKIE, 
    model_version=ModelVersions.CHIRP_V3_5
)

def generate_songs_from_prompts(prompts_file):
    # Leer el archivo JSON de prompts
    with open(prompts_file, 'r', encoding='utf-8') as file:
        prompts = json.load(file)

    # Contador para manejar el número de canciones descargadas
    downloaded_count = 0
    batch_size = 8  # Cantidad de canciones a esperar antes de continuar con el siguiente grupo

    for prompt_data in prompts:
        category = prompt_data['category']
        category_folder = os.path.join(BASE_DOWNLOAD_PATH, category)

        print(f"Generating songs for category: '{category}'")

        # Verificar si la carpeta de la categoría ya existe
        if not os.path.exists(category_folder):
            os.makedirs(category_folder)

        variations = prompt_data['variations']

        # Generar canciones para cada variación dentro de la categoría
        for variation in variations:
            prompt = variation['prompt']
            tags = variation['tags']
            title = variation.get('title', f"{prompt} - {tags[0]}")  # Nombre de la canción

            print(f"Generating songs for prompt: '{prompt}'")

            # Generar canciones para cada género del prompt
            for tag in tags:
                try:
                    songs = client.generate(
                        prompt=prompt,  #If is_custom=True, this should be the lyrics of the song. If False, it should be a brief description of what the song should be about.
                        is_custom=False, #Determines whether the song should be generated from custom lyrics (True) or from a description (False).
                        tags=tag, #Describes the desired voice type or characteristics (e.g., "English male voice"). Default is "".
                        title=title,  # Nombre de la canción con prompt y género
                        wait_audio=True
                    )

                    # Descargar y guardar las canciones en la carpeta de la categoría
                    for index, song in enumerate(songs, start=1):
                        try:
                            # Descargar el archivo con el nombre proporcionado por Suno
                            downloaded_file = client.download(song=song, path=category_folder)

                            # Construir el nuevo nombre de archivo
                            new_filename = f"{category} - {title} - {tag} - {index}.mp3"
                            new_file_path = os.path.join(category_folder, new_filename)

                            # Renombrar el archivo descargado
                            os.rename(downloaded_file, new_file_path)
                            print(f"Song downloaded and renamed to: {new_file_path}")
                            downloaded_count += 1
                        except Exception as e:
                            print(f"Failed to download song: {str(e)}")

                        # Esperar un momento para la siguiente descarga
                        if downloaded_count % batch_size == 0:
                            print(f"Waiting before the next batch...")
                            time.sleep(30)  # Esperar 30 segundos entre lotes de descargas

                except Exception as e:
                    print(f"Failed to generate songs for prompt '{prompt}' and tag '{tag}': {str(e)}")

    print("All songs downloaded successfully!")

# Ejecutar la función para generar canciones desde el archivo prompts.json
generate_songs_from_prompts("promts/cumple_especial.json")
