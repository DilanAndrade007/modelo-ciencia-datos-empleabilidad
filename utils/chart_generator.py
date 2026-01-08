"""
Módulo para generar gráficos y reportes de análisis de empleabilidad.
Contiene funciones para crear visualizaciones y exportar datos.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Manejo de importación para ejecución directa
try:
    from .location_extractor import title_case_no_accents, normalize_career_name, clean_text
except ImportError:
    from location_extractor import title_case_no_accents, normalize_career_name, clean_text

def plot_platform_vs_career(df: pd.DataFrame, outdir: str, top_n_careers: int = 10):
    """
    Genera gráfico de barras apiladas: plataformas vs carreras.
    Agrupa RapidAPI1, RapidAPI2 y CoreSignal como LinkedIn.
    
    Args:
        df: DataFrame con columnas 'career' y 'source'
        outdir: Directorio de salida
        top_n_careers: Número de carreras top a mostrar
    """
    # Agrupar plataformas LinkedIn
    df = df.copy()
    linkedin_platforms = ['rapidapi1', 'rapidapi2', 'coresignal']
    df.loc[df['source'].isin(linkedin_platforms), 'source'] = 'LinkedIn'
    
    # Obtener top carreras por volumen
    top_c = (df.groupby("career").size().sort_values(ascending=False)
               .head(top_n_careers).index.tolist())
    
    dff = df[df["career"].isin(top_c)].copy()
    if dff.empty:
        print("[INFO] Sin datos para Plataforma×Carrera.")
        return
    
    # Crear tabla pivot
    dff["one"] = 1
    tab = dff.pivot_table(index="source", columns="career",
                          values="one", aggfunc="sum", fill_value=0)
    tab = tab.loc[tab.sum(axis=1).sort_values(ascending=False).index]

    # Generar gráfico
    plt.figure(figsize=(12, 6))
    tab.plot(kind="bar", stacked=True, ax=plt.gca())
    plt.title(f"Ofertas por plataforma y carrera (top {top_n_careers} carreras)")
    plt.xlabel("Plataforma")
    plt.ylabel("Número de ofertas")
    plt.xticks(rotation=45, ha="right")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    # Guardar
    out = os.path.join(outdir, "platform_vs_career_stacked.png")
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[OK] {out}")

def plot_top_countries(df: pd.DataFrame, outdir: str, top_n: int = 15):
    """
    Genera gráfico de barras horizontales con top países.
    Excluye Estados Unidos del análisis.
    
    Args:
        df: DataFrame con columna 'country'
        outdir: Directorio de salida
        top_n: Número de países top a mostrar
    """
    # Excluir Estados Unidos
    df = df.copy()
    usa_variants = ['united states', 'usa', 'estados unidos', 'eeuu', 'us']
    df = df[~df['country'].str.lower().isin(usa_variants)]
    
    # Filtrar países válidos
    mask = (~df["country"].isin(["", "remote", "latin america"]))
    vc = df.loc[mask, "country"].value_counts().head(top_n)
    
    if vc.empty:
        print("[INFO] Sin datos para Top países.")
        return
    
    # Formatear nombres para mostrar
    vc_show = vc.rename(index=lambda x: title_case_no_accents(x))
    
    # Generar gráfico
    plt.figure(figsize=(10, 8))
    vc_show.sort_values().plot(kind="barh")
    plt.title(f"Top {top_n} países por volumen de ofertas")
    plt.xlabel("Número de ofertas")
    plt.ylabel("")
    plt.tight_layout()
    
    # Guardar
    out = os.path.join(outdir, "top_countries.png")
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[OK] {out}")

def plot_region_share(df: pd.DataFrame, outdir: str):
    """
    Genera gráfico de barras con distribución porcentual por región.
    
    Args:
        df: DataFrame con columna 'region_bucket'
        outdir: Directorio de salida
    """
    # Calcular porcentajes por región
    order = ["América Latina", "Habla hispana (fuera de LATAM)", "Remoto", "Otros países"]
    counts = df["region_bucket"].value_counts().reindex(order, fill_value=0)
    total = int(counts.sum()) if int(counts.sum()) > 0 else 1
    perc = (counts / total * 100).round(2)

    # Generar gráfico
    plt.figure(figsize=(10, 6))
    bars = perc.plot(kind="bar", color=['#2E8B57', '#4169E1', '#FF6347', '#DAA520'])
    plt.title("Distribución de ofertas por región", fontsize=14, fontweight='bold')
    plt.ylabel("Porcentaje (%)")
    plt.xlabel("")
    plt.xticks(rotation=45, ha="right")
    
    # Agregar etiquetas de porcentaje
    for i, v in enumerate(perc.values):
        plt.text(i, v + 0.5, f"{v:.1f}%", ha="center", va="bottom", fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    
    # Guardar gráfico
    out = os.path.join(outdir, "region_share.png")
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[OK] {out}")

    # Guardar tabla de datos
    region_table = pd.DataFrame({
        "region": perc.index, 
        "porcentaje": perc.values, 
        "conteo": counts.values
    })
    region_table.to_csv(os.path.join(outdir, "region_share_table.csv"), index=False, encoding="utf-8")

def plot_career_distribution(df: pd.DataFrame, outdir: str, top_n: int = 10):
    """
    Genera gráfico con distribución de ofertas por carrera.
    
    Args:
        df: DataFrame con columna 'career'
        outdir: Directorio de salida
        top_n: Número de carreras top a mostrar
    """
    career_counts = df["career"].value_counts().head(top_n)
    career_show = career_counts.rename(index=lambda x: title_case_no_accents(x))
    
    plt.figure(figsize=(12, 8))
    career_show.plot(kind="barh", color='skyblue')
    plt.title(f"Top {top_n} carreras por volumen de ofertas")
    plt.xlabel("Número de ofertas")
    plt.ylabel("")
    plt.tight_layout()
    
    out = os.path.join(outdir, "career_distribution.png")
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[OK] {out}")

def export_top_countries_csv(df: pd.DataFrame, outdir: str):
    """
    Exporta ranking completo de países a CSV.
    
    Args:
        df: DataFrame con columna 'country'
        outdir: Directorio de salida
    """
    mask = (~df["country"].isin(["", "remote", "latin america"]))
    ranking = (df.loc[mask, "country"]
                 .value_counts()
                 .rename_axis("country")
                 .reset_index(name="count"))
    
    ranking["pais"] = ranking["country"].map(title_case_no_accents)
    ranking = ranking[["pais", "count", "country"]]
    
    out_csv = os.path.join(outdir, "top_countries_full.csv")
    ranking.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"[OK] {out_csv}")

def export_career_country_counts_csv(df: pd.DataFrame, outdir: str):
    """
    Exporta tabla granular carrera × país a CSV.
    
    Args:
        df: DataFrame con columnas 'career' y 'country'
        outdir: Directorio de salida
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

    # Presentación: normalización consistente de nombres
    agg["carrera"] = agg["career"].map(title_case_no_accents)
    agg["pais"] = agg["country"].map(title_case_no_accents)

    # Ordenar y seleccionar columnas finales
    out_df = (agg[["carrera", "pais", "numero_de_ofertas"]]
                .sort_values(["carrera", "numero_de_ofertas"], ascending=[True, False]))

    out_csv = os.path.join(outdir, "carrera_pais_numero_de_ofertas.csv")
    out_df.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"[OK] {out_csv}")

def export_career_platform_table(df: pd.DataFrame, outdir: str):
    """
    Exporta tabla cruzada carrera × plataforma a CSV.
    
    Args:
        df: DataFrame con columnas 'career' y 'source'
        outdir: Directorio de salida
    """
    df_temp = df.copy()
    df_temp["one"] = 1
    
    # Crear pivot con nombres originales
    pivot = df_temp.pivot_table(index="career", columns="source", values="one",
                           aggfunc="sum", fill_value=0)
    
    # Ordenar columnas por total
    col_order = pivot.sum(axis=0).sort_values(ascending=False).index
    pivot = pivot[col_order]
    
    # Agregar totales
    pivot["TOTAL_CARRERA"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("TOTAL_CARRERA", ascending=False)
    
    # Fila de totales generales
    total_row = pivot.sum(axis=0).to_frame().T
    total_row.index = ["TOTAL_GENERAL"]
    pivot_final = pd.concat([pivot, total_row], axis=0)
    
    # Normalizar nombres de carreras después del pivot (enfoque consistente)
    pivot_final.index = pivot_final.index.map(lambda x: title_case_no_accents(x) if x != "TOTAL_GENERAL" else x)
    pivot_final.index.name = "carrera"

    out_csv = os.path.join(outdir, "tabla_carrera_por_plataforma.csv")
    pivot_final.to_csv(out_csv, encoding="utf-8")
    print(f"[OK] {out_csv}")

def export_platform_summary(df: pd.DataFrame, outdir: str):
    """
    Exporta resumen por plataforma a CSV.
    
    Args:
        df: DataFrame con columna 'source'
        outdir: Directorio de salida
    """
    platform_stats = df["source"].value_counts().reset_index()
    platform_stats.columns = ["plataforma", "total_ofertas"]
    platform_stats["porcentaje"] = (platform_stats["total_ofertas"] / platform_stats["total_ofertas"].sum() * 100).round(2)
    
    out_csv = os.path.join(outdir, "resumen_plataformas.csv")
    platform_stats.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"[OK] {out_csv}")

def generate_region_share_table(df: pd.DataFrame, outdir: str):
    """
    Genera solo la tabla CSV de distribución por región (sin gráfico).
    
    Args:
        df: DataFrame con columna 'region_bucket'
        outdir: Directorio de salida
    """
    # Calcular porcentajes por región
    order = ["América Latina", "Habla hispana (fuera de LATAM)", "Remoto", "Otros países"]
    counts = df["region_bucket"].value_counts().reindex(order, fill_value=0)
    total = int(counts.sum()) if int(counts.sum()) > 0 else 1
    perc = (counts / total * 100).round(2)

    # Guardar solo tabla de datos
    region_table = pd.DataFrame({
        "region": perc.index, 
        "porcentaje": perc.values, 
        "conteo": counts.values
    })
    
    out_csv = os.path.join(outdir, "region_share_table.csv")
    region_table.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"[OK] {out_csv}")

# ============ FUNCIONES DE ANÁLISIS DE HABILIDADES EURACE ============

def process_eurace_skills(skills_text: str) -> list:
    """
    Procesa una cadena de habilidades EURACE separadas por comas.
    
    Args:
        skills_text: Texto con habilidades separadas por comas
        
    Returns:
        list: Lista de habilidades limpias
    """
    if pd.isna(skills_text) or not skills_text or skills_text.strip() == "":
        return []
    
    # Dividir por comas y limpiar cada habilidad
    skills = [skill.strip() for skill in str(skills_text).split(',')]
    # Filtrar habilidades vacías y normalizar
    skills = [clean_text(skill) for skill in skills if skill.strip()]
    return [skill for skill in skills if skill]  # Filtrar strings vacíos después de clean_text

def generate_most_demanded_skills(df: pd.DataFrame, output_dir: str, top_n: int = 50) -> pd.DataFrame:
    """
    Genera tabla de las habilidades EURACE más demandadas en general.
    
    Args:
        df: DataFrame con datos de empleo
        output_dir: Directorio donde guardar los resultados
        top_n: Número de habilidades top a mostrar
        
    Returns:
        pd.DataFrame: Tabla con las habilidades más demandadas
    """
    print(f"Generando tabla de las {top_n} habilidades más demandadas...")
    
    # Filtrar solo registros con habilidades EURACE
    df_skills = df[df['EURACE_skills'].notna() & (df['EURACE_skills'] != '')].copy()
    
    if df_skills.empty:
        print("  No se encontraron registros con habilidades EURACE")
        return pd.DataFrame()
    
    # Expandir todas las habilidades
    all_skills = []
    for _, row in df_skills.iterrows():
        skills_list = process_eurace_skills(row['EURACE_skills'])
        all_skills.extend(skills_list)
    
    if not all_skills:
        print("  No se pudieron procesar las habilidades")
        return pd.DataFrame()
    
    # Contar frecuencias
    skills_count = pd.Series(all_skills).value_counts().head(top_n)
    
    # Crear DataFrame con estadísticas adicionales
    most_demanded = []
    total_jobs = len(df_skills)
    
    for skill, count in skills_count.items():
        # Calcular en cuántas carreras aparece esta habilidad
        careers_with_skill = df_skills[df_skills['EURACE_skills'].str.contains(skill, case=False, na=False)]['career'].nunique()
        
        # Calcular en cuántos países aparece
        countries_with_skill = df_skills[df_skills['EURACE_skills'].str.contains(skill, case=False, na=False)]['country'].nunique()
        
        most_demanded.append({
            'habilidad': skill,
            'frecuencia_total': count,
            'porcentaje_empleos': round((count / total_jobs) * 100, 2),
            'carreras_presentes': careers_with_skill,
            'paises_presentes': countries_with_skill
        })
    
    df_most_demanded = pd.DataFrame(most_demanded)
    
    # Guardar archivo CSV
    output_file = os.path.join(output_dir, "habilidades_mas_demandadas.csv")
    df_most_demanded.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"[OK] {output_file}")
    
    return df_most_demanded

def generate_skills_by_career(df: pd.DataFrame, output_dir: str, top_n: int = 20) -> pd.DataFrame:
    """
    Genera tabla de habilidades EURACE por carrera.
    
    Args:
        df: DataFrame con datos de empleo
        output_dir: Directorio donde guardar los resultados
        top_n: Número de habilidades top por carrera
        
    Returns:
        pd.DataFrame: Tabla con habilidades por carrera
    """
    print(f"Generando tabla de top {top_n} habilidades por carrera...")
    
    # Filtrar solo registros con habilidades EURACE
    df_skills = df[df['EURACE_skills'].notna() & (df['EURACE_skills'] != '')].copy()
    
    if df_skills.empty:
        print("  No se encontraron registros con habilidades EURACE")
        return pd.DataFrame()
    
    # Expandir habilidades por carrera
    career_skills = []
    for career in df_skills['career'].unique():
        career_data = df_skills[df_skills['career'] == career]
        
        # Recopilar todas las habilidades de esta carrera
        career_skills_list = []
        for _, row in career_data.iterrows():
            skills_list = process_eurace_skills(row['EURACE_skills'])
            career_skills_list.extend(skills_list)
        
        if career_skills_list:
            # Contar frecuencias para esta carrera
            skills_count = pd.Series(career_skills_list).value_counts().head(top_n)
            total_jobs_career = len(career_data)
            
            for skill, count in skills_count.items():
                career_skills.append({
                    'carrera': career,
                    'habilidad': skill,
                    'frecuencia': count,
                    'porcentaje_en_carrera': round((count / total_jobs_career) * 100, 2),
                    'empleos_totales_carrera': total_jobs_career
                })
    
    df_career_skills = pd.DataFrame(career_skills)
    
    # Guardar archivo CSV
    output_file = os.path.join(output_dir, "habilidades_por_carrera.csv")
    df_career_skills.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"[OK] {output_file}")
    
    return df_career_skills

def generate_skills_by_country(df: pd.DataFrame, output_dir: str, top_n: int = 30) -> pd.DataFrame:
    """
    Genera tabla de habilidades EURACE por país.
    
    Args:
        df: DataFrame con datos de empleo
        output_dir: Directorio donde guardar los resultados
        top_n: Número de habilidades top por país
        
    Returns:
        pd.DataFrame: Tabla con habilidades por país
    """
    print(f"Generando tabla de top {top_n} habilidades por país...")
    
    # Filtrar solo registros con habilidades EURACE y países válidos
    df_skills = df[
        (df['EURACE_skills'].notna()) & 
        (df['EURACE_skills'] != '') & 
        (df['country'].notna()) & 
        (df['country'] != '')
    ].copy()
    
    if df_skills.empty:
        print("  No se encontraron registros con habilidades EURACE y países válidos")
        return pd.DataFrame()
    
    # Expandir habilidades por país
    country_skills = []
    for country in df_skills['country'].unique():
        country_data = df_skills[df_skills['country'] == country]
        
        # Recopilar todas las habilidades de este país
        country_skills_list = []
        for _, row in country_data.iterrows():
            skills_list = process_eurace_skills(row['EURACE_skills'])
            country_skills_list.extend(skills_list)
        
        if country_skills_list:
            # Contar frecuencias para este país
            skills_count = pd.Series(country_skills_list).value_counts().head(top_n)
            total_jobs_country = len(country_data)
            
            for skill, count in skills_count.items():
                country_skills.append({
                    'pais': country,
                    'habilidad': skill,
                    'frecuencia': count,
                    'porcentaje_en_pais': round((count / total_jobs_country) * 100, 2),
                    'empleos_totales_pais': total_jobs_country
                })
    
    df_country_skills = pd.DataFrame(country_skills)
    
    # Guardar archivo CSV
    output_file = os.path.join(output_dir, "habilidades_por_pais.csv")
    df_country_skills.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"[OK] {output_file}")
    
    return df_country_skills

def generate_skills_by_career_and_country(df: pd.DataFrame, output_dir: str, top_n: int = 15) -> pd.DataFrame:
    """
    Genera tabla de habilidades EURACE por carrera y país combinado.
    
    Args:
        df: DataFrame con datos de empleo
        output_dir: Directorio donde guardar los resultados
        top_n: Número de habilidades top por combinación
        
    Returns:
        pd.DataFrame: Tabla con habilidades por carrera y país
    """
    print(f"Generando tabla de top {top_n} habilidades por carrera y país...")
    
    # Filtrar solo registros con habilidades EURACE y países válidos
    df_skills = df[
        (df['EURACE_skills'].notna()) & 
        (df['EURACE_skills'] != '') & 
        (df['country'].notna()) & 
        (df['country'] != '') &
        (df['career'].notna()) & 
        (df['career'] != '')
    ].copy()
    
    if df_skills.empty:
        print("  No se encontraron registros con habilidades EURACE, países y carreras válidos")
        return pd.DataFrame()
    
    # Expandir habilidades por carrera y país
    career_country_skills = []
    for career in df_skills['career'].unique():
        for country in df_skills['country'].unique():
            combo_data = df_skills[(df_skills['career'] == career) & (df_skills['country'] == country)]
            
            if combo_data.empty:
                continue
                
            # Recopilar todas las habilidades de esta combinación
            combo_skills_list = []
            for _, row in combo_data.iterrows():
                skills_list = process_eurace_skills(row['EURACE_skills'])
                combo_skills_list.extend(skills_list)
            
            if combo_skills_list:
                # Contar frecuencias para esta combinación
                skills_count = pd.Series(combo_skills_list).value_counts().head(top_n)
                total_jobs_combo = len(combo_data)
                
                for skill, count in skills_count.items():
                    career_country_skills.append({
                        'carrera': career,
                        'pais': country,
                        'habilidad': skill,
                        'frecuencia': count,
                        'porcentaje_en_combinacion': round((count / total_jobs_combo) * 100, 2),
                        'empleos_totales_combinacion': total_jobs_combo
                    })
    
    df_career_country_skills = pd.DataFrame(career_country_skills)
    
    # Guardar archivo CSV
    output_file = os.path.join(output_dir, "habilidades_por_carrera_y_pais.csv")
    df_career_country_skills.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"[OK] {output_file}")
    
    return df_career_country_skills

def generate_all_charts(df: pd.DataFrame, outdir: str, 
                       top_n_careers: int = 10, 
                       top_n_countries: int = 15):
    """
    Genera todos los gráficos y reportes disponibles.
    
    Args:
        df: DataFrame procesado con datos de empleo
        outdir: Directorio de salida
        top_n_careers: Número de carreras top para gráficos
        top_n_countries: Número de países top para gráficos
    """
    print("[INFO] Generando reportes...")
    
    # Crear directorio si no existe
    os.makedirs(outdir, exist_ok=True)
    
    # Gráficos principales PNG
    plot_platform_vs_career(df, outdir, top_n_careers)
    plot_top_countries(df, outdir, top_n_countries)
    plot_region_share(df, outdir)
    plot_career_distribution(df, outdir, top_n_careers)
    
    # Exportar CSVs geográficos y de plataformas
    export_top_countries_csv(df, outdir)
    export_career_country_counts_csv(df, outdir)
    export_career_platform_table(df, outdir)
    export_platform_summary(df, outdir)
    
    # Generar tabla de región (CSV solamente)
    generate_region_share_table(df, outdir)
    
    # Generar análisis de habilidades EURACE
    print("  Generando análisis de habilidades EURACE...")
    generate_most_demanded_skills(df, outdir, top_n=50)
    generate_skills_by_career(df, outdir, top_n=20)
    generate_skills_by_country(df, outdir, top_n=30)
    generate_skills_by_career_and_country(df, outdir, top_n=15)
    
    print("[INFO] Todos los reportes generados")