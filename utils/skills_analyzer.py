"""
Script independiente para análisis de habilidades EURACE.
Genera tablas específicas de habilidades por carrera, país y combinaciones.
"""

import os
import pandas as pd
from pathlib import Path

# Importar funciones desde representations
from representations import (
    load_all_from_tree, 
    clean_dataframe,
    generate_most_demanded_skills,
    generate_skills_by_career,
    generate_skills_by_country,
)

# ===================== CONFIG =====================
REPO_ROOT = Path(__file__).resolve().parent.parent
BASE_GLOBAL = REPO_ROOT / "data" / "outputs" / "todas_las_plataformas"
OUTPUT_DIR = REPO_ROOT / "data" / "outputs" / "reportes" / "habilidades"
# ==================================================

def analyze_skills_only(base_dir: str = None, output_dir: str = None) -> dict:
    """
    Ejecuta solo el análisis de habilidades EURACE.
    
    Args:
        base_dir: Directorio base con datos
        output_dir: Directorio de salida
        
    Returns:
        dict: DataFrames generados con las tablas de habilidades
    """
    # Usar valores por defecto
    if base_dir is None:
        base_dir = str(BASE_GLOBAL)
    if output_dir is None:
        output_dir = str(OUTPUT_DIR)
    
    # Crear directorio de salida
    os.makedirs(output_dir, exist_ok=True)
    
    print("ANÁLISIS DE HABILIDADES EURACE")
    print(f"Datos: {base_dir}")
    print(f"Salida: {os.path.abspath(output_dir)}")
    print("-" * 50)
    
    try:
        # 1) Cargar datos
        print("Cargando datos...")
        df = load_all_from_tree(base_dir)
        
        # 2) Limpiar datos
        print("Limpiando datos...")
        df = clean_dataframe(df)
        
        # 3) Procesar ubicaciones (simplificado - solo para country)
        if "location_final" in df.columns:
            df["country"] = df["location_final"].fillna("").astype(str)
        else:
            print("  ADVERTENCIA: Sin location_final - usando ubicaciones originales")
            df["country"] = df["location"].fillna("").astype(str)
        
        # 4) Generar todas las tablas de habilidades
        print("Generando tablas de habilidades...")
        
        results = {}
        
        # Habilidades más demandadas
        results['most_demanded'] = generate_most_demanded_skills(df, output_dir, top_n=50)
        
        # Habilidades por carrera
        results['by_career'] = generate_skills_by_career(df, output_dir, top_n=20)
        
        # Habilidades por país
        results['by_country'] = generate_skills_by_country(df, output_dir, top_n=30)
        
        print(f"\nTodas las tablas generadas en: {os.path.abspath(output_dir)}")
        print("-" * 50)
        
        return results
        
    except Exception as e:
        print(f"\nERROR: {e}")
        raise

def show_skills_preview(results: dict) -> None:
    """
    Muestra una vista previa de los resultados generados.
    
    Args:
        results: Diccionario con los DataFrames generados
    """
    print("\nVISTA PREVIA DE RESULTADOS:")
    print("=" * 50)
    
    if 'most_demanded' in results and not results['most_demanded'].empty:
        print("\nTOP 10 HABILIDADES MÁS DEMANDADAS:")
        top_10 = results['most_demanded'].head(10)
        for _, row in top_10.iterrows():
            print(f"  {row['habilidad']}: {row['frecuencia_total']:,} empleos ({row['porcentaje_empleos']}%)")
    
    if 'by_career' in results and not results['by_career'].empty:
        print(f"\nCARRERAS ANALIZADAS: {results['by_career']['carrera'].nunique()}")
        careers = results['by_career']['carrera'].unique()[:5]
        for career in careers:
            career_data = results['by_career'][results['by_career']['carrera'] == career]
            top_skill = career_data.iloc[0] if not career_data.empty else None
            if top_skill is not None:
                print(f"  {career}: {top_skill['habilidad']} ({top_skill['frecuencia']} empleos)")
    
    if 'by_country' in results and not results['by_country'].empty:
        print(f"\nPAÍSES ANALIZADOS: {results['by_country']['pais'].nunique()}")
        countries = results['by_country']['pais'].unique()[:5]
        for country in countries:
            country_data = results['by_country'][results['by_country']['pais'] == country]
            top_skill = country_data.iloc[0] if not country_data.empty else None
            if top_skill is not None:
                print(f"  {country}: {top_skill['habilidad']} ({top_skill['frecuencia']} empleos)")

if __name__ == "__main__":
    # Ejecutar análisis completo de habilidades
    results = analyze_skills_only()
    
    # Mostrar vista previa
    show_skills_preview(results)