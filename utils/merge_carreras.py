import os
import sys
import hashlib
import pandas as pd
from dateutil import parser

# Carpeta base que contiene las subcarpetas por carrera
BASE_DIR = "../data/outputs/todas_las_plataformas"
OUT_FILENAME_PATTERN = "{carrera}_Merged.csv"

# Columnas mínimas necesarias para el UID
NEEDED_COLS = ["job_title", "company", "location", "date_posted"]

def normalize_date(value):
    """
    Devuelve YYYY-MM-DD tomando la fecha del string original,
    sin conversiones de zona horaria (no cambia el día).
    """
    if value is None or str(value).strip() == "":
        return ""
    s = str(value).strip()
    try:
        dt = parser.parse(s)
    except Exception:
        # intento alterno (dayfirst) por si acaso
        try:
            dt = parser.parse(s, dayfirst=True)
        except Exception:
            return ""
    return dt.date().isoformat()

def canonical_text(x: str) -> str:
    return "" if pd.isna(x) else str(x).strip().lower()

def make_uid(job_title, company, location, date_posted_norm):
    base = "||".join([
        canonical_text(job_title),
        canonical_text(company),
        canonical_text(location),
        canonical_text(date_posted_norm),
    ])
    return hashlib.sha256(base.encode("utf-8")).hexdigest()

def read_csv_loose(path):
    """Lee CSV tolerante a encoding/separador."""
    try:
        return pd.read_csv(path)
    except Exception:
        try:
            return pd.read_csv(path, encoding="latin-1")
        except Exception:
            try:
                return pd.read_csv(path, engine="python", sep=None)
            except Exception as e:
                print(f"⚠️  No se pudo leer: {path} ({e})")
                return pd.DataFrame()

def list_career_files(career_dir):
    """Devuelve archivos útiles dentro de la carpeta de la carrera."""
    files = []
    for f in os.listdir(career_dir):
        p = os.path.join(career_dir, f)
        if not os.path.isfile(p):
            continue
        # Acepta .csv y también nombres que terminen en __merged (aunque sin extensión)
        if f.lower().endswith(".csv") or f.endswith("__merged"):
            files.append(p)
    return sorted(files)

def merge_career_folder(career_dir):
    if not os.path.isdir(career_dir):
        print(f"⚠️  No existe la carpeta de carrera: {career_dir}")
        return

    carrera = os.path.basename(career_dir)
    files = list_career_files(career_dir)
    if not files:
        print(f"⚠️  No hay archivos para unir en: {career_dir}")
        return

    dfs = []
    for fp in files:
        df = read_csv_loose(fp)
        if df.empty:
            continue

        # Asegurar columnas mínimas
        for col in NEEDED_COLS:
            if col not in df.columns:
                df[col] = ""

        # Normalizar fecha (sin cambiar el día)
        df["date_posted_norm"] = df["date_posted"].apply(normalize_date)

        # UID cruzado con 4 campos
        df["job_uid_cross"] = df.apply(
            lambda r: make_uid(r["job_title"], r["company"], r["location"], r["date_posted_norm"]),
            axis=1
        )

        # Asegúrate de NO agregar _from_file; si existiera, elimínala
        if "_from_file" in df.columns:
            df.drop(columns=["_from_file"], inplace=True)

        dfs.append(df)

    if not dfs:
        print(f"⚠️  No se pudo construir dataframe en: {career_dir}")
        return

    merged = pd.concat(dfs, ignore_index=True)

    # Deduplicar por el nuevo UID
    before = len(merged)
    merged.drop_duplicates(subset="job_uid_cross", inplace=True)
    after = len(merged)
    removed = before - after

    out_path = os.path.join(career_dir, OUT_FILENAME_PATTERN.format(carrera=carrera))
    merged.to_csv(out_path, index=False)
    print(f"✅ {carrera}: {after} filas (elim. {removed} duplicados) → {out_path}")

def main():

    if len(sys.argv) > 1:
        merge_career_folder(sys.argv[1])
    else:
        if not os.path.isdir(BASE_DIR):
            print(f"⚠️  No existe la carpeta base: {BASE_DIR}")
            return
        for carrera in sorted(os.listdir(BASE_DIR)):
            cdir = os.path.join(BASE_DIR, carrera)
            if os.path.isdir(cdir):
                merge_career_folder(cdir)

if __name__ == "__main__":
    main()
