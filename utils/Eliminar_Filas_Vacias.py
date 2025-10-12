# ======= BORRAR FILAS SIN CONTENIDO EN description NI skills (considera "[]") =======
from pathlib import Path
import re
import pandas as pd

# -------- Config --------
BASE_GLOBAL = Path(r"C:\Users\andra\Documents\Proyects\TICs\Corpus\Jobs_ScalperV2\modelo-ciencia-datos-empleabilidad\data\outputs\todas_las_plataformas")
DESCRIPTION_COL = "description"
SKILLS_COL = "skills"
ONLY_THIS_CAREER = None  # p.ej. "Administración_de_Empresas" o None para todas

# -------- Lectura robusta --------
def read_csv_robust(path: Path) -> pd.DataFrame:
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except Exception:
            pass
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc, sep=";", low_memory=False)
        except Exception:
            pass
    raise RuntimeError(f"No se pudo leer el CSV: {path}")

# -------- Criterio de "vacío" --------
BRACKETS_EMPTY_RE = re.compile(r"^\s*\[\s*\]\s*$")  # coincide con [], [   ], etc.

def series_is_empty_like(s: pd.Series) -> pd.Series:
    """
    Vacío si:
      - NaN
      - cadena vacía / solo espacios
      - exactamente "[]", "[   ]", etc.
    """
    if s is None:
        # si la columna no existe, considérala toda vacía
        return pd.Series(True, index=pd.RangeIndex(0))
    # Convertimos a string preservando NaN para chequearlos explícitamente
    is_na = s.isna()
    as_str = s.astype(str)
    is_blank = as_str.str.strip().eq("")
    is_brackets = as_str.str.match(BRACKETS_EMPTY_RE)
    return is_na | is_blank | is_brackets

# -------- Proceso por archivo --------
def clean_file(file_path: Path):
    try:
        df = read_csv_robust(file_path)
    except Exception as e:
        print(f"[ERROR] {file_path.name}: {e}")
        return

    n_before = len(df)
    if n_before == 0:
        print(f"[SKIP] {file_path.name}: vacío.")
        return

    # Si faltan columnas, las tratamos como vacías
    desc = df[DESCRIPTION_COL] if DESCRIPTION_COL in df.columns else pd.Series([None]*n_before)
    skills = df[SKILLS_COL] if SKILLS_COL in df.columns else pd.Series([None]*n_before)

    desc_empty = series_is_empty_like(desc)
    skills_empty = series_is_empty_like(skills)

    # Mantener filas donde AL MENOS una columna tiene contenido
    keep_mask = ~(desc_empty & skills_empty)
    df_kept = df[keep_mask].copy()

    removed = n_before - len(df_kept)
    if removed > 0:
        try:
            df_kept.to_csv(file_path, index=False, encoding="utf-8")
        except Exception:
            df_kept.to_csv(file_path, index=False, encoding="utf-8-sig")
        print(f"[OK] {file_path.name}: eliminadas {removed} filas (quedan {len(df_kept)}).")
    else:
        print(f"[OK] {file_path.name}: nada que eliminar ({n_before} filas).")

# -------- Recorrer todas las carreras --------
def run_all():
    base = BASE_GLOBAL
    if not base.exists():
        raise FileNotFoundError(f"No existe la ruta base: {base}")

    carreras = [p for p in base.iterdir() if p.is_dir()]
    if ONLY_THIS_CAREER:
        carreras = [d for d in carreras if d.name == ONLY_THIS_CAREER]
    if not carreras:
        print("[WARN] No se encontraron carpetas de carrera.")
        return

    for d in sorted(carreras, key=lambda x: x.name.lower()):
        target = d / f"{d.name}_Merged.csv"
        if not target.exists():
            print(f"[SKIP] No existe {target.name} en {d.name}")
            continue
        clean_file(target)

# -------- Ejecutar --------
run_all()
