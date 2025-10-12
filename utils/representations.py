"""
Módulo principal para análisis de representación geográfica de ofertas de empleo.
Coordina la carga de datos, procesamiento de países (desde location_final) y generación de reportes.
Incluye funcionalidades de carga de datos integradas.
Requiere que los datos ya tengan la columna 'location_final' procesada por file_manager.
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path

# Importar módulos especializados (con manejo de ejecución directa)
try:
    # Importación relativa (cuando se usa como módulo)
    from .location_extractor import clean_text, title_case_no_accents, bucket_from_country
    from .chart_generator import generate_all_charts
except ImportError:
    # Importación absoluta (cuando se ejecuta directamente)
    from location_extractor import clean_text, title_case_no_accents, bucket_from_country
    from chart_generator import generate_all_charts

# ===================== CONFIG =====================
REPO_ROOT = Path(__file__).resolve().parent.parent           # <repo>/
BASE_GLOBAL = REPO_ROOT / "data" / "outputs" / "todas_las_plataformas"
OUTPUT_DIR = REPO_ROOT / "data" / "outputs" / "reportes"
TOP_N_CAREERS = 10
TOP_N_COUNTRIES = 15
# ==================================================

# ============ FUNCIONES DE CARGA DE DATOS (integradas desde data_loader) ============

def read_csv_with_fallback(filepath: str) -> pd.DataFrame:
    """
    Lee un archivo CSV con fallback de encoding.
    
    Args:
        filepath: Ruta al archivo CSV
        
    Returns:
        pd.DataFrame: DataFrame leído
        
    Raises:
        Exception: Si no se puede leer con ningún encoding
    """
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    
    for encoding in encodings:
        try:
            return pd.read_csv(filepath, encoding=encoding)
        except UnicodeDecodeError:
            continue
        except Exception as e:
            # Si es otro error que no sea de encoding, re-lanzar
            if encoding == encodings[0]:  # Solo en el primer intento
                raise e
    
    raise Exception(f"No se pudo leer el archivo con ningún encoding: {filepath}")

def load_all_from_tree(base_dir: str) -> pd.DataFrame:
    """
    Carga todos los archivos _Merged.csv desde una estructura de carpetas.
    Cada carpeta representa una carrera con su archivo de datos consolidado.
    
    Args:
        base_dir: Directorio base que contiene carpetas por carrera
        
    Returns:
        pd.DataFrame: DataFrame consolidado con todas las ofertas
        
    Raises:
        FileNotFoundError: Si el directorio base no existe
        RuntimeError: Si no se encuentran archivos válidos
    """
    if not os.path.isdir(base_dir):
        raise FileNotFoundError(f"No existe el directorio base: {base_dir}")

    # Obtener carpetas de carreras
    carreras_dirs = sorted(
        d for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d))
    )

    if not carreras_dirs:
        raise RuntimeError(f"No se encontraron carpetas de carreras en: {base_dir}")

    # Columnas mínimas requeridas
    keep_cols = ["source", "location", "location_final"]
    dfs = []

    print(f"Cargando {len(carreras_dirs)} carreras...")

    for carrera_dirname in carreras_dirs:
        cdir = os.path.join(base_dir, carrera_dirname)

        # Buscar archivo _Merged de la carrera
        merged_stem = f"{carrera_dirname}_Merged"
        candidates = [
            os.path.join(cdir, merged_stem + ".csv"),
            os.path.join(cdir, merged_stem)  # por si no tiene extensión
        ]

        # Seleccionar el primer candidato que exista
        fpath = next((p for p in candidates if os.path.isfile(p)), None)
        if fpath is None:
            continue

        # Leer CSV con manejo de errores de encoding
        try:
            df_i = read_csv_with_fallback(fpath)
        except Exception as e:
            continue

        # Validar que tenga datos
        if df_i.empty:
            continue

        # Asegurar columnas mínimas
        for c in keep_cols:
            if c not in df_i.columns:
                df_i[c] = np.nan

        # Seleccionar solo columnas que existen y agregar carrera
        available_cols = [c for c in keep_cols if c in df_i.columns]
        df_i = df_i[available_cols].copy()
        df_i["career"] = clean_text(carrera_dirname)  # nombre de la carpeta
        dfs.append(df_i)

    if not dfs:
        raise RuntimeError("No se hallaron archivos <Carrera>_Merged(.csv) válidos en el árbol de carpetas.")

    # Consolidar todos los DataFrames
    df = pd.concat(dfs, ignore_index=True)
    
    print(f"Datos consolidados: {len(df):,} registros de {len(dfs)} carreras")
    
    return df

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia y normaliza un DataFrame de ofertas de empleo.
    
    Args:
        df: DataFrame con columnas source, location, career
        
    Returns:
        pd.DataFrame: DataFrame limpio y normalizado
    """
    df = df.copy()
    
    # Limpieza básica de columnas
    df["source"] = df["source"].astype(str).map(clean_text)
    df["location"] = df["location"].astype(str)
    df["career"] = df["career"].astype(str).map(clean_text)

    # Filtrar registros con datos mínimos válidos
    initial_count = len(df)
    df = df[(df["source"] != "") & (df["career"] != "")]
    final_count = len(df)
    
    if initial_count != final_count:
        print(f"Filtrados {initial_count - final_count:,} registros inválidos")
    
    return df

def get_data_summary(df: pd.DataFrame) -> dict:
    """
    Genera un resumen estadístico de los datos cargados.
    
    Args:
        df: DataFrame con datos de empleo
        
    Returns:
        dict: Diccionario con estadísticas del dataset
    """
    summary = {
        "total_registros": len(df),
        "carreras_unicas": df["career"].nunique() if "career" in df.columns else 0,
        "plataformas_unicas": df["source"].nunique() if "source" in df.columns else 0,
        "ubicaciones_unicas": df["location"].nunique() if "location" in df.columns else 0,
        "registros_con_ubicacion": df["location"].notna().sum() if "location" in df.columns else 0,
    }
    
    if "career" in df.columns:
        summary["carreras"] = df["career"].unique().tolist()
    
    if "source" in df.columns:
        summary["plataformas"] = df["source"].unique().tolist()
    
    return summary

def print_data_summary(df: pd.DataFrame):
    """
    Imprime un resumen legible de los datos cargados.
    
    Args:
        df: DataFrame con datos de empleo
    """
    summary = get_data_summary(df)
    
    print(f"\nRESUMEN:")
    print(f"  Total: {summary['total_registros']:,} registros")
    print(f"  Carreras: {summary['carreras_unicas']}")
    print(f"  Plataformas: {summary['plataformas_unicas']}")
    print(f"  Países identificados: {df['country'].nunique() if 'country' in df.columns else 0}")
    
    if summary.get('plataformas'):
        print(f"\nDistribución por plataforma:")
        for platform in sorted(summary['plataformas']):
            count = (df["source"] == platform).sum()
            percentage = (count / summary['total_registros'] * 100)
            print(f"  {platform}: {count:,} ({percentage:.1f}%)")
    
    print()  # Línea en blanco

# ============ FUNCIÓN PRINCIPAL DE PROCESAMIENTO ============

def process_job_data(base_dir: str = None, output_dir: str = None) -> None:
    """
    Función principal que coordina todo el proceso de análisis.
    
    PREREQUISITO: Los archivos CSV deben tener la columna 'location_final' ya procesada
    por file_manager.unir_corpus_acumulado_por_carrera().
    
    Args:
        base_dir: Directorio base con datos (usa BASE_GLOBAL si es None)
        output_dir: Directorio de salida (usa OUTPUT_DIR si es None)
        
    Raises:
        RuntimeError: Si los datos no tienen 'location_final' procesada
    """
    # Usar valores por defecto si no se especifican
    if base_dir is None:
        base_dir = str(BASE_GLOBAL)
    if output_dir is None:
        output_dir = str(OUTPUT_DIR)
    
    # Crear directorio de salida
    os.makedirs(output_dir, exist_ok=True)
    
    print("ANÁLISIS GEOGRÁFICO")
    print(f"Datos: {base_dir}")
    print(f"Salida: {os.path.abspath(output_dir)}")
    print("-" * 50)
    
    try:
        # 1) Cargar datos desde estructura de carpetas
        print("Cargando datos...")
        df = load_all_from_tree(base_dir)
        
        # 2) Limpiar datos básicos
        print("Limpiando datos...")
        df = clean_dataframe(df)
        
        # 3) Procesar países desde location_final (ya extraídos por file_manager)
        print("Procesando ubicaciones...")
        
        if "location_final" in df.columns and df["location_final"].notna().sum() > 0:
            print(f"  Usando {df['location_final'].notna().sum():,} países pre-extraídos")
            # Usar la columna existente y crear las columnas adicionales necesarias
            df["country"] = df["location_final"].fillna("").astype(str)
            df["country_show"] = df["country"].apply(lambda x: title_case_no_accents(x) if x else "")
            df["region_bucket"] = df["country"].apply(lambda x: bucket_from_country(x) if x else "")
        else:
            print("  ADVERTENCIA: Sin location_final - ejecutar file_manager primero")
            raise RuntimeError("Columna 'location_final' no encontrada. Ejecutar unir_corpus_acumulado_por_carrera() primero.")
        
        # 4) Mostrar resumen de datos procesados
        print_data_summary(df)
        
        # 5) Generar todos los gráficos y reportes
        print("Generando reportes...")
        generate_all_charts(df, output_dir, TOP_N_CAREERS, TOP_N_COUNTRIES)
        print(f"  Reportes en: {os.path.abspath(output_dir)}")
        print("-" * 50)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        raise



# ---------------- Función principal para ejecutar desde línea de comandos ----------------
if __name__ == "__main__":
    # Ejecutar el proceso completo con configuración por defecto
    process_job_data()