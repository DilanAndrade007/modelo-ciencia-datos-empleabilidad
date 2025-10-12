"""
Módulo para generar gráficos y reportes de análisis de empleabilidad.
Contiene funciones para crear visualizaciones y exportar datos.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt

# Manejo de importación para ejecución directa
try:
    from .location_extractor import title_case_no_accents
except ImportError:
    from location_extractor import title_case_no_accents

def plot_platform_vs_career(df: pd.DataFrame, outdir: str, top_n_careers: int = 10):
    """
    Genera gráfico de barras apiladas: plataformas vs carreras.
    
    Args:
        df: DataFrame con columnas 'career' y 'source'
        outdir: Directorio de salida
        top_n_careers: Número de carreras top a mostrar
    """
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
    
    Args:
        df: DataFrame con columna 'country'
        outdir: Directorio de salida
        top_n: Número de países top a mostrar
    """
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
    
    ranking["country_show"] = ranking["country"].map(title_case_no_accents)
    ranking = ranking[["country_show", "count", "country"]]
    
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

    # Presentación: título sin acentos
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
    print("[INFO] Generando gráficos y reportes...")
    
    # Crear directorio si no existe
    os.makedirs(outdir, exist_ok=True)
    
    # Gráficos principales
    plot_platform_vs_career(df, outdir, top_n_careers)
    plot_top_countries(df, outdir, top_n_countries)
    plot_region_share(df, outdir)
    plot_career_distribution(df, outdir, top_n_careers)
    
    # Exportar CSVs
    export_top_countries_csv(df, outdir)
    export_career_country_counts_csv(df, outdir)
    export_career_platform_table(df, outdir)
    export_platform_summary(df, outdir)
    
    print("[INFO] Todos los gráficos y reportes generados")