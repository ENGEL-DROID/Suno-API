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

def serialize_metadata(metadata):
    """ Convierte el objeto metadata a un diccionario serializable en JSON. """
    if isinstance(metadata, dict):
        return {k: serialize_metadata(v) for k, v in metadata.items()}
    elif hasattr(metadata, "__dict__"):
        return {k: serialize_metadata(v) for k, v in metadata.__dict__.items()}
    else:
        return metadata

def get_unique_filename(base_name, extension, folder_path):
    """Genera un nombre de archivo único basado en un nombre base, una extensión y una carpeta."""
    version = 1
    file_name = f"{base_name}.{extension}"
    file_path = os.path.join(folder_path, file_name)

    while os.path.exists(file_path):
        file_name = f"{base_name} - V{version}.{extension}"
        file_path = os.path.join(folder_path, file_name)
        version += 1
    
    return file_path

def generate_songs_from_prompts(prompts_file):
    # Leer el archivo JSON de prompts
    with open(prompts_file, 'r', encoding='utf-8') as file:
        prompts = json.load(file)

    # Contador para manejar el número de canciones descargadas
    downloaded_count = 0
    batch_size = 8  # Cantidad de canciones a esperar antes de continuar con el siguiente grupo

    # Lista para almacenar la información simplificada de cada canción
    songs_info = []

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
            title = variation.get('title', prompt)  # Usar el título proporcionado o el prompt

            print(f"Generating songs for prompt: '{prompt}'")

            try:
                # Generar canciones usando el prompt y todas las etiquetas combinadas
                songs = client.generate(
                    prompt=prompt,
                    is_custom=False,
                    tags=tags,  # Combinar todas las etiquetas
                    title=title,  # Nombre de la canción
                    wait_audio=True
                )

                # Descargar y guardar todas las versiones generadas
                for index, song in enumerate(songs, start=1):
                    try:
                        # Descargar el archivo de audio con el nombre proporcionado por Suno
                        downloaded_file = client.download(song=song, path=category_folder)

                        # Obtener información específica de la canción para guardar en archivo
                        song_info = {
                            "id": getattr(song, 'id', ''),
                            "video_url": getattr(song, 'video_url', ''),
                            "audio_url": getattr(song, 'audio_url', ''),
                            "image_large_url": getattr(song, 'image_large_url', ''),
                            "metadata": serialize_metadata(getattr(song, 'metadata', {})),
                            "user_id": getattr(song, 'user_id', ''),
                            "created_at": getattr(song, 'created_at', ''),
                            "title": getattr(song, 'title', ''),
                            "lyrics": getattr(song.metadata, 'prompt', '') if hasattr(song, 'metadata') and hasattr(song.metadata, 'prompt') else ''
                        }

                        # Guardar la información simplificada de la canción en la lista
                        songs_info.append(song_info)

                        # Obtener el nombre del archivo descargado
                        downloaded_filename = os.path.basename(downloaded_file)

                        # Construir el nuevo nombre de archivo para el audio
                        new_audio_filename = get_unique_filename(f"{title} - {index}", "mp3", category_folder)
                        new_audio_file_path = new_audio_filename

                        # Construir el nombre de archivo para guardar la información
                        info_filename = get_unique_filename(f"{title} - {index}", "json", category_folder)
                        info_file_path = info_filename

                        # Guardar la información en un archivo JSON
                        with open(info_file_path, 'w', encoding='utf-8') as info_file:
                            json.dump(song_info, info_file, indent=4, ensure_ascii=False)
                            print(f"Song info saved to: {info_file_path}")

                        # Renombrar el archivo de audio descargado
                        os.rename(os.path.join(category_folder, downloaded_filename), new_audio_file_path)
                        print(f"Song downloaded and renamed to: {new_audio_file_path}")
                        downloaded_count += 1

                        # Guardar letra de la canción si está disponible
                        if song_info['lyrics']:
                            # Construir el nombre de archivo para la letra
                            lyrics_filename = get_unique_filename(f"{title} - {index}", "txt", category_folder)
                            lyrics_file_path = lyrics_filename
                            # Guardar la letra en un archivo de texto
                            with open(lyrics_file_path, 'w', encoding='utf-8') as lyrics_file:
                                lyrics_file.write(song_info['lyrics'])
                            print(f"Lyrics saved to: {lyrics_file_path}")

                    except Exception as e:
                        print(f"Failed to download song or save lyrics: {str(e)}")

                    # Esperar un momento para la siguiente descarga
                    if downloaded_count % batch_size == 0:
                        print(f"Waiting before the next batch...")
                        time.sleep(30)  # Esperar 30 segundos entre lotes de descargas

            except Exception as e:
                print(f"Failed to generate songs for prompt '{prompt}': {str(e)}")

    print("All songs downloaded successfully!")

# Ejecutar la función para generar canciones desde el archivo prompts.json
generate_songs_from_prompts("promts/fortuna.json")
