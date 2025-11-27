"""
Extractor de habilidades blandas (EURACE) con diccionario externo YAML.
- Solo columnas: EURACE_skills, initial_skills
- Sobrescribe el CSV original
- Sin negaciones
- Implícitos vía patrones + (opcional) fuzzy con rapidfuzz
"""

import re
import ast
import unicodedata
from pathlib import Path
import pandas as pd
import yaml
from rapidfuzz import fuzz, process as rf_process
HAS_RAPIDFUZZ = True

# -------------- CONFIG --------------
BASE_GLOBAL = Path("C:\\Users\\andra\\Documents\\Proyects\\TICs\\Corpus\\Jobs_ScalperV2\\modelo-ciencia-datos-empleabilidad\\data\\outputs\\todas_las_plataformas")
DICT_PATH   = Path("C:\\Users\\andra\\Documents\\Proyects\\TICs\\Corpus\\Jobs_ScalperV2\\modelo-ciencia-datos-empleabilidad\\config\\skills.yml")
DESC_COL    = "description_final"
SKILLS_COL  = "skills"
EURACE_COL  = "EURACE_skills"
INIT_COL    = "initial_skills"
ONLY_THIS_CAREER = None

OVERWRITE = True      # sobrescribe CSV original
FUZZY_THRESHOLD = 90  # umbral conservador para rescate difuso

# -------------- Normalización --------------
URL_RE = re.compile(r"https?://\S+|www\.\S+")
EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
MULTISPACE_RE = re.compile(r"\s+")
PUNCT_TO_SPACE = str.maketrans({c: " " for c in "/|,;:()[]{}<>!?'\"“”‘’·•*#@%^=+~"})

def strip_accents_lower(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s.lower()

def normalize_text(s: str) -> str:
    s = s or ""
    s = URL_RE.sub(" ", s)
    s = EMAIL_RE.sub(" ", s)
    s = s.replace("-", " ").translate(PUNCT_TO_SPACE)
    s = strip_accents_lower(s)
    s = MULTISPACE_RE.sub(" ", s).strip()
    return s

# -------------- Carga YAML + compilación --------------
def load_dictionary(yaml_path: Path):
    if not yaml_path.exists():
        raise FileNotFoundError(f"No se encontró el diccionario YAML en: {yaml_path}")
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    order = data.get("order")
    if not order or not isinstance(order, list):
        raise ValueError("En el YAML debe existir una lista 'order' con el orden de categorías.")

    categories = data.get("categories")
    if not categories or not isinstance(categories, dict):
        raise ValueError("En el YAML debe existir un bloque 'categories' con las categorías y sus definiciones.")

    # Ensambla estructuras
    compiled = []  # lista de (regex, cat)
    cat2_canonical = {}
    fuzzy_bank = {}

    for cat in order:
        if cat not in categories:
            raise ValueError(f"La categoría '{cat}' listada en 'order' no está definida en 'categories' del YAML.")
        cfg = categories[cat] or {}
        canonical = cfg.get("canonical", []) or []
        patterns = cfg.get("patterns", []) or []
        impl_fuzzy = cfg.get("impl_fuzzy", []) or []  # opcional

        # Sanitiza listas a str
        canonical = [str(x) for x in canonical]
        patterns = [str(x) for x in patterns]
        impl_fuzzy = [str(x) for x in impl_fuzzy]

        # compila regex
        for pat in patterns:
            compiled.append((re.compile(pat), cat))

        # bancos
        cat2_canonical[cat] = set(canonical)
        fuzzy_bank[cat] = list(canonical) + impl_fuzzy

    phrase2cat = {phr: cat for cat, phrases in cat2_canonical.items() for phr in phrases}

    return order, compiled, cat2_canonical, fuzzy_bank, phrase2cat

# -------------- Parse 'skills' --------------
def parse_skills_cell(cell):
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return None
    if isinstance(cell, list):
        vals = [str(x).strip() for x in cell if str(x).strip()]
        return vals or None
    s = str(cell).strip()
    if s in ("", "[]", "[ ]"):
        return None
    if s.startswith("[") and s.endswith("]"):
        try:
            obj = ast.literal_eval(s)
            if isinstance(obj, list):
                vals = [str(x).strip() for x in obj if str(x).strip()]
                return vals or None
        except Exception:
            pass
    parts = [p.strip() for p in s.split(",")]
    parts = [p for p in parts if p]
    return parts or None

# -------------- Extracción --------------
def extract_from_text(raw_text: str, order, compiled, cat2_canonical, fuzzy_bank, phrase2cat):
    text_norm = normalize_text(raw_text)
    cats, phrases = set(), set()

    # 1) Regex (explícito + implícito)
    for rgx, cat in compiled:
        if rgx.search(text_norm):
            cats.add(cat)
            # asigna una canónica razonable: primera cuyo "sin espacios" esté en el texto; si no, la primera del set
            added = False
            for phr in cat2_canonical[cat]:
                if phr.replace(" ", "") in text_norm.replace(" ", ""):
                    phrases.add(phr)
                    added = True
                    break
            if not added and cat2_canonical[cat]:
                phrases.add(next(iter(cat2_canonical[cat])))

    # 2) Rescate difuso por categoría (si no hubo regex para esa categoría)
    if HAS_RAPIDFUZZ:
        for cat in order:
            if cat in cats:
                continue
            bank = fuzzy_bank.get(cat, [])
            if not bank:
                continue
            best = rf_process.extractOne(text_norm, bank, scorer=fuzz.token_set_ratio)
            if best and best[1] >= FUZZY_THRESHOLD:
                cats.add(cat)
                best_phr = best[0]
                if best_phr in cat2_canonical[cat]:
                    phrases.add(best_phr)
                elif cat2_canonical[cat]:
                    phrases.add(next(iter(cat2_canonical[cat])))

    # EURACE_skills (orden del YAML)
    eurace_list = [cat for cat in order if cat in cats]
    eurace_out = ", ".join(eurace_list) if eurace_list else ""

    # initial_skills agrupadas por categoría (mismo orden)
    if phrases:
        by_cat = {cat: [] for cat in order}
        for phr in sorted(phrases):
            cat = phrase2cat.get(phr)
            if cat in by_cat:
                by_cat[cat].append(phr)
        flat = []
        for cat in order:
            flat.extend(by_cat[cat])
        init_out = ", ".join(dict.fromkeys(flat))
    else:
        init_out = ""

    return eurace_out, init_out

# -------------- Proceso por archivo --------------
def process_file(path: Path, order, compiled, cat2_canonical, fuzzy_bank, phrase2cat):
    # lectura robusta
    df = None
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            df = pd.read_csv(path, encoding=enc, low_memory=False)
            break
        except Exception:
            df = None
    if df is None:
        print(f"[ERROR] No se pudo leer {path.name}")
        return

    missing = [c for c in (DESC_COL, SKILLS_COL) if c not in df.columns]
    if missing:
        print(f"[WARN] {path.name}: faltan columnas {missing}.")
        return

    total = len(df)
    print(f"[INFO] Procesando {path.name} ({total} filas)")

    eurace_vals, init_vals = [], []
    for d, s in zip(df[DESC_COL], df[SKILLS_COL]):
        pieces = []
        if isinstance(d, str) and d.strip():
            pieces.append(d)
        lst = parse_skills_cell(s)
        if lst:
            pieces.append(", ".join(lst))

        if not pieces:
            eurace_vals.append("")
            init_vals.append("")
            continue

        eur, ini = extract_from_text(" / ".join(pieces), order, compiled, cat2_canonical, fuzzy_bank, phrase2cat)
        eurace_vals.append(eur)
        init_vals.append(ini)

    # Solo estas dos columnas
    df[EURACE_COL] = eurace_vals
    df[INIT_COL]   = init_vals

    # Salida (sobrescribe original si OVERWRITE=True)
    out_path = path
    try:
        df.to_csv(out_path, index=False, encoding="utf-8")
    except Exception:
        df.to_csv(out_path, index=False, encoding="utf-8-sig")

    n_cats = int((df[EURACE_COL].str.len() > 0).sum())
    n_init = int((df[INIT_COL].str.len() > 0).sum())
    print(f"[OK] {out_path.name}: {n_cats}/{total} con EURACE_skills, {n_init}/{total} con initial_skills.\n")

# -------------- Recorrer base --------------
def run_all():
    order, compiled, cat2_canonical, fuzzy_bank, phrase2cat = load_dictionary(DICT_PATH)

    base = BASE_GLOBAL
    if not base.exists():
        raise FileNotFoundError(f"No existe la ruta base: {base}")

    dirs = [p for p in base.iterdir() if p.is_dir()]
    if ONLY_THIS_CAREER:
        dirs = [d for d in dirs if d.name == ONLY_THIS_CAREER]
    if not dirs:
        print("[WARN] No se encontraron carpetas para procesar.")
        return

    for d in sorted(dirs, key=lambda x: x.name.lower()):
        target = d / f"{d.name}_Merged.csv"
        if not target.exists():
            print(f"[SKIP] No existe {target.name} en {d.name}")
            continue
        process_file(target, order, compiled, cat2_canonical, fuzzy_bank, phrase2cat)

# -------------- Main --------------
if __name__ == "__main__":
    run_all()
