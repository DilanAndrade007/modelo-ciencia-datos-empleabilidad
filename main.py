import yaml
import os
from datetime import datetime
from extractors.indeed_api import extraer_desde_indeed
from extractors.jooble_api import extraer_desde_jooble
from extractors.rapidapi_api_1 import extraer_desde_rapidapi_1
from extractors.rapidapi_api_2 import extraer_desde_rapidapi_2
from extractors.coresignal_api import extraer_desde_coresignal
from extractors.careerjet_api import extraer_desde_careerjet
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

seleccion = input(" Escribe la(s) plataforma(s) a ejecutar (ej: jooble,rapidapi,coresignal), 'todas' o 'ninguna': ").strip().lower()

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
def ejecutar_rapidapi_1():
    api_key = config["rapidapi1"]["api_key"]
    locations = config["rapidapi1"].get("locations", ["Ecuador"])
    carreras = config["rapidapi1"]["carreras"]
    log_rapid = cargar_log_existente("rapidapi1")

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
            extraer_desde_rapidapi_1(termino, api_key, carrera, locations)
        unir_corpus_por_carrera("rapidapi1", carrera, fecha_hoy)
        copiar_corpus_diario_a_global("rapidapi1", carrera, fecha_hoy)
        unir_corpus_acumulado_por_carrera("rapidapi1", carrera)

# === Función para ejecutar CORESIGNAL
def ejecutar_coresignal():
    api_key = config["coresignal"]["api_key"]
    carreras = config["coresignal"]["carreras"]
    log_core = cargar_log_existente("coresignal")

    scraping_ya_hecho = any(
        termino in log_core and log_core[termino].get("last_extraction_date") == fecha_hoy
        for terminos in carreras.values()
        for termino in terminos
    )

    if scraping_ya_hecho:
        respuesta = input(f"Ya se realizó scraping en Coresignal hoy ({fecha_hoy}). ¿Deseas repetir todas las búsquedas? (y/n): ")
        if respuesta.strip().lower() != "y":
            print(" Saltando Coresignal.")
            return

    for carrera, terminos in carreras.items():
        print(f"\n Carrera: {carrera} (Coresignal)")
        for termino in terminos:
            extraer_desde_coresignal(termino, api_key, carrera)
        unir_corpus_por_carrera("coresignal", carrera, fecha_hoy)
        copiar_corpus_diario_a_global("coresignal", carrera, fecha_hoy)
        unir_corpus_acumulado_por_carrera("coresignal", carrera)

# === Función para ejecutar LINKEDIN RAPIDAPI
def ejecutar_rapidapi_2():
    api_key = config["rapidapi2"]["api_key"]
    locations = config["rapidapi2"].get("locations", ["Ecuador"])
    carreras = config["rapidapi2"]["carreras"]
    log_linkedin = cargar_log_existente("rapidapi2")

    scraping_ya_hecho = any(
        termino in log_linkedin and log_linkedin[termino].get("last_extraction_date") == fecha_hoy
        for terminos in carreras.values()
        for termino in terminos
    )

    if scraping_ya_hecho:
        respuesta = input(f"Ya se realizó scraping en LinkedIn RapidAPI hoy ({fecha_hoy}). ¿Deseas repetir todas las búsquedas? (y/n): ")
        if respuesta.strip().lower() != "y":
            print(" Saltando LinkedIn RapidAPI.")
            return

    for carrera, terminos in carreras.items():
        print(f"\n Carrera: {carrera} (LinkedIn RapidAPI)")
        for termino in terminos:
            extraer_desde_rapidapi_2(termino, api_key, carrera, include_ai=True)
        unir_corpus_por_carrera("rapidapi2", carrera, fecha_hoy)
        copiar_corpus_diario_a_global("rapidapi2", carrera, fecha_hoy)
        unir_corpus_acumulado_por_carrera("rapidapi2", carrera)


# # === Función para ejecutar CAREERJET
# def ejecutar_careerjet():
#     carreras = config["careerjet"]["carreras"]
#     country_code = config["careerjet"].get("country_code", "ec")
#     log_cj = cargar_log_existente("careerjet")
#     scraping_ya_hecho = any(
#         termino in log_cj and log_cj[termino].get("last_extraction_date") == fecha_hoy
#         for terminos in carreras.values()
#         for termino in terminos
#     )
#     if scraping_ya_hecho:
#         respuesta = input(f"Ya se realizó scraping en Careerjet hoy ({fecha_hoy}). ¿Deseas repetir todas las búsquedas? (y/n): ")
#         if respuesta.strip().lower() != "y":
#             print(" Saltando Careerjet.")
#             return
#     for carrera, terminos in carreras.items():
#         print(f"\n Carrera: {carrera} (Careerjet)")
#         for termino in terminos:
#             extraer_desde_careerjet(termino, carrera, country_code)
#         unir_corpus_por_carrera("careerjet", carrera, fecha_hoy)
#         copiar_corpus_diario_a_global("careerjet", carrera, fecha_hoy)
#         unir_corpus_acumulado_por_carrera("careerjet", carrera)

# if "careerjet" in plataformas_seleccionadas:
#     ejecutar_careerjet()


if "coresignal" in plataformas_seleccionadas:
    ejecutar_coresignal()

if "jooble" in plataformas_seleccionadas:
    ejecutar_jooble()

if "rapidapi1" in plataformas_seleccionadas:
    ejecutar_rapidapi_1()

if "rapidapi2" in plataformas_seleccionadas:
    ejecutar_rapidapi_2()

print("\n Proceso finalizado.")
