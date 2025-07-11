import os
import requests
import hashlib
import json
import pandas as pd
import time
from datetime import datetime
from utils.file_manager import crear_directorios, guardar_log, cargar_log_existente

def generar_job_id(titulo, empresa, ubicacion, fecha):
    cadena = f"{titulo}_{empresa}_{ubicacion}_{fecha}"
    return hashlib.md5(cadena.encode('utf-8')).hexdigest()

def normalizar(trabajo_raw, fuente, carrera, fecha):
    """Mapea datos raw al esquema estándar."""
    titulo = trabajo_raw.get('title', '')
    empresa = trabajo_raw.get('company_name', '')
    ubicacion = trabajo_raw.get('location', '')
    fecha_creacion = trabajo_raw.get('created', '')
    descripcion = trabajo_raw.get('description', '')

    # Skills solo si existen explícitamente
    skills = trabajo_raw.get('skills', [])

    job_id = generar_job_id(titulo, empresa, ubicacion, fecha_creacion)

    return {
        'job_id': job_id,
        'source': fuente,
        'job_title': titulo,
        'company': empresa,
        'location': ubicacion,
        'description': descripcion,
        'skills': skills,
        'careers_required': carrera,
        'date_posted': fecha_creacion,
        'url': trabajo_raw.get('url', ''),
        'career_tag': '',
        'soft_skills_detected': [],
        'extraction_date': fecha
    }

def extraer_desde_coresignal(query, api_key, carrera):
    HOY = datetime.now().strftime("%Y-%m-%d")
    fuente = "coresignal"
    crear_directorios()

    # === Reanudar desde log si existe ===
    log = cargar_log_existente(fuente)
    if query in log and log[query].get("last_extraction_date") == HOY:
        print(f"Ya se extrajo '{query}' hoy. Omitiendo...")
        return

    # === Extracción ===
    session = requests.Session()
    session.headers.update({
        "apikey": api_key,
        "accept": "application/json"
    })

    search_url = "https://api.coresignal.com/cdapi/v2/job_base/search/filter"
    collect_url = "https://api.coresignal.com/cdapi/v2/job_base/collect"

    filtros = {"title": query}

    try:
        response = session.post(search_url, json=filtros, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Error al buscar IDs en Coresignal: {e}")
        return

    job_ids = response.json()

    if not job_ids:
        print("No se encontraron trabajos.")
        return

    job_ids = job_ids[:50]  # Límite arbitrario para evitar excesivas llamadas
    trabajos_mapeados = []

    for job_id in job_ids:
        detalle_url = f"{collect_url}/{job_id}"
        resp = session.get(detalle_url, timeout=30)
        if resp.status_code != 200:
            continue
        trabajo_raw = resp.json()
        trabajo = normalizar(trabajo_raw, fuente, carrera, HOY)
        trabajos_mapeados.append(trabajo)
        time.sleep(0.1)

    if not trabajos_mapeados:
        print("No se obtuvieron detalles de trabajos.")
        return

    # === Guardado ===
    df = pd.DataFrame(trabajos_mapeados)

    # Crear carpeta por carrera
    directorio = f"data/outputs/{fuente}/{carrera.replace(' ', '_')}"
    os.makedirs(directorio, exist_ok=True)
    nombre_csv = f"{directorio}/{fuente}__{query.replace(' ', '_')}__{HOY}.csv"

    if os.path.exists(nombre_csv):
        df_existente = pd.read_csv(nombre_csv)
        df = pd.concat([df_existente, df], ignore_index=True)
        df.drop_duplicates(subset="job_id", inplace=True)

    df.to_csv(nombre_csv, index=False)
    print(f"✅ Archivo guardado: {nombre_csv} ({len(df)} filas)")

    # Guardar log
    guardar_log(fuente, query, HOY, len(df), pagina=0)
