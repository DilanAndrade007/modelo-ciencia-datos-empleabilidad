import yaml
import os
from datetime import datetime
from extractors.indeed_api import extraer_desde_indeed
from extractors.jooble_api import extraer_desde_jooble
from extractors.rapidapi_api import extraer_desde_rapidapi
from utils.file_manager import (
    cargar_log_existente,
    unir_corpus_por_carrera,
    unir_corpus_acumulado_por_carrera,
    copiar_corpus_diario_a_global
)

# === Fecha actual
fecha_hoy = datetime.now().strftime("%Y-%m-%d")

# === Cargar configuración ===
with open("config/platforms.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# === Mostrar plataformas disponibles habilitadas
plataformas_disponibles = [k for k, v in config.items() if v.get("enabled")]
print("Plataformas habilitadas:", ", ".join(plataformas_disponibles))

seleccion = input(" Escribe la(s) plataforma(s) a ejecutar (ej: jooble,rapidapi), 'todas' o 'ninguna': ").strip().lower()

if seleccion == "ninguna":
    print(" No se ejecutará ninguna plataforma.")
    exit()

if seleccion == "todas":
    plataformas_seleccionadas = plataformas_disponibles
else:
    plataformas_seleccionadas = [p.strip() for p in seleccion.split(",") if p.strip() in plataformas_disponibles]
    if not plataformas_seleccionadas:
        print(" Ninguna plataforma válida fue seleccionada.")
        exit()

# === Función para ejecutar JOOBLE
def ejecutar_jooble():
    api_key = config["jooble"]["api_key"]
    carreras = config["jooble"]["carreras"]
    log_jooble = cargar_log_existente("jooble")

    scraping_ya_hecho = any(
        termino in log_jooble and log_jooble[termino].get("last_extraction_date") == fecha_hoy
        for terminos in carreras.values()
        for termino in terminos
    )

    if scraping_ya_hecho:
        respuesta = input(f"Ya se realizó scraping en Jooble hoy ({fecha_hoy}). ¿Deseas repetir todas las búsquedas? (y/n): ")
        if respuesta.strip().lower() != "y":
            print(" Saltando Jooble.")
            return

    for carrera, terminos in carreras.items():
        print(f"\n Carrera: {carrera} (Jooble)")
        for termino in terminos:
            extraer_desde_jooble(termino, api_key, carrera)
        unir_corpus_por_carrera("jooble", carrera, fecha_hoy)
        copiar_corpus_diario_a_global("jooble", carrera, fecha_hoy)
        unir_corpus_acumulado_por_carrera("jooble", carrera)

# === Función para ejecutar RAPIDAPI
def ejecutar_rapidapi():
    api_key = config["rapidapi"]["api_key"]
    locations = config["rapidapi"].get("locations", ["Ecuador"])
    carreras = config["rapidapi"]["carreras"]
    log_rapid = cargar_log_existente("rapidapi")

    scraping_ya_hecho = any(
        termino in log_rapid and log_rapid[termino].get("last_extraction_date") == fecha_hoy
        for terminos in carreras.values()
        for termino in terminos
    )

    if scraping_ya_hecho:
        respuesta = input(f"Ya se realizó scraping en RapidAPI hoy ({fecha_hoy}). ¿Deseas repetir todas las búsquedas? (y/n): ")
        if respuesta.strip().lower() != "y":
            print(" Saltando RapidAPI.")
            return

    for carrera, terminos in carreras.items():
        print(f"\n Carrera: {carrera} (RapidAPI)")
        for termino in terminos:
            extraer_desde_rapidapi(termino, api_key, carrera, locations)
        unir_corpus_por_carrera("rapidapi", carrera, fecha_hoy)
        copiar_corpus_diario_a_global("rapidapi", carrera, fecha_hoy)
        unir_corpus_acumulado_por_carrera("rapidapi", carrera)

#  def ejecutar_indeed():
#     carreras = config["indeed"]["carreras"]
#     log_indeed = cargar_log_existente("indeed")

#     scraping_ya_hecho = any(
#         termino in log_indeed and log_indeed[termino].get("last_extraction_date") == fecha_hoy
#         for terminos in carreras.values()
#         for termino in terminos
#     )

#     if scraping_ya_hecho:
#         respuesta = input(f"Ya se realizó scraping en Indeed hoy ({fecha_hoy}). ¿Deseas repetir todas las búsquedas? (y/n): ")
#         if respuesta.strip().lower() != "y":
#             print("Saltando Indeed.")
#             return

#     for carrera, terminos in carreras.items():
#         print(f"\n Carrera: {carrera} (Indeed)")
#         for termino in terminos:
#             extraer_desde_indeed(termino, carrera)
#         unir_corpus_por_carrera("indeed", carrera)
#         copiar_corpus_diario_a_global("indeed", carrera)
#         unir_corpus_acumulado_por_carrera("indeed", carrera)


# if "indeed" in plataformas_seleccionadas:
#     ejecutar_indeed()

if "jooble" in plataformas_seleccionadas:
    ejecutar_jooble()

if "rapidapi" in plataformas_seleccionadas:
    ejecutar_rapidapi()

print("\n Proceso finalizado.")
