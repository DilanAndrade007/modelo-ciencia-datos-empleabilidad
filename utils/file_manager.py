import os, json
import pandas as pd
import glob
import shutil
import hashlib
from dateutil import parser
# Importar funciones de extracción de países
try:
    from .location_extractor import country_from_location, clean_text
except ImportError:
    from location_extractor import country_from_location, clean_text

NEEDED_COLS = ["job_title", "company", "location", "date_posted"]

def normalize_date(value):
    """Devuelve YYYY-MM-DD sin cambiar el día."""
    if value is None or str(value).strip() == "":
        return ""
    s = str(value).strip()
    for kwargs in ({}, {"dayfirst": True}):
        try:
            return parser.parse(s, **kwargs).date().isoformat()
        except Exception:
            pass
    return ""

def canonical_text(x) -> str:
    return "" if pd.isna(x) else str(x).strip().lower()

def make_uid(job_title, company, location, date_posted_norm):
    base = "||".join(map(canonical_text, [job_title, company, location, date_posted_norm]))
    return hashlib.sha256(base.encode("utf-8")).hexdigest()

def read_csv_loose(path: str) -> pd.DataFrame:
    """Lector tolerante a encoding/separador."""
    for kwargs in ({}, {"engine": "python", "sep": None}, {"encoding": "latin-1"}):
        try:
            return pd.read_csv(path, **kwargs)
        except Exception:
            continue
    print(f"⚠️  No se pudo leer: {path}")
    return pd.DataFrame()

def crear_directorios():
    os.makedirs("data/outputs", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs("config", exist_ok=True)

def copiar_corpus_diario_a_global(fuente, carrera, fecha):
    """
    Copia el archivo de corpus unificado diario de una carrera desde la plataforma
    hacia la carpeta 'todas_las_plataformas/<Carrera>/', conservando el nombre de origen.
    """
    origen = os.path.join(
        "data", "outputs", fuente, carrera.replace(" ", "_"),
        "corpus_unido", f"{fuente}__{carrera.replace(' ', '_')}__{fecha}__merged.csv"
    )
    destino_dir = os.path.join("data", "outputs", "todas_las_plataformas", carrera.replace(" ", "_"))
    os.makedirs(destino_dir, exist_ok=True)
    destino = os.path.join(destino_dir, os.path.basename(origen))

    if os.path.exists(origen):
        shutil.copy2(origen, destino)
        print(f"🗂️  Copiado a carpeta global: {destino}")
    else:
        print(f"⚠️  No se encontró el archivo diario para copiar: {origen}")

def unir_corpus_acumulado_por_carrera():
    """
    Deduplica por 'job_id' y guarda '<Carrera>_Merged.csv' en la carpeta de cada carrera.
    """
    base_global = os.path.join("data", "outputs", "todas_las_plataformas")

    carreras = sorted(
        d for d in os.listdir(base_global)
        if os.path.isdir(os.path.join(base_global, d))
    )

    for carrera_dirname in carreras:
        cdir = os.path.join(base_global, carrera_dirname)
        archivos = sorted(
            p for p in os.listdir(cdir)
            if os.path.isfile(os.path.join(cdir, p))
            and (p.lower().endswith(".csv") or p.endswith("__merged"))
        )

        if not archivos:
            print(f"⚠️  {carrera_dirname}: no hay archivos para unir.")
            continue

        dfs = []
        total_reemplazos = 0

        for fname in archivos:
            path = os.path.join(cdir, fname)
            df = read_csv_loose(path)
            if df.empty:
                print(f"⚠️  No se pudo leer o vacío: {path}")
                continue

            # Asegurar columnas mínimas
            for col in NEEDED_COLS:
                if col not in df.columns:
                    df[col] = ""

            # Normalizar fecha y recalcular/sobrescribir job_id
            df["date_posted_norm"] = df["date_posted"].apply(normalize_date)

            old_job_id = df["job_id"].astype(str) if "job_id" in df.columns else None
            df["job_id"] = df.apply(
                lambda r: make_uid(r["job_title"], r["company"], r["location"], r["date_posted_norm"]),
                axis=1
            )
            if old_job_id is not None:
                changed = (old_job_id != df["job_id"].astype(str))
                total_reemplazos += int(changed.sum())

            dfs.append(df)

        merged = pd.concat(dfs, ignore_index=True)

        # Deduplicar por job_id
        before = len(merged)
        merged.drop_duplicates(subset="job_id", inplace=True)
        removed = before - len(merged)

        # Crear columna location_final con países extraídos
        if "location" in merged.columns:
            print(f"  📍 Extrayendo países de {len(merged)} ubicaciones...")
            merged["location_final"] = merged["location"].astype(str).apply(
                lambda x: clean_text(country_from_location(x)) if x and str(x).strip() not in ['', 'nan', 'None'] else ""
            )

        # Reordenar columnas: date_posted_norm después de date_posted, location_final después de location
        cols = list(merged.columns)
        
        # Mover date_posted_norm
        if "date_posted" in cols and "date_posted_norm" in cols:
            cols.remove("date_posted_norm")
            insert_at = cols.index("date_posted") + 1 if "date_posted" in cols else len(cols)
            cols.insert(insert_at, "date_posted_norm")
        
        # Mover location_final
        if "location" in cols and "location_final" in cols:
            cols.remove("location_final")
            insert_at = cols.index("location") + 1 if "location" in cols else len(cols)
            cols.insert(insert_at, "location_final")
        
        merged = merged[cols]

        out_path = os.path.join(cdir, f"{carrera_dirname}_Merged.csv")
        merged.to_csv(out_path, index=False)
        extra = f" | job_id sobrescritos: {total_reemplazos}" if total_reemplazos else ""
        print(f"- {carrera_dirname}: {len(merged)} filas (elim. {removed} duplicados){extra} → {out_path}")

def unir_corpus_por_carrera(fuente, carrera, fecha):
    """
    Une todos los CSVs de una carrera para una plataforma y fecha dada.
    Guarda el resultado en 'corpus_unido/' dentro de la carpeta de la carrera.
    """
    base_path = os.path.join("data", "outputs", fuente, carrera.replace(" ", "_"))
    patron = os.path.join(base_path, f"{fuente}__*__{fecha}.csv")
    archivos_csv = glob.glob(patron)

    if not archivos_csv:
        print(f"No se encontraron archivos para unir en {base_path}")
        return

    # Cargar y concatenar
    dfs = [pd.read_csv(f) for f in archivos_csv]
    df_unido = pd.concat(dfs, ignore_index=True).drop_duplicates(subset="job_id")

    # Guardar en subcarpeta corpus_unido/
    output_dir = os.path.join(base_path, "corpus_unido")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{fuente}__{carrera.replace(' ', '_')}__{fecha}__merged.csv")
    df_unido.to_csv(output_file, index=False)

    print(f"Corpus unificado guardado en: {output_file} ({len(df_unido)} filas)")

def guardar_log(fuente, consulta, fecha, total=None, pagina=None, ubicaciones_finales=None):
    """
    Guarda o actualiza el log de extracción:
    - Si ubicaciones_finales es None: guarda plano (por término).
    - Si ubicaciones_finales es dict: guarda anidado por ubicación.
    """
    log_path = os.path.join("logs", f"{fuente}_log.json")

    # Cargar log existente
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            log = json.load(f)
    else:
        log = {}

    if ubicaciones_finales:
        if consulta not in log:
            log[consulta] = {}
        for loc, info in ubicaciones_finales.items():
            log[consulta][loc] = {
                "last_extraction_date": fecha,
                "last_page_extracted": info.get("last_page_extracted", 0),
                "total_extracted": info.get("total_extracted", 0),
            }
    else:
        log[consulta] = {
            "last_extraction_date": fecha,
            "total_offers_extracted": total,
            "last_page_extracted": pagina,
        }

    # Guardar
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    print(f"Log actualizado → {log_path}")

def cargar_log_existente(fuente):
    """
    Retorna el diccionario de log de la plataforma si existe, o un dict vacío si no.
    """
    log_path = os.path.join("logs", f"{fuente}_log.json")
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}
