import os
import json
import time
import requests
import hashlib
import pandas as pd
from datetime import datetime
from utils.file_manager import guardar_log, crear_directorios, cargar_log_existente

# ===================== PARÁMETROS =====================
PLAN_MAX_JOBS_PER_MONTH = 10_000
PLAN_MAX_REQUESTS_PER_MONTH = 5_000
PLAN_MAX_JOBS_PER_CALL = 100
PLAN_MAX_RPS = 5                 # referencia
RATE_LIMIT_SLEEP = 0.25          # 1/4 seg => 4 req/seg (seguro < 5 rps)
# ================================================================

def _quota_file_path(fuente: str) -> str:
    base = f"data/outputs/{fuente}"
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, ".quota.json")

def _month_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m")  # p.ej. "2025-08"

def _load_quota(fuente: str, month_key: str) -> dict:
    """Carga o inicializa contadores de la cuota mensual."""
    path = _quota_file_path(fuente)
    if os.path.exists(path):
        try:
            data = json.load(open(path, "r", encoding="utf-8"))
        except Exception:
            data = {}
    else:
        data = {}

    if month_key not in data:
        data[month_key] = {
            "requests_used": 0,
            "jobs_used": 0
        }
    return data

def _save_quota(fuente: str, data: dict) -> None:
    path = _quota_file_path(fuente)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generar_job_id(titulo, empresa, ubicacion, fecha):
    cadena = f"{titulo}_{empresa}_{ubicacion}_{fecha}"
    return hashlib.sha256(cadena.encode('utf-8')).hexdigest()

def _safe_request_get(url, headers, params, timeout=30, max_retries=3):
    """
    GET con reintentos y backoff ante 429/5xx.
    Respeta un pequeño sleep fijo para no exceder 5 rps.
    """
    attempt = 0
    backoff = 1.0
    while True:
        # Rate limiting simple (≤ 4 rps)
        time.sleep(RATE_LIMIT_SLEEP)
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=timeout)
        except requests.RequestException as e:
            attempt += 1
            if attempt > max_retries:
                print(f"  Error de red tras {attempt} intentos: {e}")
                return None
            time.sleep(backoff)
            backoff = min(backoff * 2, 8.0)
            continue

        if resp.status_code == 200:
            return resp

        # Manejo de límites y errores transitorios
        if resp.status_code in (429, 500, 502, 503, 504):
            attempt += 1
            if attempt > max_retries:
                print(f"  HTTP {resp.status_code} tras {attempt} intentos. Abortando.")
                return resp  # devolvemos para que el caller decida
            # Respetar Retry-After si viene
            retry_after = resp.headers.get("Retry-After")
            wait_s = float(retry_after) if retry_after else backoff
            print(f"  HTTP {resp.status_code}. Reintentando en {wait_s:.1f}s...")
            time.sleep(wait_s)
            backoff = min(backoff * 2, 16.0)
            continue

        # Códigos no recuperables
        print(f"  Error HTTP {resp.status_code}")
        return resp

def buscar_linkedin_rapidapi(query, api_key, limit=100, offset=0, include_ai=False):
    url = "https://linkedin-job-search-api.p.rapidapi.com/active-jb-7d"

    # Asegurar límite del plan por llamada
    limit = max(1, min(int(limit), PLAN_MAX_JOBS_PER_CALL))

    querystring = {
        "limit": str(limit),
        "offset": str(offset),
        "title_filter": f"\"{query}\"",
        "description_type": "text"
    }
    if include_ai:
        querystring["include_ai"] = "true"

    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "linkedin-job-search-api.p.rapidapi.com"
    }

    response = _safe_request_get(url, headers, querystring, timeout=30, max_retries=3)
    if response is None:
        return []
    if response.status_code != 200:
        # Si llegamos aquí con error no recuperable
        return []

    try:
        jobs = response.json()
    except Exception as e:
        print(" Error al parsear JSON:", e)
        return []

    print(f"  Recuperados {len(jobs)} empleos (offset={offset}, limit={limit})")
    return jobs

def normalizar(oferta, fuente, fecha, carrera_tag):
    # Primero construir location_str
    locations_raw = oferta.get("locations_derived") or []
    locations = []
    for loc in locations_raw:
        if isinstance(loc, dict):
            location_text = ", ".join(filter(None, [
                loc.get("city", ""),
                loc.get("admin", ""),
                loc.get("country", "")
            ]))
            locations.append(location_text)
        elif isinstance(loc, str):
            locations.append(loc)
        else:
            locations.append("")
    location_str = "; ".join(locations)

    # Luego generar uid usando location_str
    uid = generar_job_id(
        oferta.get('title', ''),
        oferta.get('organization', ''),
        location_str,
        oferta.get("date_posted", "")
    )

    return {
        "job_id": hashlib.sha256(uid.encode()).hexdigest(),
        "source": fuente,
        "job_title": oferta.get("title", ""),
        "company": oferta.get("organization", ""),
        "location": location_str,
        "description": oferta.get("description_text", ""),
        "skills": oferta.get("ai_key_skills", []) if "ai_key_skills" in oferta else [],
        "careers_required": carrera_tag,
        "date_posted": oferta.get("date_posted", ""),
        "url": oferta.get("url", ""),
        "career_tag": "",
        "soft_skills_detected": [],
        "extraction_date": fecha
    }

def extraer_desde_rapidapi_2(query, api_key, carrera, include_ai=False):
    HOY_DT = datetime.now()
    HOY = HOY_DT.strftime("%Y-%m-%d")
    MES = _month_key(HOY_DT)

    fuente = "rapidapi2"
    crear_directorios()

    # ====== INICIALIZA CUOTA ======
    quota_data = _load_quota(fuente, MES)
    requests_used = quota_data[MES]["requests_used"]
    jobs_used = quota_data[MES]["jobs_used"]

    remaining_requests = max(0, PLAN_MAX_REQUESTS_PER_MONTH - requests_used)
    remaining_jobs = max(0, PLAN_MAX_JOBS_PER_MONTH - jobs_used)

    if remaining_requests <= 0 or remaining_jobs <= 0:
        print(f" Cuota mensual agotada para {MES}. Requests usados: {requests_used}, Jobs usados: {jobs_used}.")
        return
    # ============================================

    log = cargar_log_existente(fuente)

    # Reanudación por día (tu lógica original)
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
        # Si no queda cuota, salimos
        remaining_requests = max(0, PLAN_MAX_REQUESTS_PER_MONTH - quota_data[MES]["requests_used"])
        remaining_jobs = max(0, PLAN_MAX_JOBS_PER_MONTH - quota_data[MES]["jobs_used"])
        if remaining_requests <= 0 or remaining_jobs <= 0:
            print(" Corte por cuota mensual alcanzada.")
            break

        # Ajustar limit por jobs restantes y por tope del plan por llamada
        limit_for_this_call = min(PLAN_MAX_JOBS_PER_CALL, remaining_jobs)
        if limit_for_this_call <= 0:
            break

        # Llamada a la API (consume 1 request)
        results = buscar_linkedin_rapidapi(
            query, api_key,
            limit=limit_for_this_call,
            offset=offset,
            include_ai=include_ai
        )

        # Actualizar cuota de requests
        quota_data[MES]["requests_used"] += 1

        if not results:
            break

        # Normalización y acumulado
        normalized = [normalizar(o, fuente, HOY, carrera) for o in results]
        all_results.extend(normalized)

        # Actualizar cuota de jobs
        quota_data[MES]["jobs_used"] += len(results)
        total_extraidos += len(results)

        # Guardar cuota periódicamente para no perder estado
        _save_quota(fuente, quota_data)

        offset += PLAN_MAX_JOBS_PER_CALL  # seguimos con tu lógica de paginado por múltiplos de 100

        # Si llegó menos de lo pedido, no hay más páginas
        if len(results) < limit_for_this_call:
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

    # Guarda tu log como siempre (no toco firma)
    # last_page_extracted = offset // 100 (consistente con tu paginado original)
    guardar_log(fuente, query, HOY, len(df), offset // 100)

    # Guardar cuota final del ciclo
    _save_quota(fuente, quota_data)
