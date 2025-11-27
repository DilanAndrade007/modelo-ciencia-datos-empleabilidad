# ========== NORMALIZAR 'description_final' EN *_Merged.csv (versión robusta) ==========
# Limpia HTML/URLs/emails/emojis, viñetas en TODO el texto, markdown suelto,
# separadores decorativos, tags de idioma ([SPANISH], EN:, etc.), pipes/underscores,
# colapsa ". ." repetidos, corrige espacios y puntuación.
# NO modifica filas vacías ni con [GT_FAIL].

import re, html, unicodedata
from pathlib import Path
import pandas as pd
from ftfy import fix_text
import emoji

# ------------------- CONFIG -------------------
BASE_GLOBAL = Path("/content/drive/MyDrive/todas_las_plataformas")
FINAL_COL = "description_final"
ONLY_THIS_CAREER = None          # p.ej. "Administración_de_Empresas" o None
FAIL_MARKER = "[GT_FAIL]"

# ----------------- REGEX / UTILS --------------
URL_RE = re.compile(r"(https?://\S+|www\.\S+)")
EMAIL_RE = re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w{2,}\b")
HTML_TAG_RE = re.compile(r"<[^>]+>")

WS_RE = re.compile(r"\s+")
SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([,.;:!?])")
PUNCT_DUP_RE = re.compile(r"([.!?])\1{1,}")        # "!!!" -> "!"
DOT_SPACE_FIX_RE = re.compile(r"\s*\.\s*")         # normaliza espacios alrededor de "."
MULTI_DOTS_RE = re.compile(r"(?:\.\s*){2,}")       # ". ." repetidos -> ". "
LEADING_PUNCT_RE = re.compile(r"^[\.\,\;\:\-\–\—\·\•\*]+")  # puntos/viñetas al inicio

# Markdown y decoración
MD_STRONG_EM_RE = re.compile(r"(\*\*|__)+")        # **, __
MD_INLINE_EM_RE = re.compile(r"(^|[\s\W])(\*|_)(.+?)(\2)($|[\s\W])", re.DOTALL)  # *texto* / _texto_
STRAY_STARS_RE = re.compile(r"\*+")                # asteriscos sueltos -> espacio
PIPE_RE = re.compile(r"\s*\|\s*")                  # " | " -> ". "
UNDERSCORES_RUN_RE = re.compile(r"_{2,}")          # "__", "____" -> ". "
DECORATIVE_LINE_RE = re.compile(r"(?m)^\s*([=\-_*~<>\.]{3,})\s*$")  # líneas de ====, ----, ****, ...

# Viñetas
BULLET_CHARS = "•◦·‣∙●○▪▫◆◇■□►➤–—"  # incluye guiones largos/medios
LEADING_BULLET_RE = re.compile(r"^\s*[•\-\–\—\·\‣\∙\●\○\▪\▫\►\➤]\s*", re.MULTILINE)

# Tags de idioma / encabezados tipo idioma
LANG_TAG_INLINE_RE = re.compile(r"\[\s*(spanish|english|es|en|pt|fr|de|it)\s*\]", re.I)
LANG_TAG_LINE_RE = re.compile(r"(?m)^\s*(spanish|english|es|en|pt|fr|de|it)\s*:\s*", re.I)

# Q&A → QA (Quality Assurance)
QA_VARIANTS = [
    re.compile(r'(?i)\bq\s*&\s*a\b'),
    re.compile(r'(?i)\bq\s*/\s*a\b'),
    re.compile(r'(?i)\bq\s*[-–—]\s*a\b'),
    re.compile(r'(?i)\bq\s*\+\s*a\b'),
    re.compile(r'(?i)\bq\s*y\s*a\b'),
]

def nfc(s: str) -> str:
    s = fix_text(s or "")
    s = html.unescape(s)
    return unicodedata.normalize("NFC", s)

def _strip_markdown_and_layout(s: str) -> str:
    # HTML / URLs / Emails / Emojis
    s = HTML_TAG_RE.sub(" ", s)
    s = URL_RE.sub(" ", s)
    s = EMAIL_RE.sub(" ", s)
    s = emoji.replace_emoji(s, " ")

    # Elimina tags de idioma y líneas decorativas
    s = LANG_TAG_INLINE_RE.sub(" ", s)
    s = LANG_TAG_LINE_RE.sub("", s)
    s = DECORATIVE_LINE_RE.sub(" ", s)

    # Viñetas: al inicio de línea y en todo el texto
    s = LEADING_BULLET_RE.sub("", s)
    s = s.translate({ord(ch): " " for ch in BULLET_CHARS})

    # Encabezados y hashes (#)
    s = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", s)  # #, ## al inicio
    s = re.sub(r"#+", " ", s)                    # hashes sueltos

    # Markdown ** __ * _
    s = MD_STRONG_EM_RE.sub(" ", s)
    s = MD_INLINE_EM_RE.sub(lambda m: f"{m.group(1)}{m.group(3)}{m.group(5)}", s)
    s = STRAY_STARS_RE.sub(" ", s)               # quita * sueltos

    # Pipes y underscores largos -> separadores
    s = PIPE_RE.sub(". ", s)
    s = UNDERSCORES_RUN_RE.sub(". ", s)

    # Guiones medios/largos como separadores suaves
    s = re.sub(r"\s*[–—]\s*", ". ", s)

    return s

def _normalize_qa_terms(s: str) -> str:
    for pat in QA_VARIANTS:
        s = pat.sub("QA", s)
    s = re.sub(r'\bQA\b(?!\s*\()', 'QA (Quality Assurance)', s)
    return s

def _fix_spacing_and_punct(s: str) -> str:
    s = SPACE_BEFORE_PUNCT_RE.sub(r"\1", s)
    s = DOT_SPACE_FIX_RE.sub(". ", s)      # ". " estándar
    s = MULTI_DOTS_RE.sub(". ", s)         # colapsa ". .", ". . .", etc.
    s = re.sub(r"\.\s+\.", ". ", s)        # ".  ." -> ". "
    s = PUNCT_DUP_RE.sub(r"\1", s)         # "!!!" -> "!"
    s = LEADING_PUNCT_RE.sub("", s)        # quita puntuación/viñetas líderes
    s = re.sub(r"\s+\.$", ".", s)          # " . " final -> "."
    return s

def clean_final_text(text: str) -> str:
    """Normaliza SOLO el contenido de description_final ya traducido."""
    if not isinstance(text, str):
        return ""
    s = nfc(text)

    # Saltos de línea -> ". "
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = s.replace("\n•", "\n")
    s = s.replace("\n", ". ")

    # Ruido y maquetación
    s = _strip_markdown_and_layout(s)

    # Q&A → QA (Quality Assurance)
    s = _normalize_qa_terms(s)

    # Espaciado y puntuación
    s = _fix_spacing_and_punct(s)

    # Compactar espacios finales
    s = WS_RE.sub(" ", s).strip()

    # Si quedó algo como ". Texto" por limpieza, vuelve a limpiar líder
    s = LEADING_PUNCT_RE.sub("", s).strip()
    return s

# --------------- LECTURA ROBUSTA ----------------
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

# --------------- PROCESO POR ARCHIVO ---------------
def normalize_file(path: Path):
    try:
        df = read_csv_robust(path)
    except Exception as e:
        print(f"[ERROR] Leyendo {path.name}: {e}")
        return

    if FINAL_COL not in df.columns:
        print(f"[WARN] No hay columna '{FINAL_COL}' en {path.name}")
        return

    col = df[FINAL_COL].astype(str)

    # NO tocar vacíos ni filas con ticket
    mask_keep = col.str.strip().eq("") | col.str.startswith(FAIL_MARKER, na=False)
    mask_norm = ~mask_keep

    n_total = len(df)
    n_norm = int(mask_norm.sum())
    if n_norm == 0:
        print(f"[OK] {path.name}: nada que normalizar ({n_total} filas).")
        return

    df.loc[mask_norm, FINAL_COL] = col[mask_norm].map(clean_final_text)

    # Guardar
    try:
        df.to_csv(path, index=False, encoding="utf-8")
    except Exception:
        df.to_csv(path, index=False, encoding="utf-8-sig")

    print(f"[OK] {path.name}: normalizadas {n_norm}/{n_total} filas.")

# --------------- RECORRER TODAS LAS CARRERAS ---------------
def normalize_all():
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
        target = d / f"{d.name}_Merged.csv"
        if not target.exists():
            print(f"[SKIP] No existe {target.name} en {d.name}")
            continue
        normalize_file(target)

# --------------------- EJECUCIÓN ---------------------
normalize_all()
