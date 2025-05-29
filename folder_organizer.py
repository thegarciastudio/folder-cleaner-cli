
from pathlib import Path
import argparse
import logging
import hashlib
import gdown

def calcular_hash(archivo, algoritmo="sha256"):
    hash_func = hashlib.new(algoritmo)
    with open(archivo, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            hash_func.update(chunk)
    return hash_func.hexdigest()

def extraer_id_carpeta(url):
    if "folders/" in url:
        return url.split("folders/")[1].split("?")[0]
    else:
        return None

archivos_movidos = 0
archivos_no_movidos = 0
archivos_simulados = 0
dic = {}

logs_dir = Path(__file__).parent / "logs"
logs_dir.mkdir(exist_ok=True)
log_file = logs_dir / "folder_organizer.log"

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

parser = argparse.ArgumentParser(description="Organize files by type / Organiza archivos por tipo")
parser.add_argument("--carpeta", type=str, required=True, help="Folder to organize / Carpeta a organizar")
parser.add_argument("--dry-run", action="store_true", help="Simulate the process without moving files / Simula sin mover archivos")
parser.add_argument("--drive-folder-url", type=str, help="Google Drive folder URL / URL de carpeta de Google Drive")
parser.add_argument("--idioma", type=str, default="es", choices=["es", "en"], help="Language for messages: es (Español) or en (English)")

arg = parser.parse_args()

ids = extraer_id_carpeta(arg.drive_folder_url) if arg.drive_folder_url else None
dry_run = arg.dry_run
idioma = arg.idioma
ruta = Path(arg.carpeta).resolve()

agrupacion = {
    "documentos": [".pdf", ".docx", ".txt"],
    "imágenes": [".jpg", ".png", ".jpeg"],
    "videos": [".mp4", ".mov", ".avi"],
    "otros": []
}

if ruta.exists():
    if ids:
        gdown.download_folder(id=ids, output=ruta)

    for p in agrupacion:
        (ruta / p).mkdir(exist_ok=True)
        logging.info(f"Folder {p} created or already exists")

    for i in ruta.glob("*"):
        if i.is_file():
            carpeta = "otros"
            nombre = i.name
            j = 1
            hass = calcular_hash(i)

            if hass in dic:
                logging.warning(f"File {i} is a duplicate of {dic[hass]}")
                print(f"{'El archivo' if idioma == 'es' else 'File'} {i} {'tiene el mismo contenido que' if idioma == 'es' else 'is a duplicate of'} {dic[hass]}")
            else:
                dic[hass] = i

            for clave, lista in agrupacion.items():
                for extension in lista:
                    if i.suffix == extension:
                        carpeta = clave

            while (ruta / carpeta / nombre).exists():
                nombre = f"{i.stem}({j}){i.suffix}"
                j += 1

            if dry_run:
                print(f"[DRY-RUN] {'Movería' if idioma == 'es' else 'Would move'}: {i} -> {ruta/carpeta/nombre}")
                archivos_simulados += 1
            else:
                mover = ""
                while mover not in ["s", "n"]:
                    mover = input(f"{'¿Desea mover el archivo' if idioma == 'es' else 'Do you want to move file'} {i} -> {ruta/carpeta/nombre}? (s/n) ").lower()
                    if mover not in ["s", "n"]:
                        print("Error. Entrada no válida, por favor ingrese 's' para sí o 'n' para no" if idioma == "es"
                              else "Invalid input. Please enter 's' for yes or 'n' for no")

                if mover == "s":
                    i.rename(ruta / carpeta / nombre)
                    logging.info(f"File moved: {i} -> {ruta/carpeta/nombre}")
                    archivos_movidos += 1
                else:
                    archivos_no_movidos += 1

    if idioma == "es":
        print("\nResumen:")
        print(f"Archivos movidos: {archivos_movidos}")
        print(f"Archivos no movidos: {archivos_no_movidos}")
        print(f"Archivos simulados: {archivos_simulados}\n")
    else:
        print("\nSummary:")
        print(f"Files moved: {archivos_movidos}")
        print(f"Files not moved: {archivos_no_movidos}")
        print(f"Simulated files: {archivos_simulados}\n")

else:
    print("Error. No existe la ruta" if idioma == "es" else "Error. The path does not exist")
    logging.error(f"The path {ruta} does not exist")
