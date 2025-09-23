# ====================== DEPENDENCIAS ======================
import re, html, unicodedata, time, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from ftfy import fix_text
import emoji
from tqdm.auto import tqdm
from deep_translator import GoogleTranslator


# ======================= CONFIGURACIÓN =====================
BASE_GLOBAL = Path("/content/drive/MyDrive/todas_las_plataformas")
DESCRIPTION_COL = "description"
NEW_COL = "description_final"
ONLY_THIS_CAREER = None            # p.ej. "Administración_de_Empresas" o None para todas

# Rendimiento
MAX_WORKERS = 2                    # 2–4 si no te limita
CHUNK_LIMIT = 4500                 # margen seguro (<~5000) por llamada

# Reintentos / control de fallos
FAIL_MARKER = "[GT_FAIL] "         # prefijo cuando falla la traducción
RETRY_ONLY_FAILED_FROM_CSV = True  # al relanzar, solo reintenta FAIL o vacías
RETRY_PREV_FAIL = True             # reintenta en esta sesión aunque esté cacheado como FAIL

# Menos ruido en consola (solo progreso y mensajes clave)
# ===========================================================


# URLs, e-mails, HTML
URL_RE = re.compile(r"(https?://\S+|www\.\S+)")
EMAIL_RE = re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w{2,}\b")
HTML_TAG_RE = re.compile(r"<[^>]+>")

# Espacios/puntuación
WS_RE = re.compile(r"\s+")
SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([,.;:!?])")
PUNCT_DUP_RE = re.compile(r"([.!?])\1{1,}")     # "!!" -> "!"
DOT_SPACE_FIX_RE = re.compile(r"\s*\.\s*")       # normalizar espacios alrededor de "."

# Markdown/ruido
MD_STRONG_EM_RE = re.compile(r"(\*\*|__)+")      # **, __
MD_INLINE_EM_RE = re.compile(r"(^|[\s\W])(\*|_)(.+?)(\2)($|[\s\W])", re.DOTALL)  # *texto* / _texto_
PIPE_RE = re.compile(r"\s*\|\s*")                # " | " -> ". "
UNDERSCORES_RUN_RE = re.compile(r"_{2,}")        # "__", "____" -> ". "
LEADING_BULLET_RE = re.compile(r"^\s*[•\-\–\—\·\‣\∙\●\○\▪\▫\►\➤]\s*", re.MULTILINE)

# Encabezados y hashes (#, ##, …)
HASH_HEADING_RE = re.compile(r"(?m)^\s{0,3}#{1,6}\s*")  # quitar encabezados Markdown
HASH_INLINE_RE = re.compile(r"#+")  

# --- Variantes de Q&A ---
QA_VARIANTS = [
    re.compile(r'(?i)\bq\s*&\s*a\b'),          # Q & A
    re.compile(r'(?i)\bq\s*/\s*a\b'),          # Q/A
    re.compile(r'(?i)\bq\s*[-–—]\s*a\b'),      # Q-A, Q – A, Q — A
]

def normalize_qa_terms(s: str) -> str:
    # 1) Unificar todas las variantes a "QA"
    for pat in QA_VARIANTS:
        s = pat.sub("QA", s)
    # 2) Expandir "QA" si no está ya expandido (evita duplicar)
    s = re.sub(r'\bQA\b(?!\s*\()', 'QA (Quality Assurance)', s)
    return s

def normalize_unicode(s: str) -> str:
    s = fix_text(s)
    s = html.unescape(s)
    return unicodedata.normalize("NFC", s)

def _strip_markdown_and_layout(s: str) -> str:
    # Quitar HTML, URLs y e-mails
    s = HTML_TAG_RE.sub(" ", s)
    s = URL_RE.sub(" ", s)
    s = EMAIL_RE.sub(" ", s)

    # Quitar emojis
    s = emoji.replace_emoji(s, " ")

    # Quitar viñetas al inicio de línea
    s = LEADING_BULLET_RE.sub("", s)

    # Quitar encabezados y hashes (#)
    s = HASH_HEADING_RE.sub("", s)
    s = HASH_INLINE_RE.sub(" ", s)

    # Quitar negritas/cursivas Markdown ** __ * _
    s = MD_STRONG_EM_RE.sub(" ", s)
    s = MD_INLINE_EM_RE.sub(lambda m: f"{m.group(1)}{m.group(3)}{m.group(5)}", s)

    # Pipes y underscores largos -> separadores ". "
    s = PIPE_RE.sub(". ", s)
    s = UNDERSCORES_RUN_RE.sub(". ", s)

    # Guiones medios/largos como separadores suaves
    s = re.sub(r"\s*[–—]\s*", ". ", s)

    return s

def _fix_spacing_and_punct(s: str) -> str:
    # Quitar espacios antes de puntuación
    s = SPACE_BEFORE_PUNCT_RE.sub(r"\1", s)

    # Normalizar puntos y espacios
    s = DOT_SPACE_FIX_RE.sub(". ", s)     # ". " estándar
    s = re.sub(r"\.\s+\.", ". ", s)       # ".  ." -> ". "

    # Colapsar repeticiones de signos "!!!" -> "!"
    s = PUNCT_DUP_RE.sub(r"\1", s)

    # Si quedó " . " al final -> "."
    s = re.sub(r"\s+\.$", ".", s)

    return s

def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""

    s = normalize_unicode(text)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = s.replace("\n•", "\n")
    s = s.replace("\n", ". ")

    s = _strip_markdown_and_layout(s)

    # >>> normaliza Q&A aquí <<<
    s = normalize_qa_terms(s)

    s = _fix_spacing_and_punct(s)
    s = WS_RE.sub(" ", s).strip()
    return s


# ==================== LECTURA ROBUSTA CSV =====================
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


# ================== TRADUCTOR POR HILO + CACHÉ =================
_thread_local = threading.local()
_global_cache = {}  # texto_limpio -> traducción o FAIL_MARKER+texto

def _get_translator():
    gt = getattr(_thread_local, "gt", None)
    if gt is None:
        gt = GoogleTranslator(source="auto", target="es")
        _thread_local.gt = gt
    return gt

def _split_into_chunks(text: str, limit: int = CHUNK_LIMIT):
    """Divide en <=limit, intenta cortar por final de frase; si no, corta duro."""
    if len(text) <= limit:
        return [text]
    parts = re.split(r'(?<=[\.\!\?\;:])\s+', text)
    chunks, cur = [], ""
    for p in parts:
        if not p:
            continue
        add = len(p) + (1 if cur else 0)
        if len(cur) + add <= limit:
            cur = f"{cur} {p}".strip() if cur else p
        else:
            if cur:
                chunks.append(cur)
            if len(p) > limit:
                for i in range(0, len(p), limit):
                    chunks.append(p[i:i+limit])
                cur = ""
            else:
                cur = p
    if cur:
        chunks.append(cur)
    return chunks

def _translate_text_with_fail(text: str) -> str:
    """
    Traduce con troceo + 3 reintentos por trozo.
    Si cualquier trozo falla, devuelve FAIL_MARKER + texto original.
    """
    if not text:
        return ""
    # caché de sesión
    cached = _global_cache.get(text)
    if cached is not None:
        if RETRY_PREV_FAIL and isinstance(cached, str) and cached.startswith(FAIL_MARKER):
            pass  # reintenta en esta sesión
        else:
            return cached

    gt = _get_translator()
    outs = []
    for ch in _split_into_chunks(text, CHUNK_LIMIT):
        ok = False
        delay = 2.0
        for _ in range(3):
            try:
                out = gt.translate(ch)
                if not isinstance(out, str) or out.strip() == "":
                    raise RuntimeError("empty")
                outs.append(out)
                ok = True
                break
            except Exception:
                time.sleep(delay)  # backoff 2s, 4s, 8s
                delay *= 2
        if not ok:
            fail_val = f"{FAIL_MARKER}{text}"
            _global_cache[text] = fail_val
            return fail_val

    final = " ".join(outs)
    _global_cache[text] = final
    return final


# ===== TRADUCIR SOLO ÚNICOS (omite vacíos) + MAPEO RÁPIDO =====
def translate_series_unique_multithread(series: pd.Series, max_workers: int = 3) -> pd.Series:
    """
    - Traduce solo valores únicos no vacíos ('' se omiten y se dejan tal cual).
    - Usa hilos y caché en memoria para acelerar.
    """
    texts = series.fillna("").astype(str)

    # únicos no vacíos
    uniques = [u for u in texts.unique().tolist() if u != ""]

    # únicos realmente pendientes (no en caché, o FAIL y queremos reintentar)
    to_do = []
    for u in uniques:
        v = _global_cache.get(u)
        if v is None:
            to_do.append(u)
        elif RETRY_PREV_FAIL and isinstance(v, str) and v.startswith(FAIL_MARKER):
            to_do.append(u)

    if to_do:
        def worker(u):
            return u, _translate_text_with_fail(u)
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            for u, out in tqdm(ex.map(worker, to_do), total=len(to_do),
                               desc="Traduciendo únicos", unit="texto"):
                _global_cache[u] = out

    # mapear: vacíos quedan como "", el resto toma de la caché
    return texts.map(lambda x: _global_cache.get(x, x))


# ===================== PROCESAMIENTO POR CSV ====================
def process_file(target_file: Path):
    try:
        df = read_csv_robust(target_file)
    except Exception as e:
        print(f"[ERROR] Leyendo {target_file.name}: {e}")
        return

    if DESCRIPTION_COL not in df.columns:
        print(f"[WARN] No hay columna '{DESCRIPTION_COL}' en {target_file.name}")
        return

    total = len(df)
    print(f"\n[INFO] Procesando {target_file.name} ({total} filas)")

    cleaned = df[DESCRIPTION_COL].fillna("").apply(clean_text)
    mask_desc_empty = cleaned.eq("")  # filas sin descripción -> no tocar

    if NEW_COL in df.columns and RETRY_ONLY_FAILED_FROM_CSV:
        col = df[NEW_COL].astype(str) if NEW_COL in df.columns else pd.Series("", index=df.index)
        mask_fail  = col.str.startswith(FAIL_MARKER, na=False)
        mask_empty_final = df[NEW_COL].isna() | df[NEW_COL].eq("") if NEW_COL in df.columns else pd.Series(True, index=df.index)
        # pendientes = filas con descripción (no vacías) y final FAIL o vacío
        mask_pending = (~mask_desc_empty) & (mask_fail | mask_empty_final)

        n_pending = int(mask_pending.sum())
        n_skip = int(len(df) - n_pending)
        print(f"[INFO] Reintentando solo pendientes (con descripción): {n_pending} filas | conservando {n_skip} restantes")

        if n_pending > 0:
            translated_pending = translate_series_unique_multithread(
                cleaned[mask_pending], max_workers=MAX_WORKERS
            )
            if NEW_COL not in df.columns:
                df[NEW_COL] = ""
            df.loc[mask_pending, NEW_COL] = translated_pending
        else:
            print("[INFO] No hay pendientes que reintentar.")
    else:
        # Pase completo: traducir solo filas con descripción
        translated = translate_series_unique_multithread(
            cleaned[~mask_desc_empty], max_workers=MAX_WORKERS
        )
        # crear/actualizar solo en las filas con descripción
        if NEW_COL not in df.columns:
            df[NEW_COL] = ""
        df.loc[~mask_desc_empty, NEW_COL] = translated

    # Guardar
    try:
        df.to_csv(target_file, index=False, encoding="utf-8")
    except Exception:
        df.to_csv(target_file, index=False, encoding="utf-8-sig")

    print(f"[OK] Guardado en {target_file}\n")


# ===================== RECORRER TODAS LAS CARRERAS ====================
def process_all():
    if not BASE_GLOBAL.exists():
        raise FileNotFoundError(f"No existe la ruta base: {BASE_GLOBAL}")

    carrera_dirs = [p for p in BASE_GLOBAL.iterdir() if p.is_dir()]
    if ONLY_THIS_CAREER:
        carrera_dirs = [d for d in carrera_dirs if d.name == ONLY_THIS_CAREER]
    if not carrera_dirs:
        print("[WARN] No se encontraron carpetas de carrera para procesar.")
        return

    for carrera_dir in sorted(carrera_dirs, key=lambda x: x.name.lower()):
        expected_name = f"{carrera_dir.name}_Merged.csv"
        target_file = carrera_dir / expected_name
        if not target_file.exists():
            print(f"[SKIP] No existe {expected_name} en {carrera_dir.name}")
            continue
        process_file(target_file)


# =========================== EJECUCIÓN ==========================
process_all()
