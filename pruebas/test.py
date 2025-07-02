import requests
import json
import time
import csv
import hashlib
from datetime import datetime
from typing import List, Dict, Optional

class JobsAPI:
    """Cliente para la API de trabajos de Coresignal"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.coresignal.com/cdapi/v2"
        self.headers = {
            "apikey": api_key,
            "accept": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def buscar_trabajos(self, filtros: Dict) -> List[int]:
        """
        Busca trabajos usando filtros y devuelve lista de IDs
        
        Filtros disponibles:
        - title: título del trabajo
        - location: ubicación
        - company_name: nombre de la empresa
        """
        url = f"{self.base_url}/job_base/search/filter"
        
        try:
            response = self.session.post(url, json=filtros, timeout=30)
            response.raise_for_status()
            
            job_ids = response.json()
            print(f"✅ Encontrados {len(job_ids)} trabajos")
            return job_ids
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error en búsqueda: {e}")
            return []
    
    def obtener_trabajo(self, job_id: int) -> Optional[Dict]:
        """Obtiene detalles completos de un trabajo por su ID"""
        url = f"{self.base_url}/job_base/collect/{job_id}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error obteniendo trabajo {job_id}: {e}")
            return None
    
    def generar_job_id(self, titulo: str, empresa: str, ubicacion: str, fecha: str) -> str:
        """Genera un hash único para el trabajo"""
        cadena = f"{titulo}_{empresa}_{ubicacion}_{fecha}"
        return hashlib.md5(cadena.encode('utf-8')).hexdigest()
    
    def extraer_skills(self, descripcion: str) -> List[str]:
        """Extrae skills básicas de la descripción (implementación simple)"""
        skills_comunes = [
            'python', 'java', 'javascript', 'react', 'angular', 'vue',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes',
            'git', 'github', 'gitlab', 'jenkins', 'ci/cd',
            'html', 'css', 'nodejs', 'php', 'ruby', 'golang',
            'machine learning', 'data science', 'tensorflow', 'pytorch',
            'scrum', 'agile', 'project management'
        ]
        
        if not descripcion:
            return []
        
        descripcion_lower = descripcion.lower()
        skills_encontradas = []
        
        for skill in skills_comunes:
            if skill.lower() in descripcion_lower:
                skills_encontradas.append(skill)
        
        return skills_encontradas
    
    def mapear_trabajo(self, trabajo_raw: Dict) -> Dict:
        """Mapea los datos de la API a nuestro formato deseado"""
        
        # Extraer datos básicos
        titulo = trabajo_raw.get('title', '')
        empresa = trabajo_raw.get('company_name', '')
        ubicacion = trabajo_raw.get('location', '')
        fecha_creacion = trabajo_raw.get('created', '')
        descripcion = trabajo_raw.get('description', '')
        
        # Generar job_id único
        job_id = self.generar_job_id(titulo, empresa, ubicacion, fecha_creacion)
        
        # Extraer skills
        skills = self.extraer_skills(descripcion)
        
        # Mapear a nuestro formato
        trabajo_mapeado = {
            'job_id': job_id,
            'source': 'coresignal',  # Fuente fija
            'job_title': titulo,
            'company': empresa,
            'location': ubicacion,
            'description': descripcion,
            'skills': ', '.join(skills) if skills else '',
            'careers_required': '',  # Vacío por ahora
            'date_posted': fecha_creacion,
            'url': trabajo_raw.get('url', ''),
            'career_tag': '',  # Vacío para clasificación futura
            'soft_skills_detected': '',  # Vacío para análisis posterior
            'extraction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return trabajo_mapeado
    
    def obtener_trabajos_completos(self, filtros: Dict, limite: int = 10, delay: float = 0.1) -> List[Dict]:
        """
        Busca trabajos y obtiene sus detalles completos en formato mapeado
        """
        print(f"🔍 Buscando trabajos con filtros: {filtros}")
        
        # Paso 1: Buscar IDs
        job_ids = self.buscar_trabajos(filtros)
        
        if not job_ids:
            print("❌ No se encontraron trabajos")
            return []
        
        # Limitar número de trabajos a obtener
        job_ids = job_ids[:limite]
        print(f"📋 Obteniendo detalles de {len(job_ids)} trabajos...")
        
        # Paso 2: Obtener detalles de cada trabajo
        trabajos_mapeados = []
        for i, job_id in enumerate(job_ids, 1):
            print(f"   📄 Obteniendo trabajo {i}/{len(job_ids)} (ID: {job_id})")
            
            trabajo_raw = self.obtener_trabajo(job_id)
            if trabajo_raw:
                trabajo_mapeado = self.mapear_trabajo(trabajo_raw)
                trabajos_mapeados.append(trabajo_mapeado)
            
            # Pausa para evitar rate limiting
            if delay > 0:
                time.sleep(delay)
        
        print(f"✅ Obtenidos {len(trabajos_mapeados)} trabajos completos")
        return trabajos_mapeados

def mostrar_trabajo_detallado(trabajo: Dict):
    """Muestra información detallada de un trabajo en nuestro formato"""
    print(f"""
{'='*60}
📋 JOB ID: {trabajo.get('job_id', 'N/A')}
🌐 SOURCE: {trabajo.get('source', 'N/A')}
💼 JOB TITLE: {trabajo.get('job_title', 'N/A')}
🏢 COMPANY: {trabajo.get('company', 'N/A')}
📍 LOCATION: {trabajo.get('location', 'N/A')}
🔗 URL: {trabajo.get('url', 'N/A')}
📅 DATE POSTED: {trabajo.get('date_posted', 'N/A')}
📊 EXTRACTION DATE: {trabajo.get('extraction_date', 'N/A')}

🎯 SKILLS DETECTED: {trabajo.get('skills', 'Ninguna detectada')}

📝 DESCRIPTION (primeros 300 caracteres):
{trabajo.get('description', 'Sin descripción')[:300]}...

🎓 CAREERS REQUIRED: {trabajo.get('careers_required', 'No especificado')}
🏷️ CAREER TAG: {trabajo.get('career_tag', 'Sin clasificar')}
💭 SOFT SKILLS: {trabajo.get('soft_skills_detected', 'Pendiente análisis')}
{'='*60}
""")

def exportar_a_csv_formato_personalizado(trabajos: List[Dict], archivo: str = "trabajos_extraidos.csv"):
    """Exporta trabajos a CSV en nuestro formato personalizado"""
    
    if not trabajos:
        print("❌ No hay trabajos para exportar")
        return
    
    # Campos en el orden deseado
    campos = [
        'job_id', 'source', 'job_title', 'company', 'location',
        'description', 'skills', 'careers_required', 'date_posted',
        'url', 'career_tag', 'soft_skills_detected', 'extraction_date'
    ]
    
    with open(archivo, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        
        for trabajo in trabajos:
            writer.writerow(trabajo)
    
    print(f"✅ Exportados {len(trabajos)} trabajos a {archivo}")

def mostrar_estadisticas(trabajos: List[Dict]):
    """Muestra estadísticas de los trabajos extraídos"""
    if not trabajos:
        print("❌ No hay trabajos para analizar")
        return
    
    print(f"""
📊 ESTADÍSTICAS DE EXTRACCIÓN
{'='*40}
🔢 Total trabajos: {len(trabajos)}
🏢 Empresas únicas: {len(set(t.get('company', '') for t in trabajos if t.get('company')))}
📍 Ubicaciones únicas: {len(set(t.get('location', '') for t in trabajos if t.get('location')))}

🎯 SKILLS MÁS COMUNES:
""")
    
    # Contar skills
    todas_skills = []
    for trabajo in trabajos:
        skills_str = trabajo.get('skills', '')
        if skills_str:
            skills_lista = [s.strip() for s in skills_str.split(',') if s.strip()]
            todas_skills.extend(skills_lista)
    
    if todas_skills:
        from collections import Counter
        skills_counter = Counter(todas_skills)
        for skill, count in skills_counter.most_common(10):
            print(f"   • {skill}: {count} veces")
    else:
        print("   • No se detectaron skills")

def ejemplo_completo():
    """Ejemplo completo con tu API key"""
    
    # Tu API key
    API_KEY = "cRreeqnOAOmLIp14RV9zNM7uV9bbfKpz"
    
    # Crear cliente
    api = JobsAPI(API_KEY)
    
    print("=" * 80)
    print("🚀 EXTRACTOR DE TRABAJOS - FORMATO PERSONALIZADO")
    print("=" * 80)
    
    # Ejemplo 1: Buscar desarrolladors Python
    print("\n1️⃣ BÚSQUEDA: DESARROLLADORES PYTHON")
    trabajos_python = api.obtener_trabajos_completos({"title": "python developer"}, limite=3)
    
    print(f"\n📋 RESULTADOS ENCONTRADOS ({len(trabajos_python)} trabajos):")
    for trabajo in trabajos_python:
        mostrar_trabajo_detallado(trabajo)
    
    # Ejemplo 2: Buscar trabajos remotos
    print("\n2️⃣ BÚSQUEDA: TRABAJOS REMOTOS")
    trabajos_remotos = api.obtener_trabajos_completos({"location": "remote"}, limite=2)
    
    print(f"\n📋 RESULTADOS ENCONTRADOS ({len(trabajos_remotos)} trabajos):")
    for trabajo in trabajos_remotos:
        mostrar_trabajo_detallado(trabajo)
    
    # Combinar todos los trabajos
    todos_trabajos = trabajos_python + trabajos_remotos
    
    # Mostrar estadísticas
    print("\n📊 ESTADÍSTICAS GENERALES:")
    mostrar_estadisticas(todos_trabajos)
    
    # Exportar a CSV
    print("\n💾 EXPORTANDO RESULTADOS...")
    exportar_a_csv_formato_personalizado(todos_trabajos)
    
    print(f"\n✅ PROCESO COMPLETADO")
    print(f"📁 Archivo generado: trabajos_extraidos.csv")
    print(f"📊 Total trabajos procesados: {len(todos_trabajos)}")

def probar_trabajo_individual():
    """Prueba obtener un trabajo individual para ver la estructura completa"""
    API_KEY = "cRreeqnOAOmLIp14RV9zNM7uV9bbfKpz"
    api = JobsAPI(API_KEY)
    
    print("\n🔍 PROBANDO TRABAJO INDIVIDUAL...")
    
    # Primero buscar algunos IDs
    job_ids = api.buscar_trabajos({"title": "developer"})
    
    if job_ids:
        # Tomar el primer ID
        primer_id = job_ids[0]
        print(f"📋 Obteniendo trabajo con ID: {primer_id}")
        
        # Obtener datos raw
        trabajo_raw = api.obtener_trabajo(primer_id)
        
        if trabajo_raw:
            print("\n📄 DATOS RAW DE LA API:")
            print("="*50)
            print(json.dumps(trabajo_raw, indent=2, ensure_ascii=False)[:1000] + "...")
            
            print("\n📋 DATOS MAPEADOS:")
            trabajo_mapeado = api.mapear_trabajo(trabajo_raw)
            mostrar_trabajo_detallado(trabajo_mapeado)

if __name__ == "__main__":
    # Ejecutar ejemplo completo
    ejemplo_completo()
    
    # Descomentar para ver estructura raw de un trabajo individual
    # probar_trabajo_individual()