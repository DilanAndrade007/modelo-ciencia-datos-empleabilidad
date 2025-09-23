# =============== TRADUCIR COLUMNA "skills" A ESPAÑOL (salida: "item1, item2, ...") ===============
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import ast
import re
import pandas as pd
from tqdm.auto import tqdm
from deep_translator import GoogleTranslator

# ---------------- CONFIG ----------------
BASE_GLOBAL = Path("/content/drive/MyDrive/todas_las_plataformas")
SKILLS_COL = "skills"
ONLY_THIS_CAREER = None          # p.ej., "Administración_de_Empresas" o None para todas

MAX_WORKERS = 3                  # 2–4 si no te limita
RETRIES_PER_ITEM = 3             # reintentos por skill
RETRY_SLEEP_BASE = 1.5           # 1.5s, 3s, 4.5s ...

# ---------------- THREAD-LOCAL TRANSLATOR ----------------
_thread_local = threading.local()
_global_cache: dict[str, str] = {}  # skill_original -> skill_traducida

def _get_translator():
    gt = getattr(_thread_local, "gt", None)
    if gt is None:
        gt = GoogleTranslator(source="auto", target="es")
        _thread_local.gt = gt
    return gt

def _translate_item(text: str) -> str:
    """Traduce un ítem (string corto). Si falla tras reintentos, devuelve el original."""
    if not isinstance(text, str):
        return text
    t = text.strip()
    if t == "":
        return ""
    cached = _global_cache.get(t)
    if isinstance(cached, str):
        return cached

    delay = RETRY_SLEEP_BASE
    for _ in range(RETRIES_PER_ITEM):
        try:
            out = _get_translator().translate(t)
            if isinstance(out, str) and out.strip():
                _global_cache[t] = out.strip()
                return _global_cache[t]
            raise RuntimeError("empty result")
        except Exception:
            time.sleep(delay)
            delay += RETRY_SLEEP_BASE

    _global_cache[t] = t  # conserva original si falló todo
    return t

# ---------------- LECTURA ROBUSTA ----------------
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

# ---------------- PARSEAR COLUMNA SKILLS ----------------
BRACKETS_EMPTY_RE = re.compile(r"^\s*\[\s*\]\s*$")

def parse_skills_cell(cell) -> list[str] | None:
    """
    Devuelve lista de strings o None si la celda está vacía.
    Trata como vacío: NaN, "", "[]", "[   ]".
    Si viene como lista Python en string -> ast.literal_eval.
    Si no, intenta split por comas.
    """
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return None
    s = str(cell).strip()
    if s == "" or BRACKETS_EMPTY_RE.match(s):
        return None

    # ¿es una lista literal? (soporta comillas simples/dobles estilo Python/JSON)
    if s.startswith("[") and s.endswith("]"):
        try:
            obj = ast.literal_eval(s)
            if isinstance(obj, list):
                out = []
                for x in obj:
                    if x is None:
                        continue
                    t = str(x).strip()
                    if t != "":
                        out.append(t)
                return out if out else None
        except Exception:
            pass

    # fallback: separar por comas
    parts = [p.strip() for p in s.split(",")]
    parts = [p for p in parts if p]
    return parts if parts else None

def format_skills_plain(skills: list[str]) -> str:
    """Serializa como 'item1, item2, item3' (sin comillas ni corchetes)."""
    return ", ".join(skills)

# ---------------- TRADUCCIÓN ÚNICOS + MAPEO ----------------
def translate_skills_series(series: pd.Series, max_workers: int = 3) -> pd.Series:
    """
    - Parsea cada celda a lista de strings (o None si vacía).
    - Traduce solo los ítems únicos (multihilo + caché).
    - Reconstruye cada celda preservando el orden; vacías -> "" (celda en blanco).
    """
    parsed = series.apply(parse_skills_cell)

    # recolecta ítems únicos a traducir
    uniq_items = []
    seen = set()
    for lst in parsed:
        if not lst:
            continue
        for it in lst:
            if it not in seen:
                seen.add(it)
                uniq_items.append(it)

    # traduce únicos pendientes
    if uniq_items:
        def worker(u):
            return u, _translate_item(u)
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            for u, out in tqdm(ex.map(worker, uniq_items), total=len(uniq_items),
                               desc="Traduciendo skills únicas", unit="skill"):
                _global_cache[u] = out

    # reconstruye celdas
    out_series = []
    for lst in parsed:
        if not lst:
            out_series.append("")  # celda vacía
        else:
            translated = [_global_cache.get(x, x) for x in lst]
            out_series.append(format_skills_plain(translated))

    return pd.Series(out_series, index=series.index)

# ---------------- PROCESO POR ARCHIVO ----------------
def process_file(path: Path):
    try:
        df = read_csv_robust(path)
    except Exception as e:
        print(f"[ERROR] Leyendo {path.name}: {e}")
        return

    if SKILLS_COL not in df.columns:
        print(f"[WARN] No hay columna '{SKILLS_COL}' en {path.name}")
        return

    total = len(df)
    print(f"\n[INFO] Procesando {path.name} ({total} filas)")

    df[SKILLS_COL] = translate_skills_series(df[SKILLS_COL], max_workers=MAX_WORKERS)

    # guardar
    try:
        df.to_csv(path, index=False, encoding="utf-8")
    except Exception:
        df.to_csv(path, index=False, encoding="utf-8-sig")

    print(f"[OK] Guardado en {path}.\n")

# ---------------- RECORRER TODAS LAS CARRERAS ----------------
def run_all():
    base = BASE_GLOBAL
    if not base.exists():
        raise FileNotFoundError(f"No existe la ruta base: {base}")

    dirs = [p for p in base.iterdir() if p.is_dir()]
    if ONLY_THIS_CAREER:
        dirs = [d for d in dirs if d.name == ONLY_THIS_CAREER]
    if not dirs:
        print("[WARN] No se encontraron carpetas.")
        return

    for d in sorted(dirs, key=lambda x: x.name.lower()):
        expected = d / f"{d.name}_Merged.csv"
        if not expected.exists():
            print(f"[SKIP] No existe {expected.name} en {d.name}")
            continue
        process_file(expected)

# ---------------- EJECUCIÓN ----------------
run_all()
