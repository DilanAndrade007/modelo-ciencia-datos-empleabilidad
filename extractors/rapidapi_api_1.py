import os
import requests
import hashlib
import json
import pandas as pd
from datetime import datetime
from utils.file_manager import (
    crear_directorios,
    guardar_log,
    cargar_log_existente,
)

def generar_job_id(titulo, empresa, ubicacion, fecha):
    cadena = f"{titulo}_{empresa}_{ubicacion}_{fecha}"
    return hashlib.sha256(cadena.encode('utf-8')).hexdigest()

def buscar_en_rapidapi(query, api_key):
    resultados = []
    headers = {
        "x-rapidapi-host": "jsearch.p.rapidapi.com",
        "x-rapidapi-key": api_key,
    }
    base_url = "https://jsearch.p.rapidapi.com/search"

    page = 1
    while True:
        params = {
            "query": query,
            "page": page,
        }
        try:
            response = requests.get(base_url, headers=headers, params=params, timeout=10)
            if response.status_code != 200:
                print(f"Error HTTP {response.status_code} para '{query}', página {page}")
                break
            data = response.json()
            jobs = data.get("data", [])
            if not jobs:
                break
            resultados.extend(jobs)
            print(f"  Página {page}: {len(jobs)} ofertas")
            page += 1
        except Exception as e:
            print(f" Error en página {page}: {e}")
            break
    return resultados, page - 1, len(resultados)

def normalizar_oferta(job, fuente, carrera, fecha):
    uid = generar_job_id(
        job.get('job_title', ''),
        job.get('employer_name', ''),
        job.get('job_city', ''),
        job.get('job_posted_at_datetime_utc', '')
    )
    return {
        "job_id": hashlib.sha256(uid.encode()).hexdigest(),
        "source": fuente,
        "job_title": job.get("job_title", ""),
        "company": job.get("employer_name", ""),
        "location": f"{job.get('job_city', '')}, {job.get('job_country', '')}",
        "description": job.get("job_description", ""),
        "skills": job.get("job_highlights", {}).get("Qualifications", []) +
                  job.get("job_highlights", {}).get("Responsibilities", []),
        "careers_required": carrera,
        "date_posted": job.get("job_posted_at_datetime_utc", ""),
        "url": job.get("job_apply_link", ""),
        "career_tag": "",
        "soft_skills_detected": [],
        "extraction_date": fecha,
    }

def extraer_desde_rapidapi_1(query, api_key, carrera):
    HOY = datetime.now().strftime("%Y-%m-%d")
    fuente = "rapidapi1"
    crear_directorios()

    log = cargar_log_existente(fuente)
    if query in log and log[query].get("last_extraction_date") == HOY:
        print(f" Ya se extrajo '{query}' hoy. Omitiendo...")
        return

    ofertas_raw, ultima_pagina, total = buscar_en_rapidapi(query, api_key)
    if not ofertas_raw:
        print(" No se extrajeron resultados.")
        return

    corpus = [normalizar_oferta(job, fuente, carrera, HOY) for job in ofertas_raw]
    df = pd.DataFrame(corpus)

    directorio = f"data/outputs/{fuente}/{carrera.replace(' ', '_')}"
    os.makedirs(directorio, exist_ok=True)
    nombre_csv = f"{directorio}/{fuente}__{query.replace(' ', '_')}__{HOY}.csv"

    if os.path.exists(nombre_csv):
        df_existente = pd.read_csv(nombre_csv)
        df = pd.concat([df_existente, df], ignore_index=True).drop_duplicates(subset="job_id")

    df.to_csv(nombre_csv, index=False)
    print(f"✅ Archivo guardado: {nombre_csv} ({len(df)} filas)")

    guardar_log(fuente, query, fecha=HOY, total=total, pagina=ultima_pagina)
