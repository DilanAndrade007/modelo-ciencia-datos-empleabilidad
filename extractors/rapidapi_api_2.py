import os
import requests
import hashlib
import pandas as pd
from datetime import datetime
from utils.file_manager import guardar_log, crear_directorios, cargar_log_existente

def buscar_linkedin_rapidapi(query, api_key, limit=100, offset=0, include_ai=False):
    url = "https://linkedin-job-search-api.p.rapidapi.com/active-jb-7d"

    querystring = {
        "limit": str(limit),
        "offset": str(offset),
        "title_filter": f"\"{query}\""
    }

    if include_ai:
        querystring["include_ai"] = "true"

    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "linkedin-job-search-api.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring, timeout=30)

    if response.status_code != 200:
        print(f" Error HTTP {response.status_code}")
        return []

    try:
        jobs = response.json()
    except Exception as e:
        print(" Error al parsear JSON:", e)
        return []

    print(f"  Recuperados {len(jobs)} empleos (offset={offset})")
    return jobs


def normalizar(oferta, fuente, fecha, carrera_tag):
    uid = f"{oferta.get('title')}_{oferta.get('organization')}_{oferta.get('date_posted')}_{oferta.get('url')}"

    # Arreglado aquí:
    locations_raw = oferta.get("locations_derived") or []
    locations = []

    for loc in locations_raw:
        if isinstance(loc, dict):
            location_text = ", ".join(
                filter(None, [
                    loc.get("city", ""),
                    loc.get("admin", ""),
                    loc.get("country", "")
                ])
            )
            locations.append(location_text)
        elif isinstance(loc, str):
            locations.append(loc)
        else:
            locations.append("")

    location_str = "; ".join(locations)

    return {
        "job_id": hashlib.md5(uid.encode()).hexdigest(),
        "source": fuente,
        "job_title": oferta.get("title", ""),
        "company": oferta.get("organization", ""),
        "location": location_str,
        "description": oferta.get("description_text", ""),
        "skills": oferta.get("ai_key_skills", []) if "ai_key_skills" in oferta else [],
        "careers_required": [],
        "date_posted": oferta.get("date_posted", ""),
        "url": oferta.get("url", ""),
        "career_tag": carrera_tag,
        "soft_skills_detected": [],
        "extraction_date": fecha
    }


def extraer_desde_rapidapi_2(query, api_key, carrera, include_ai=False):
    HOY = datetime.now().strftime("%Y-%m-%d")
    fuente = "rapidapi2"
    crear_directorios()

    log = cargar_log_existente(fuente)

    # Verificar si ya se extrajo hoy
    ultima_pagina = 0
    if query in log:
        ultima_fecha = log[query].get("last_extraction_date")
        if ultima_fecha == HOY:
            ultima_pagina = log[query].get("last_page_extracted", 0) + 1
            print(f" Reanudando desde offset {(ultima_pagina-1)*100} (mismo día: {HOY})")
        else:
            print(f" Nueva extracción para '{query}' en un día distinto ({HOY}). Iniciando desde 0.")

    offset = (ultima_pagina-1) * 100 if ultima_pagina > 0 else 0
    total_extraidos = 0
    all_results = []

    while True:
        results = buscar_linkedin_rapidapi(query, api_key, limit=100, offset=offset, include_ai=include_ai)
        if not results:
            break

        normalized = [normalizar(o, fuente, HOY, carrera) for o in results]
        all_results.extend(normalized)

        offset += 100
        total_extraidos += len(results)

        if len(results) < 100:
            break

    if not all_results:
        print(" No se extrajeron nuevas ofertas de LinkedIn RapidAPI.")
        return

    df = pd.DataFrame(all_results)

    directorio = f"data/outputs/{fuente}/{carrera.replace(' ', '_')}"
    os.makedirs(directorio, exist_ok=True)
    nombre_csv = f"{directorio}/{fuente}__{query.replace(' ', '_')}__{HOY}.csv"

    if os.path.exists(nombre_csv):
        df_existente = pd.read_csv(nombre_csv)
        df = pd.concat([df_existente, df], ignore_index=True)
        df.drop_duplicates(subset="job_id", inplace=True)

    df.to_csv(nombre_csv, index=False)
    print(f" Archivo actualizado: {nombre_csv} ({len(df)} filas totales)")

    guardar_log(fuente, query, HOY, len(df), offset // 100)
