"""
Módulo para extracción y normalización de ubicaciones/países desde datos de empleo.
Contiene toda la lógica para identificar países desde strings de ubicación.
"""

import re
import pandas as pd
from unicodedata import normalize, combining

# ---------------- Utilidades de texto ----------------
def strip_accents(s: str) -> str:
    """Remueve acentos y caracteres especiales del texto."""
    if not isinstance(s, str):
        return ""
    return "".join(ch for ch in normalize("NFKD", s) if not combining(ch))

def clean_text(s):
    """Normaliza texto: sin acentos, minúsculas, espacios únicos."""
    if s is None:
        return ""
    if isinstance(s, float) and pd.isna(s):
        return ""
    s = str(s).strip()
    if s.lower() in {"", "nan", "null", "none", "na"}:
        return ""
    t = strip_accents(s).lower()
    t = re.sub(r"\s+", " ", t)
    return t.strip()

def title_case_no_accents(s: str) -> str:
    """Convierte a Title Case sin acentos."""
    return " ".join(w.capitalize() for w in s.split())

# ---------------- Constantes y conjuntos de datos ----------------
NON_COUNTRY_PLACEHOLDERS = {
    "abroad","Remote","remote","worldwide","global","international",
    "anywhere","any location","various locations","multiple locations",
    "unspecified","unknown","-","n/a","na"
}

# Estados de EE.UU. (para mapear a "united states")
US_STATE_CODES = {
    "al","ak","az","ar","ca","co","ct","de","fl","ga","hi","id","il","in","ia","ks","ky","la","me",
    "md","ma","mi","mn","ms","mo","mt","ne","nv","nh","nj","nm","ny","nc","nd","oh","ok","or","pa",
    "ri","sc","sd","tn","tx","ut","vt","va","wa","wv","wi","wy","dc"
}

US_STATE_NAMES = {
    "alabama","alaska","arizona","arkansas","california","colorado","connecticut","delaware","florida","georgia",
    "hawaii","idaho","illinois","indiana","iowa","kansas","kentucky","louisiana","maine","maryland","massachusetts",
    "michigan","minnesota","mississippi","missouri","montana","nebraska","nevada","new hampshire","new jersey",
    "new mexico","new york","north carolina","north dakota","ohio","oklahoma","oregon","pennsylvania","rhode island",
    "south carolina","south dakota","tennessee","texas","utah","vermont","virginia","washington","west virginia",
    "wisconsin","wyoming","district of columbia"
}

# Diccionario maestro: país canónico -> variantes
COUNTRY_CANONICAL_MAP = {
    # --- LATAM ---
    "mexico": ["mexico", "méxico", "united mexican states", "estados unidos mexicanos", "mx"],
    "guatemala": ["guatemala", "republic of guatemala", "república de guatemala"],
    "belize": ["belize", "belice"],
    "honduras": ["honduras", "republic of honduras", "república de honduras"],
    "el salvador": ["el salvador", "republic of el salvador", "república de el salvador", "sv"],
    "nicaragua": ["nicaragua", "republic of nicaragua", "república de nicaragua"],
    "costa rica": ["costa rica", "republic of costa rica", "república de costa rica"],
    "panama": ["panama", "panamá", "republic of panama", "república de panamá", "pa"],
    "cuba": ["cuba", "republic of cuba", "república de cuba", "cu"],
    "dominican republic": ["dominican republic", "república dominicana", "do"],
    "puerto rico": ["puerto rico", "commonwealth of puerto rico", "estado libre asociado de puerto rico", "pr"],
    "colombia": ["colombia", "republic of colombia", "república de colombia", "co"],
    "venezuela": ["venezuela", "bolivarian republic of venezuela", "república bolivariana de venezuela", "ve"],
    "ecuador": ["ecuador", "republic of ecuador", "república del ecuador", "ec"],
    "peru": ["peru", "perú", "republic of peru", "república del perú", "pe"],
    "bolivia": ["bolivia", "plurinational state of bolivia", "estado plurinacional de bolivia", "bo"],
    "chile": ["chile", "republic of chile", "república de chile", "cl"],
    "argentina": ["argentina", "argentine republic", "república argentina", "ar"],
    "uruguay": ["uruguay", "oriental republic of uruguay", "república oriental del uruguay", "uy"],
    "paraguay": ["paraguay", "republic of paraguay", "república del paraguay", "py"],
    "brazil": ["brazil", "brasil", "federative republic of brazil", "república federativa del brasil", "br"],
    "haiti": ["haiti", "haïti", "republic of haiti", "république d'haiti", "república de haiti", "ht"],
    "french guiana": ["french guiana", "guayana francesa"],
    "latin america": ["latin america", "latam"],

    # --- Habla hispana fuera de LATAM ---
    "spain": ["spain", "españa", "espana", "kingdom of spain", "reino de españa", "es"],
    "equatorial guinea": ["equatorial guinea", "guinea ecuatorial"],

    # --- Países principales del mundo ---
    "united states": ["united states", "usa", "u.s.a.", "us", "u s", "u.s.", "u.s", "united states of america", "washington dc", "washington d.c.", "district of columbia"],
    "united kingdom": ["united kingdom", "uk", "england", "scotland", "wales", "northern ireland", "great britain", "gb", "london"],
    "canada": ["canada", "ca", "ottawa"],
    "switzerland": ["switzerland", "ch", "bern", "suisse", "schweiz"],
    "germany": ["germany", "de", "deutschland", "berlin"],
    "france": ["france", "fr", "french republic", "paris"],
    "italy": ["italy", "it", "italian republic", "roma", "rome"],
    "austria": ["austria", "at", "vienna", "österreich"],
    "netherlands": ["netherlands", "nl", "holland", "amsterdam"],
    "belgium": ["belgium", "be", "brussels", "belgië", "belgique"],
    "sweden": ["sweden", "se", "stockholm", "sverige"],
    "norway": ["norway", "no", "oslo", "norge"],
    "denmark": ["denmark", "dk", "copenhagen", "danmark"],
    "finland": ["finland", "fi", "helsinki", "suomi"],
    "poland": ["poland", "pl", "warsaw", "polska"],
    "czech republic": ["czech republic", "czechia", "cz", "prague", "praha"],
    "slovakia": ["slovakia", "sk", "bratislava", "slovenská republika"],
    "hungary": ["hungary", "hu", "budapest", "magyarország"],
    "ukraine": ["ukraine", "ua", "kyiv", "kiev", "ukraina"],
    "russia": ["russia", "ru", "russian federation", "moscow", "rossiya"],
    "romania": ["romania", "ro", "bucharest", "românia"],
    "greece": ["greece", "gr", "athens", "ellada", "hellas"],
    "turkey": ["turkey", "tr", "ankara", "turkiye", "türkiye"],
    "australia": ["australia", "au", "canberra"],
    "new zealand": ["new zealand", "nz", "wellington"],
    "japan": ["japan", "jp", "tokyo", "nippon", "nihon"],
    "south korea": ["south korea", "republic of korea", "rok", "seoul"],
    "china": ["china", "cn", "beijing", "people's republic of china"],
    "india": ["india", "in", "new delhi", "bharat"],
    "singapore": ["singapore", "sg", "singapore city"],
    "israel": ["israel", "il", "jerusalem"],
    "south africa": ["south africa", "za", "pretoria", "cape town", "bloemfontein"],
    # ... (puedes agregar más países según necesites)
}

# Buckets regionales
LATAM_SET = {
    "mexico","guatemala","belize","honduras","el salvador","nicaragua","costa rica","panama","cuba",
    "dominican republic","puerto rico","haiti","colombia","venezuela","ecuador","peru","bolivia","chile",
    "argentina","uruguay","paraguay","brazil","french guiana","latin america"
}

SPANISH_OUTSIDE_LATAM_SET = {"spain","equatorial guinea"}

# ---------------- Índice de búsqueda ----------------
def build_country_index(cmap: dict) -> dict:
    """Construye índice de variantes → país canónico."""
    idx = {}
    for canon, variants in cmap.items():
        canon_norm = clean_text(canon)
        idx[canon_norm] = canon_norm  # el propio nombre canónico también
        for v in variants:
            vnorm = clean_text(v)
            if vnorm:
                idx[vnorm] = canon_norm
    return idx

VARIANT2CANON = build_country_index(COUNTRY_CANONICAL_MAP)

# ---------------- Funciones de detección ----------------
NOISE_WORDS = r"(greater|metropolitan|metro|area|region|province|state|prefecture|governorate)"

def _strip_noise_for_guess(s: str) -> str:
    """Remueve palabras ruidosas para detección suave."""
    s = re.sub(r"https?://\S+", " ", s)             # URLs
    s = re.sub(r"[\[\]\(\)\'\"]", " ", s)           # corchetes/comillas
    s = s.replace(" d.c.", " dc")
    s = re.sub(fr"\b{NOISE_WORDS}\b", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def soft_country_guess(full_loc: str) -> str:
    """
    Detección suave por 'contains' con límites de palabra usando el índice de variantes.
    Recorre variantes más largas primero para evitar colisiones (ej. korea vs south korea).
    """
    s = f" {_strip_noise_for_guess(clean_text(full_loc))} "
    # ordenar por largo descendente
    for variant in sorted(VARIANT2CANON.keys(), key=len, reverse=True):
        if not variant or len(variant) < 2:
            continue
        if f" {variant} " in s:
            return VARIANT2CANON[variant]
    return ""

# ---------------- Función principal de extracción ----------------
def country_from_location(loc: str) -> str:
    """
    Extrae el país desde una string de ubicación.
    
    Args:
        loc: String de ubicación (ej: "San Francisco, CA, USA")
        
    Returns:
        str: País canónico identificado o string vacío si no se encuentra
    """
    s = clean_text(loc)
    if s == "":
        return ""
    if "http://" in s or "https://" in s:
        return ""

    # Verificar placeholders de no-país
    if s in NON_COUNTRY_PLACEHOLDERS:
        return "remote"

    # Verificar estados de EE.UU.
    if s in US_STATE_CODES or s in US_STATE_NAMES or s.endswith(" state"):
        return "united states"
    
    # Búsqueda exacta en índice
    if s in VARIANT2CANON:
        return VARIANT2CANON[s]

    # Analizar por partes separadas por comas
    parts = [p.strip() for p in s.split(",") if p.strip()]
    last = clean_text(parts[-1]) if parts else s

    if last in NON_COUNTRY_PLACEHOLDERS:
        return "remote"

    if last in US_STATE_CODES or last in US_STATE_NAMES or last.endswith(" state"):
        return "united states"
    
    if last in VARIANT2CANON:
        return VARIANT2CANON[last]

    # Detección suave como último recurso
    guess = soft_country_guess(s)
    if guess:
        return guess

    return ""

def bucket_from_country(country: str) -> str:
    """
    Asigna un bucket regional al país.
    
    Args:
        country: País canónico
        
    Returns:
        str: Bucket regional correspondiente
    """
    c = clean_text(country)
    if c == "remote":
        return "Remoto"
    if c == "":
        return "Otros países"
    if c in LATAM_SET:
        return "América Latina"
    if c in SPANISH_OUTSIDE_LATAM_SET:
        return "Habla hispana (fuera de LATAM)"
    return "Otros países"

# ---------------- Función de procesamiento completo ----------------
def extract_countries_from_dataframe(df: pd.DataFrame, location_col: str = "location") -> pd.DataFrame:
    """
    Procesa un DataFrame agregando columnas de país y región.
    
    Args:
        df: DataFrame con datos de empleo
        location_col: Nombre de la columna que contiene ubicaciones
        
    Returns:
        pd.DataFrame: DataFrame con columnas country, country_show, region_bucket agregadas
    """
    df = df.copy()
    
    # Extraer países
    df["country"] = df[location_col].astype(str).map(country_from_location).map(clean_text)
    df["country_show"] = df["country"].map(title_case_no_accents)
    df["region_bucket"] = df["country"].map(bucket_from_country)
    
    return df

# ---------------- Funciones de utilidad para análisis ----------------
def get_country_stats(df: pd.DataFrame, exclude_remote: bool = True) -> pd.DataFrame:
    """
    Obtiene estadísticas de países desde un DataFrame procesado.
    
    Args:
        df: DataFrame con columna 'country'
        exclude_remote: Si excluir trabajos remotos y otros
        
    Returns:
        pd.DataFrame: Ranking de países con conteos
    """
    if exclude_remote:
        mask = (~df["country"].isin(["", "remote", "latin america"]))
        countries_data = df.loc[mask, "country"]
    else:
        countries_data = df["country"]
    
    ranking = (countries_data
                 .value_counts()
                 .rename_axis("country")
                 .reset_index(name="count"))
    
    ranking["country_show"] = ranking["country"].map(title_case_no_accents)
    return ranking[["country_show", "count", "country"]]

def get_region_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Obtiene estadísticas de regiones desde un DataFrame procesado.
    
    Args:
        df: DataFrame con columna 'region_bucket'
        
    Returns:
        pd.DataFrame: Estadísticas por región
    """
    order = ["América Latina", "Habla hispana (fuera de LATAM)", "Remoto", "Otros países"]
    counts = df["region_bucket"].value_counts().reindex(order, fill_value=0)
    total = int(counts.sum()) if int(counts.sum()) > 0 else 1
    perc = (counts / total * 100).round(2)
    
    return pd.DataFrame({
        "region": perc.index, 
        "porcentaje": perc.values, 
        "conteo": counts.values
    })