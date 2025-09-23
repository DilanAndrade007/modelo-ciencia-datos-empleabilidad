import os
import sys
import hashlib
import pandas as pd
from dateutil import parser

BASE_DIR = "../data/outputs/todas_las_plataformas"
OUT_FILENAME_PATTERN = "{carrera}_Merged.csv"
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
    for kwargs in ({}, {"engine": "python", "sep": None}, {"encoding": "latin-1"}):
        try:
            return pd.read_csv(path, **kwargs)
        except Exception:
            continue
    print(f"⚠️  No se pudo leer: {path}")
    return pd.DataFrame()

def list_career_files(career_dir: str):
    return sorted(
        p for f in os.listdir(career_dir)
        for p in [os.path.join(career_dir, f)]
        if os.path.isfile(p) and (p.lower().endswith(".csv") or p.endswith("__merged"))
    )

def merge_career_folder(career_dir: str):
    if not os.path.isdir(career_dir):
        print(f"⚠️  No existe la carpeta de carrera: {career_dir}")
        return

    carrera = os.path.basename(career_dir)
    files = list_career_files(career_dir)
    if not files:
        print(f"⚠️  No hay archivos para unir en: {career_dir}")
        return

    dfs = []
    total_reemplazos = 0

    for fp in files:
        df = read_csv_loose(fp)
        if df.empty:
            continue

        for col in NEEDED_COLS:
            if col not in df.columns:
                df[col] = ""

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

    if not dfs:
        print(f"⚠️  No se pudo construir dataframe en: {career_dir}")
        return

    merged = pd.concat(dfs, ignore_index=True)

    before = len(merged)
    merged.drop_duplicates(subset="job_id", inplace=True)
    removed = before - len(merged)

    # ⬇️ Reordenar: date_posted_norm inmediatamente después de date_posted
    if "date_posted" in merged.columns and "date_posted_norm" in merged.columns:
        cols = list(merged.columns)
        # quitar y reinsertar
        cols.remove("date_posted_norm")
        idx = cols.index("date_posted") + 1
        cols.insert(idx, "date_posted_norm")
        merged = merged[cols]

    out_path = os.path.join(career_dir, OUT_FILENAME_PATTERN.format(carrera=carrera))
    merged.to_csv(out_path, index=False)
    msg_extra = f" | job_id sobrescritos: {total_reemplazos}" if total_reemplazos else ""
    print(f"✅ {carrera}: {len(merged)} filas (elim. {removed} duplicados){msg_extra} → {out_path}")

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
