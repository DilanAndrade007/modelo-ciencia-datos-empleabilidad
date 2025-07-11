import os
import requests
import hashlib
import json
import pandas as pd
from datetime import datetime
from utils.file_manager import guardar_log, crear_directorios, cargar_log_existente

def generar_job_id(titulo, empresa, ubicacion, fecha):
    cadena = f"{titulo}_{empresa}_{ubicacion}_{fecha}"
    return hashlib.md5(cadena.encode('utf-8')).hexdigest()

def buscar_jooble(query, api_key, start_page=1, delay=1.0):
    url = f"https://jooble.org/api/{api_key}"
    resultados = []
    pagina = start_page
    while True:
        try:
            body = {"keywords": query, "page": pagina}
            response = requests.post(url, json=body, timeout=10)
            if response.status_code != 200:
                print(f" Error HTTP {response.status_code} en página {pagina}")
                break
            data = response.json()
            jobs = data.get("jobs", [])
            if not jobs:
                break
            resultados.extend(jobs)
            print(f"  Página {pagina}: {len(jobs)} ofertas")
            pagina += 1
        except Exception as e:
            print(f"  Error en página {pagina}: {e}")
            break
    return resultados, pagina - 1

def normalizar(oferta, fuente, carrera, fecha):
    uid = generar_job_id(
    oferta.get('title', ''),
    oferta.get('company', ''),
    oferta.get('location', ''),
    oferta.get('updated', '')
    )
    return {
        "job_id": hashlib.md5(uid.encode()).hexdigest(),
        "source": fuente,
        "job_title": oferta.get("title", ""),
        "company": oferta.get("company", ""),
        "location": oferta.get("location", ""),
        "description": oferta.get("snippet", ""),
        "skills": [],
        "careers_required": carrera,
        "date_posted": oferta.get("updated", ""),
        "url": oferta.get("link", ""),
        "career_tag": "",
        "soft_skills_detected": [],
        "extraction_date": fecha
    }

def extraer_desde_jooble(query, api_key, carrera):
    HOY = datetime.now().strftime("%Y-%m-%d")
    fuente = "jooble"
    crear_directorios()

    # === Reanudar desde log si existe ===
    log = cargar_log_existente(fuente)
    ultima_pagina = 1
    if query in log:
        ultima_fecha = log[query].get("last_extraction_date")
        if ultima_fecha == HOY:
            ultima_pagina = log[query].get("last_page_extracted", 0) + 1
            print(f" Reanudando desde página {ultima_pagina} (mismo día: {HOY})")
        else:
            print(f" Nueva ejecución para '{query}' en un día distinto ({HOY}). Iniciando desde página 1.")


    # === Extracción ===
    ofertas_raw, pagina_final = buscar_jooble(query, api_key, start_page=ultima_pagina)
    if not ofertas_raw:
        print(" No se extrajeron nuevas ofertas.")
        return

    corpus = [normalizar(o, fuente, HOY) for o in ofertas_raw]
    df = pd.DataFrame(corpus)

    # === Crear carpeta por carrera ===
    directorio = f"data/outputs/{fuente}/{carrera.replace(' ', '_')}"
    os.makedirs(directorio, exist_ok=True)
    nombre_csv = f"{directorio}/{fuente}__{query.replace(' ', '_')}__{HOY}.csv"

    # === Si ya existe, unir y deduplicar ===
    if os.path.exists(nombre_csv):
        df_existente = pd.read_csv(nombre_csv)
        df = pd.concat([df_existente, df], ignore_index=True)
        df.drop_duplicates(subset="job_id", inplace=True)

    df.to_csv(nombre_csv, index=False)
    print(f" Archivo actualizado: {nombre_csv} ({len(df)} filas totales)")

    # === Guardar log ===
    guardar_log(fuente, query, HOY, len(df), pagina_final)
