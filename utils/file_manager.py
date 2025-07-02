import os, json
import pandas as pd
import glob
import shutil

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

def unir_corpus_acumulado_por_carrera(fuente, carrera):
    """
    Une todos los CSVs diarios ya consolidados por fecha (corpus_unido) para una carrera.
    Guarda un corpus acumulado: corpus__<Carrera>__acumulado.csv
    """
    base_dir = os.path.join("data", "outputs", fuente, carrera.replace(" ", "_"), "corpus_unido")
    patron = os.path.join(base_dir, f"{fuente}__{carrera.replace(' ', '_')}__*__merged.csv")
    archivos_csv = glob.glob(patron)

    if not archivos_csv:
        print(f"No se encontraron corpus diarios en {base_dir}")
        return

    dfs = [pd.read_csv(f) for f in archivos_csv]
    df_total = pd.concat(dfs, ignore_index=True).drop_duplicates(subset="job_id")

    output_file = os.path.join(base_dir, f"{fuente}__{carrera.replace(' ', '_')}__acumulado.csv")
    df_total.to_csv(output_file, index=False)

    print(f"Corpus acumulado guardado en: {output_file} ({len(df_total)} filas)")


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
