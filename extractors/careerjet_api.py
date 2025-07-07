import os
import requests
import hashlib
import pandas as pd
from datetime import datetime
from utils.file_manager import crear_directorios, guardar_log, cargar_log_existente

def generar_job_id(titulo, empresa, ubicacion, fecha):
    """Genera un hash único para el trabajo."""
    cadena = f"{titulo}_{empresa}_{ubicacion}_{fecha}"
    return hashlib.md5(cadena.encode('utf-8')).hexdigest()

def normalizar(oferta, fuente, fecha):
    """Mapea datos raw al esquema estándar."""
    titulo = oferta.get("title", "")
    empresa = oferta.get("company", "")
    ubicacion = oferta.get("locations", "")
    fecha_publicacion = oferta.get("date", "")
    descripcion = oferta.get("description", "")

    job_id = generar_job_id(titulo, empresa, ubicacion, fecha_publicacion)

    return {
        "job_id": job_id,
        "source": fuente,
        "job_title": titulo,
        "company": empresa,
        "location": ubicacion,
        "description": descripcion,
        "skills": [],  # No se infiere nada
        "careers_required": [],
        "date_posted": fecha_publicacion,
        "url": oferta.get("url", ""),
        "career_tag": "",
        "soft_skills_detected": [],
        "extraction_date": fecha,
    }

def extraer_desde_careerjet(query, carrera, country_code="ec"):
    HOY = datetime.now().strftime("%Y-%m-%d")
    fuente = "careerjet"
    crear_directorios()

    log = cargar_log_existente(fuente)
    if query in log and log[query].get("last_extraction_date") == HOY:
        print(f"⏩ Ya se extrajo '{query}' hoy. Omitiendo...")
        return

    base_url = "https://api.careerjet.com/jobs"
    page = 1
    all_jobs = []

    while True:
        params = {
            "keywords": query,
            "location": country_code.upper(),  # puede ser país o ciudad
            "page": page
        }
        try:
            response = requests.get(base_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"❌ Error al consultar Careerjet: {e}")
            break

        ofertas = data.get("jobs", [])
        if not ofertas:
            break

        all_jobs.extend(ofertas)
        print(f"  Página {page}: {len(ofertas)} ofertas")
        page += 1

    if not all_jobs:
        print(f"⚠️ No se encontraron resultados para '{query}'.")
        return

    corpus = [normalizar(o, fuente, HOY) for o in all_jobs]
    df = pd.DataFrame(corpus)

    # === Guardado ===
    directorio = f"data/outputs/{fuente}/{carrera.replace(' ', '_')}"
    os.makedirs(directorio, exist_ok=True)
    nombre_csv = f"{directorio}/{fuente}__{query.replace(' ', '_')}__{HOY}.csv"

    if os.path.exists(nombre_csv):
        df_existente = pd.read_csv(nombre_csv)
        df = pd.concat([df_existente, df], ignore_index=True)
        df.drop_duplicates(subset="job_id", inplace=True)

    df.to_csv(nombre_csv, index=False)
    print(f"✅ Archivo guardado: {nombre_csv} ({len(df)} filas)")

    guardar_log(fuente, query, HOY, len(df), pagina=page - 1)
