import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from datetime import datetime
import hashlib
import time
from utils.file_manager import guardar_log, crear_directorios, cargar_log_existente

def generar_job_id(titulo, empresa, ubicacion, fecha):
    """Genera un ID único para cada trabajo"""
    texto = f"{titulo}_{empresa}_{ubicacion}_{fecha}"
    return hashlib.md5(texto.encode("utf-8")).hexdigest()

def normalizar_oferta_indeed(job, carrera, fecha_hoy):
    """Normaliza una oferta de Indeed al formato estándar"""
    try:
        titulo = job.select_one("h2.jobTitle span").text.strip()
        empresa = job.select_one("span.companyName").text.strip()
        ubicacion = job.select_one("div.companyLocation").text.strip()
        descripcion = job.select_one("div.job-snippet").text.strip().replace("\n", " ")
        enlace = job.find("a", href=True)['href']
        url_oferta = f"https://ec.indeed.com{enlace}"
        
        job_id = generar_job_id(titulo, empresa, ubicacion, fecha_hoy)
        
        return {
            "job_id": job_id,
            "source": "indeed",
            "job_title": titulo,
            "company": empresa,
            "location": ubicacion,
            "description": descripcion,
            "skills": [],
            "careers_required": carrera,
            "date_posted": fecha_hoy,
            "url": url_oferta,
            "career_tag": "",
            "soft_skills_detected": [],
            "extraction_date": fecha_hoy
        }
    except Exception as e:
        print(f"❌ Error al normalizar oferta: {e}")
        return None

def buscar_indeed_pagina(driver, termino, pagina, fecha_hoy, carrera):
    """Busca ofertas en una página específica de Indeed"""
    url = f"https://ec.indeed.com/jobs?q={termino}&l=Ecuador&start={pagina * 10}"
    print(f"🔍 Procesando página {pagina + 1} para término '{termino}' en Indeed...")
    
    try:
        driver.get(url)
        
        # Pausar para resolver CAPTCHA manualmente si es necesario
        input("🧩 Presiona ENTER cuando la página esté lista (si hay CAPTCHA, resuélvelo primero)...")
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        empleos = soup.select("div.job_seen_beacon")
        
        if not empleos:
            print(f"⚠️ No se encontraron ofertas en la página {pagina + 1}")
            return [], False
        
        resultados_pagina = []
        for job in empleos:
            oferta_normalizada = normalizar_oferta_indeed(job, carrera, fecha_hoy)
            if oferta_normalizada:
                resultados_pagina.append(oferta_normalizada)
        
        print(f"✅ Página {pagina + 1}: {len(resultados_pagina)} ofertas extraídas")
        return resultados_pagina, True
        
    except Exception as e:
        print(f"❌ Error en página {pagina + 1}: {e}")
        return [], False

def extraer_desde_indeed(termino, carrera):
    """Función principal para extraer ofertas de Indeed con manejo de logs y páginas existentes"""
    HOY = datetime.now().strftime("%Y-%m-%d")
    fuente = "indeed"
    
    # Crear directorios necesarios
    crear_directorios()
    
    # === Reanudar desde log si existe ===
    log = cargar_log_existente(fuente)
    pagina_inicial = 0
    
    if termino in log:
        ultima_fecha = log[termino].get("last_extraction_date")
        if ultima_fecha == HOY:
            pagina_inicial = log[termino].get("last_page_extracted", 0) + 1
            print(f"🔄 Reanudando desde página {pagina_inicial + 1} (mismo día: {HOY})")
        else:
            print(f"🆕 Nueva ejecución para '{termino}' en un día distinto ({HOY}). Iniciando desde página 1.")
    else:
        print(f"🆕 Primera ejecución para '{termino}' hoy ({HOY}). Iniciando desde página 1.")
    
    # Configurar navegador
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    
    try:
        resultados = []
        pagina = pagina_inicial
        
        # Buscar en todas las páginas hasta que no haya más resultados
        while True:
            ofertas_pagina, continuar = buscar_indeed_pagina(driver, termino, pagina, HOY, carrera)
            
            if ofertas_pagina:
                resultados.extend(ofertas_pagina)
            
            if not continuar:
                print(f"🛑 Deteniendo extracción en página {pagina + 1} (no hay más resultados)")
                break
            
            pagina += 1
            
            # Pausa entre páginas para evitar bloqueos
            time.sleep(2)
        
        # === Crear carpeta por carrera ===
        directorio = f"data/outputs/{fuente}/{carrera.replace(' ', '_')}"
        os.makedirs(directorio, exist_ok=True)
        nombre_csv = f"{directorio}/{fuente}__{termino.replace(' ', '_')}__{HOY}.csv"
        
        # === Si ya existe archivo, unir y deduplicar ===
        if resultados:
            df = pd.DataFrame(resultados)
            
            if os.path.exists(nombre_csv):
                print(f"📄 Archivo existente encontrado, uniendo datos...")
                df_existente = pd.read_csv(nombre_csv)
                df = pd.concat([df_existente, df], ignore_index=True)
                df.drop_duplicates(subset="job_id", inplace=True)
            
            df.to_csv(nombre_csv, index=False)
            print(f"💾 Archivo guardado: {nombre_csv} ({len(df)} ofertas totales)")
            
            # === Guardar log actualizado ===
            guardar_log(fuente, termino, HOY, len(df), pagina)
            print(f"📊 Log actualizado - Total: {len(df)} ofertas, Última página: {pagina + 1}")
            
        else:
            print("⚠️ No se extrajeron nuevas ofertas en esta sesión")
        
        return resultados
        
    except Exception as e:
        print(f"❌ Error general en extracción: {e}")
        return []
        
    finally:
        driver.quit()
        print("🔚 Navegador cerrado")