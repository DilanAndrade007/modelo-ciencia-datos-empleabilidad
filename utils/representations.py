import os, re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from unicodedata import normalize, combining
from pathlib import Path  

# ===================== CONFIG =====================
REPO_ROOT   = Path(__file__).resolve().parent.parent           # <repo>/
base_global = REPO_ROOT / "data" / "outputs" / "todas_las_plataformas"
OUTPUT_DIR  = REPO_ROOT / "data" / "outputs" / "reportes"
TOP_N_CAREERS   = 10
TOP_N_COUNTRIES = 15
# ==================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------- utilidades ----------------
def strip_accents(s: str) -> str:
    if not isinstance(s, str):
        return ""
    return "".join(ch for ch in normalize("NFKD", s) if not combining(ch))

def clean_text(s):
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
    return " ".join(w.capitalize() for w in s.split())

NON_COUNTRY_PLACEHOLDERS = {
    "abroad","Remote","remote","worldwide","global","international",
    "anywhere","any location","various locations","multiple locations",
    "unspecified","unknown","-","n/a","na"
}

# ---------------- Estados de EE.UU. (para mapear a "united states") ----------------
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

# ---------------- Diccionario maestro: país canónico -> variantes ----------------
# Puedes agregar/editar libremente. Todo se normaliza con clean_text() antes de indexar.
COUNTRY_CANONICAL_MAP = {
    # --- LATAM (incluye tus ejemplos) ---
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
    "haiti": ["haiti", "haïti", "republic of haiti", "république d’haiti", "república de haiti", "ht"],
    "french guiana": ["french guiana", "guayana francesa"],
    "latin america": ["latin america", "latam"],

    # --- Habla hispana fuera de LATAM ---
    "spain": ["spain", "españa", "espana", "kingdom of spain", "reino de españa", "es"],
    "equatorial guinea": ["equatorial guinea", "guinea ecuatorial"],

    # --- Estados Unidos, Reino Unido y comunes fuera ---
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
    "afghanistan": ["afghanistan", "af", "kabul"],
    "albania": ["albania", "al", "tirana"],
    "andorra": ["andorra", "ad", "andorra la vella"],
    "angola": ["angola", "ao", "luanda"],
    "antigua and barbuda": ["antigua and barbuda", "antigua", "barbuda", "st. john's"],
    "saudi arabia": ["saudi arabia", "ksa", "riyadh", "kingdom of saudi arabia"],
    "algeria": ["algeria", "dz", "algiers", "al-jazair"],
    "armenia": ["armenia", "am", "yerevan"],
    "australia": ["australia", "au", "canberra"],
    "azerbaijan": ["azerbaijan", "az", "baku"],
    "bahamas": ["bahamas", "bs", "nassau"],
    "bangladesh": ["bangladesh", "bd", "dhaka"],
    "barbados": ["barbados", "bb", "bridgetown"],
    "bahrain": ["bahrain", "bh", "manama"],
    "belarus": ["belarus", "by", "minsk", "belarussia"],
    "benin": ["benin", "bj", "porto-novo"],
    "bhutan": ["bhutan", "bt", "thimphu"],
    "bosnia and herzegovina": ["bosnia and herzegovina", "ba", "sarajevo"],
    "botswana": ["botswana", "bw", "gaborone"],
    "brunei": ["brunei", "bn", "bandar seri begawan"],
    "bulgaria": ["bulgaria", "bg", "sofia"],
    "burkina faso": ["burkina faso", "bf", "ouagadougou"],
    "burundi": ["burundi", "bi", "gitega", "bujumbura"],
    "cabo verde": ["cabo verde", "cape verde", "cv", "praia"],
    "cambodia": ["cambodia", "kh", "phnom penh", "kampuchea"],
    "cameroon": ["cameroon", "cm", "yaounde", "yaoundé"],
    "chad": ["chad", "td", "ndjamena"],
    "cyprus": ["cyprus", "cy", "nicosia"],
    "comoros": ["comoros", "km", "moroni"],
    "north korea": ["north korea", "democratic people's republic of korea", "dprk", "pyongyang"],
    "south korea": ["south korea", "republic of korea", "rok", "seoul"],
    "ivory coast": ["ivory coast", "côte d'ivoire", "ci", "abidjan", "yamoussoukro"],
    "croatia": ["croatia", "hr", "zagreb"],
    "dominica": ["dominica", "dm", "roseau"],
    "egypt": ["egypt", "eg", "cairo", "arab republic of egypt"],
    "united arab emirates": ["united arab emirates", "uae", "abudhabi", "dubai"],
    "estonia": ["estonia", "ee", "tallinn"],
    "ethiopia": ["ethiopia", "et", "addis ababa"],
    "fiji": ["fiji", "fj", "suva"],
    "philippines": ["philippines", "ph", "manila", "republika ng pilipinas"],
    "gabon": ["gabon", "ga", "libreville"],
    "gambia": ["gambia", "gm", "banjul"],
    "georgia": ["georgia", "ge", "tbilisi"],
    "ghana": ["ghana", "gh", "accra"],
    "grenada": ["grenada", "gd", "st. george's"],
    "guinea": ["guinea", "gn", "conakry"],
    "guinea-bissau": ["guinea-bissau", "gw", "bissau"],
    "guyana": ["guyana", "gy", "georgetown"],
    "iceland": ["iceland", "is", "reykjavik"],
    "india": ["india", "in", "new delhi", "bharat"],
    "indonesia": ["indonesia", "id", "jakarta"],
    "iraq": ["iraq", "iq", "baghdad"],
    "iran": ["iran", "ir", "tehran", "islamic republic of iran"],
    "israel": ["israel", "il", "jerusalem"],
    "jamaica": ["jamaica", "jm", "kingston"],
    "japan": ["japan", "jp", "tokyo", "nippon", "nihon"],
    "jordan": ["jordan", "jo", "amman"],
    "kazakhstan": ["kazakhstan", "kz", "astana", "nur-sultan"],
    "kenya": ["kenya", "ke", "nairobi"],
    "kiribati": ["kiribati", "ki", "tarawa"],
    "kuwait": ["kuwait", "kw", "kuwait city"],
    "laos": ["laos", "la", "vientiane", "lao people's democratic republic"],
    "lesotho": ["lesotho", "ls", "maseru"],
    "latvia": ["latvia", "lv", "riga"],
    "lebanon": ["lebanon", "lb", "beirut"],
    "liberia": ["liberia", "lr", "monrovia"],
    "libya": ["libya", "ly", "tripoli", "state of libya"],
    "liechtenstein": ["liechtenstein", "li", "vaduz"],
    "lithuania": ["lithuania", "lt", "vilnius"],
    "luxembourg": ["luxembourg", "lu", "luxemburg", "luxemburgo", "luxembourg city"],
    "madagascar": ["madagascar", "mg", "antananarivo"],
    "malaysia": ["malaysia", "my", "kuala lumpur"],
    "malawi": ["malawi", "mw", "lilongwe"],
    "maldives": ["maldives", "mv", "malé"],
    "mali": ["mali", "ml", "bamako"],
    "malta": ["malta", "mt", "valletta"],
    "morocco": ["morocco", "ma", "rabat", "maroc"],
    "mauritius": ["mauritius", "mu", "port louis"],
    "mauritania": ["mauritania", "mr", "nouakchott"],
    "micronesia": ["micronesia", "fm", "palikir", "federated states of micronesia"],
    "moldova": ["moldova", "md", "chisinau", "republic of moldova"],
    "monaco": ["monaco", "mc", "monte carlo"],
    "mongolia": ["mongolia", "mn", "ulaanbaatar"],
    "montenegro": ["montenegro", "me", "podgorica"],
    "mozambique": ["mozambique", "mz", "maputo"],
    "namibia": ["namibia", "na", "windhoek"],
    "nauru": ["nauru", "nr", "yaren"],
    "nepal": ["nepal", "np", "kathmandu"],
    "niger": ["niger", "ne", "niamey"],
    "nigeria": ["nigeria", "ng", "abuja", "lagos"],
    "new zealand": ["new zealand", "nz", "wellington"],
    "oman": ["oman", "om", "muscat"],
    "pakistan": ["pakistan", "pk", "islamabad"],
    "papua new guinea": ["papua new guinea", "pg", "port moresby"],
    "portugal": ["portugal", "pt", "lisbon", "lisboa"],
    "central african republic": ["central african republic", "car", "bangui"],
    "republic of the congo": ["republic of the congo", "congo-brazzaville", "brazzaville"],
    "democratic republic of the congo": ["democratic republic of the congo", "congo-kinshasa", "kinshasa", "dr congo"],
    "rwanda": ["rwanda", "rw", "kigali"],
    "samoa": ["samoa", "ws", "apia"],
    "saint kitts and nevis": ["saint kitts and nevis", "kn", "basseterre"],
    "san marino": ["san marino", "sm", "san marino city"],
    "saint vincent and the grenadines": ["saint vincent and the grenadines", "vc", "kingstown"],
    "saint lucia": ["saint lucia", "lc", "castries"],
    "sao tome and principe": ["sao tome and principe", "st", "sao tome"],
    "senegal": ["senegal", "sn", "dakar"],
    "serbia": ["serbia", "rs", "belgrade", "beograd"],
    "seychelles": ["seychelles", "sc", "victoria"],
    "sierra leone": ["sierra leone", "sl", "freetown"],
    "singapore": ["singapore", "sg", "singapore city"],
    "syria": ["syria", "sy", "damascus", "syrian arab republic"],
    "somalia": ["somalia", "so", "mogadishu"],
    "sri lanka": ["sri lanka", "lk", "colombo", "sri jayawardenepura kotte"],
    "south africa": ["south africa", "za", "pretoria", "cape town", "bloemfontein"],
    "sudan": ["sudan", "sd", "khartoum"],
    "south sudan": ["south sudan", "ss", "juba"],
    "thailand": ["thailand", "th", "bangkok", "kingdom of thailand"],
    "tanzania": ["tanzania", "tz", "dodoma"],
    "tajikistan": ["tajikistan", "tj", "dushanbe"],
    "east timor": ["east timor", "timor-leste", "dili"],
    "togo": ["togo", "tg", "lome"],
    "tonga": ["tonga", "to", "nuku'alofa"],
    "trinidad and tobago": ["trinidad and tobago", "tt", "port of spain"],
    "tunisia": ["tunisia", "tn", "tunis", "tunisian republic"],
    "turkmenistan": ["turkmenistan", "tm", "ashgabat"],
    "tuvalu": ["tuvalu", "tv", "funafuti"],
    "uganda": ["uganda", "ug", "kampala"],
    "uzbekistan": ["uzbekistan", "uz", "tashkent"],
    "vanuatu": ["vanuatu", "vu", "port-vila"],
    "vietnam": ["vietnam", "vn", "hanoi", "viet nam"],
    "yemen": ["yemen", "ye", "sana'a", "sana"],
    "zambia": ["zambia", "zm", "lusaka"],
    "zimbabwe": ["zimbabwe", "zw", "harare"]

}

# --------- Buckets (por país canónico) ----------
LATAM_SET = {
    "mexico","guatemala","belize","honduras","el salvador","nicaragua","costa rica","panama","cuba",
    "dominican republic","puerto rico","haiti","colombia","venezuela","ecuador","peru","bolivia","chile",
    "argentina","uruguay","paraguay","brazil","french guiana","latin america"
}
SPANISH_OUTSIDE_LATAM_SET = {"spain","equatorial guinea"}

# ----------------- Índice de variantes → país canónico -----------------
def build_country_index(cmap: dict) -> dict:
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

# ---------------- helpers de normalización ----------------
NOISE_WORDS = r"(greater|metropolitan|metro|area|region|province|state|prefecture|governorate)"
def _strip_noise_for_guess(s: str) -> str:
    s = re.sub(r"https?://\S+", " ", s)             # URLs
    s = re.sub(r"[\[\]\(\)\'\"]", " ", s)           # corchetes/comillas
    s = s.replace(" d.c.", " dc")
    s = re.sub(fr"\b{NOISE_WORDS}\b", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # "republic of X" se maneja por diccionario (muchos ya están incluidos)
    return s

def soft_country_guess(full_loc: str) -> str:
    """
    Detección suave por 'contains' con límites de palabra usando el índice de variantes.
    Recorre variantes más largas primero para evitar colisiones (ej. korea vs south korea).
    """
    s = f" {_strip_noise_for_guess(full_loc)} "
    # ordenar por largo descendente
    for variant in sorted(VARIANT2CANON.keys(), key=len, reverse=True):
        if not variant or len(variant) < 2:
            continue
        if f" {variant} " in s:
            return VARIANT2CANON[variant]
    return ""

# ---------------- país + bucket desde 'location' ----------------
def country_from_location(loc: str) -> str:
    s = clean_text(loc)
    if s == "":
        return ""
    if "http://" in s or "https://" in s:
        return ""

    if s in NON_COUNTRY_PLACEHOLDERS:
        return "remote"

    if s in US_STATE_CODES or s in US_STATE_NAMES or s.endswith(" state"):
        return "united states"
    if s in VARIANT2CANON:
        return VARIANT2CANON[s]

    parts = [p.strip() for p in s.split(",") if p.strip()]
    last = clean_text(parts[-1]) if parts else s

    if last in NON_COUNTRY_PLACEHOLDERS:
        return "remote"

    if last in US_STATE_CODES or last in US_STATE_NAMES or last.endswith(" state"):
        return "united states"
    if last in VARIANT2CANON:
        return VARIANT2CANON[last]

    guess = soft_country_guess(s)
    if guess:
        return guess

    return ""

def bucket_from_country(country: str) -> str:
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

# ---------------- carga (carpeta = carrera) ----------------
def load_all_from_tree(base_dir: str) -> pd.DataFrame:
    if not os.path.isdir(base_dir):
        raise FileNotFoundError(f"No existe el directorio base: {base_dir}")

    carreras_dirs = sorted(
        d for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d))
    )

    keep_cols = ["source", "location"]
    dfs = []

    for carrera_dirname in carreras_dirs:
        cdir = os.path.join(base_dir, carrera_dirname)

        # Nombre esperado del archivo único por carrera
        merged_stem = f"{carrera_dirname}_Merged"
        candidates = [
            os.path.join(cdir, merged_stem + ".csv"),
            os.path.join(cdir, merged_stem)  # por si no tiene extensión
        ]

        # Seleccionar el primer candidato que exista
        fpath = next((p for p in candidates if os.path.isfile(p)), None)
        if fpath is None:
            print(f"[WARN] No se encontró el archivo único por carrera: {merged_stem}(.csv) en {cdir}. Se omite esta carrera.")
            continue

        # Leer CSV con fallback de encoding
        try:
            try:
                df_i = pd.read_csv(fpath, encoding="utf-8")
            except UnicodeDecodeError:
                df_i = pd.read_csv(fpath, encoding="latin-1")
        except Exception as e:
            print(f"[WARN] No se pudo leer {fpath}: {e}")
            continue

        # Asegurar columnas mínimas
        for c in keep_cols:
            if c not in df_i.columns:
                df_i[c] = np.nan

        df_i = df_i[keep_cols].copy()
        df_i["career"] = clean_text(carrera_dirname)  # nombre de la carpeta
        dfs.append(df_i)

        print(f"[INFO] Procesado {os.path.basename(fpath)} (filas: {len(df_i)})")

    if not dfs:
        raise RuntimeError("No se hallaron archivos <Carrera>_Merged(.csv) válidos en el árbol de carpetas.")

    df = pd.concat(dfs, ignore_index=True)

    # Limpieza mínima
    df["source"]   = df["source"].astype(str).map(clean_text)
    df["location"] = df["location"].astype(str)
    df["career"]   = df["career"].astype(str).map(clean_text)

    # País y bucket
    df["country"]       = df["location"].map(country_from_location).map(clean_text)
    df["country_show"]  = df["country"].map(title_case_no_accents)
    df["region_bucket"] = df["country"].map(bucket_from_country)

    # Filtra mínimos válidos
    df = df[(df["source"] != "") & (df["career"] != "")]
    return df

# ---------------- gráficas / tablas ----------------
def plot_platform_vs_career(df: pd.DataFrame, outdir: str, top_n_careers: int = 10):
    top_c = (df.groupby("career").size().sort_values(ascending=False)
               .head(top_n_careers).index.tolist())
    dff = df[df["career"].isin(top_c)].copy()
    if dff.empty:
        print("[INFO] Sin datos para Plataforma×Carrera.")
        return
    dff["one"] = 1
    tab = dff.pivot_table(index="source", columns="career",
                          values="one", aggfunc="sum", fill_value=0)
    tab = tab.loc[tab.sum(axis=1).sort_values(ascending=False).index]

    tab.plot(kind="bar", stacked=True, figsize=(11,5))
    plt.title(f"Ofertas por plataforma y carrera (top {top_n_careers} carreras)")
    plt.xlabel("Plataforma"); plt.ylabel("Número de ofertas")
    plt.xticks(rotation=45, ha="right"); plt.tight_layout()
    out = os.path.join(outdir, "platform_vs_career_stacked.png")
    plt.savefig(out, dpi=150); plt.close(); print(f"[OK] {out}")

def plot_top_countries(df: pd.DataFrame, outdir: str, top_n: int = 15):
    mask = (~df["country"].isin(["", "remote", "latin america"]))
    vc = df.loc[mask, "country"].value_counts().head(top_n)
    if vc.empty:
        print("[INFO] Sin datos para Top países.")
        return
    vc_show = vc.rename(index=lambda x: " ".join(w.capitalize() for w in x.split()))
    plt.figure(figsize=(8,6))
    vc_show.sort_values().plot(kind="barh")
    plt.title(f"Top {top_n} países por volumen de ofertas")
    plt.xlabel("Número de ofertas"); plt.ylabel(""); plt.tight_layout()
    out = os.path.join(outdir, "top_countries.png")
    plt.savefig(out, dpi=150); plt.close(); print(f"[OK] {out}")

def export_top_countries_csv(df: pd.DataFrame, outdir: str):
    mask = (~df["country"].isin(["", "remote", "latin america"]))
    ranking = (df.loc[mask, "country"]
                 .value_counts()
                 .rename_axis("country")
                 .reset_index(name="count"))
    ranking["country_show"] = ranking["country"].map(lambda s: " ".join(w.capitalize() for w in s.split()))
    ranking = ranking[["country_show","count","country"]]
    out_csv = os.path.join(outdir, "top_countries_full.csv")
    ranking.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"[OK] {out_csv}")

def plot_region_share(df: pd.DataFrame, outdir: str):
    order = ["América Latina","Habla hispana (fuera de LATAM)","Remoto","Otros países"]
    counts = df["region_bucket"].value_counts().reindex(order, fill_value=0)
    total = int(counts.sum()) if int(counts.sum()) > 0 else 1
    perc = (counts / total * 100).round(2)

    perc.plot(kind="bar", figsize=(7,4))
    plt.title("Distribución de ofertas por región")
    plt.ylabel("Porcentaje (%)"); plt.xlabel("")
    for i, v in enumerate(perc.values):
        plt.text(i, v + 0.5, f"{v:.1f}%", ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    out = os.path.join(outdir, "region_share.png")
    plt.savefig(out, dpi=150); plt.close(); print(f"[OK] {out}")

    region_table = pd.DataFrame({"region": perc.index, "porcentaje": perc.values, "conteo": counts.values})
    region_table.to_csv(os.path.join(outdir, "region_share_table.csv"), index=False, encoding="utf-8")

def export_career_country_counts_csv(df: pd.DataFrame, outdir: str):
    """
    Crea un CSV granular con columnas:
    - carrera
    - pais
    - numero_de_ofertas

    Nota: excluye vacíos, 'remote' y 'latin america' para contar solo países.
    """
    # Filtrar valores no-país
    mask = (~df["country"].isin(["", "remote", "latin america"]))
    if not mask.any():
        print("[INFO] No hay datos de países válidos para exportar carrera×país.")
        return

    # Agregar por carrera y país canónico
    agg = (df.loc[mask]
             .groupby(["career", "country"])
             .size()
             .reset_index(name="numero_de_ofertas"))

    # Presentación: título sin acentos
    agg["carrera"] = agg["career"].map(title_case_no_accents)
    agg["pais"]    = agg["country"].map(title_case_no_accents)

    # Ordenar y seleccionar columnas finales
    out_df = (agg[["carrera", "pais", "numero_de_ofertas"]]
                .sort_values(["carrera", "numero_de_ofertas"], ascending=[True, False]))

    out_csv = os.path.join(outdir, "carrera_pais_numero_de_ofertas.csv")
    out_df.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"[OK] {out_csv}")


def export_career_platform_table(df: pd.DataFrame, outdir: str):
    df["one"] = 1
    pivot = df.pivot_table(index="career", columns="source", values="one",
                           aggfunc="sum", fill_value=0)
    col_order = pivot.sum(axis=0).sort_values(ascending=False).index
    pivot = pivot[col_order]
    pivot["TOTAL_CARRERA"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("TOTAL_CARRERA", ascending=False)
    total_row = pivot.sum(axis=0).to_frame().T
    total_row.index = ["TOTAL_GENERAL"]
    pivot_final = pd.concat([pivot, total_row], axis=0)

    out_csv = os.path.join(outdir, "tabla_carrera_por_plataforma.csv")
    pivot_final.to_csv(out_csv, encoding="utf-8")
    print(f"[OK] {out_csv}")

# ---------------- main ----------------
if __name__ == "__main__":
    print(f"[INFO] Base: {base_global}")
    print(f"[INFO] Out : {os.path.abspath(OUTPUT_DIR)}")

    df = load_all_from_tree(base_global)
    print(f"Registros cargados: {len(df):,}")
    print(f"Carreras únicas (por carpeta): {df['career'].nunique()}")
    print(f"Plataformas detectadas: {', '.join(sorted(df['source'].unique()))}")

    # 1) Barras apiladas
    plot_platform_vs_career(df, OUTPUT_DIR, TOP_N_CAREERS)

    # 2) Top países (+ CSV completo)
    plot_top_countries(df, OUTPUT_DIR, TOP_N_COUNTRIES)
    export_top_countries_csv(df, OUTPUT_DIR)

    # 3) Porcentajes por región
    plot_region_share(df, OUTPUT_DIR)

    # 4) Tabla carrera × plataformas
    export_career_platform_table(df, OUTPUT_DIR)

    # 5) CSV granular carrera × país
    export_career_country_counts_csv(df, OUTPUT_DIR)
    
    print("[DONE]")
