

## 📋 INFORME COMPLETO: COMPONENTE DE DESPLIEGUE

### ✅ ELEMENTOS IMPLEMENTADOS DEL COMPONENTE DE DESPLIEGUE

---

## **1. ENTREGABLES PRINCIPALES** ✓

### **1.1 Corpus Consolidado por Carrera** ✓

**Ubicación**: `data/outputs/todas_las_plataformas/[Carrera]/[Carrera]_Merged.csv`

**Script responsable**: file_manager.py - Función `unir_corpus_acumulado_por_carrera()`

**Características implementadas**:
- ✅ Deduplicación por `job_id` (SHA256 hash)
- ✅ Unificación de esquema entre plataformas
- ✅ Estructura por carrera con 26 carreras activas
- ✅ Columnas de trazabilidad: `job_id`, `source`, `url`, `extraction_date`
- ✅ Columnas analíticas: `EURACE_skills`, `initial_skills`
- ✅ Columna procesada: `description_final`
- ✅ Extracción geográfica: `location_final` con países

**Código clave**:
```python
# file_manager.py líneas 71-167
def unir_corpus_acumulado_por_carrera():
    """Deduplica por 'job_id' y guarda '<Carrera>_Merged.csv'"""
    # Recalcula job_id con SHA256
    # Deduplica por job_id
    # Extrae países a location_final
    # Reordena columnas
```

---

### **1.2 Artefactos Intermedios por Plataforma** ✓

**Ubicación**: `data/outputs/[plataforma]/[Carrera]/corpus_unido/`

**Patrón de nombres**: `[fuente]__[Carrera]__YYYY-MM-DD__merged.csv`

**Script responsable**: file_manager.py - Función `unir_corpus_por_carrera()`

**Características**:
- ✅ Corpus diario por plataforma y carrera
- ✅ Copiado automático a carpeta global (file_manager.py)
- ✅ Auditoría de origen por fuente
- ✅ Trazabilidad temporal de extracciones

**Plataformas activas**:
- `jooble/`
- `rapidapi1/` (JSSearch)
- `rapidapi2/` (LinkedIn)
- `coresignal/`

---

### **1.3 Logs de Extracción** ✓

**Ubicación**: `logs/[plataforma]_log.json`

**Script responsable**: file_manager.py - Funciones `guardar_log()` y `cargar_log_existente()`

**Estructura del log**:
```json
{
  "keyword": {
    "last_extraction_date": "YYYY-MM-DD",
    "total_offers_extracted": 400,
    "last_page_extracted": 4
  }
}
```

**Logs existentes**:
- ✅ rapidapi2_log.json (LinkedIn)
- ✅ `coresignal_log.json`
- ✅ `jooble_log.json`
- ✅ `rapidapi1_log.json`

**Funcionalidades**:
- ✅ Control de re-extracción (evita duplicados diarios)
- ✅ Continuidad de ejecución por página
- ✅ Auditoría operativa completa

---

### **1.4 Reportes y Productos de Comunicación** ✓

**Ubicación**: reportes

**Script responsable**: chart_generator.py - Función `generate_all_charts()`

**Gráficos PNG generados**:
- ✅ `platform_vs_career_stacked.png` - Distribución plataforma×carrera
- ✅ `top_countries.png` - Top 15 países (excluye USA)
- ✅ `region_share.png` - Distribución regional
- ✅ `career_distribution.png` - Top 10 carreras
- ✅ `mapa.html` - Mapa interactivo de ubicaciones

**CSVs analíticos generados**:
```
reportes/Quarto_View/Data/
├── carrera_pais_numero_de_ofertas.csv       ✓
├── tabla_carrera_por_plataforma.csv         ✓
├── top_countries_full.csv                   ✓
├── resumen_plataformas.csv                  ✓
├── region_share_table.csv                   ✓
├── habilidades_mas_demandadas.csv           ✓
├── habilidades_por_carrera.csv              ✓
├── habilidades_por_pais.csv                 ✓
└── habilidades_por_carrera_y_pais.csv       ✓
```

**Código clave**:
```python
# chart_generator.py líneas 554-603
def generate_all_charts(df, outdir, top_n_careers=10, top_n_countries=15):
    """Genera todos los gráficos y reportes disponibles"""
    # Gráficos PNG
    # CSVs geográficos
    # Análisis de habilidades EURACE
```

---

### **1.5 Reporte Reproducible en Quarto** ✓

**Ubicación**: Quarto_View

**Estructura verificada**:
```
Quarto_View/
├── ReporteQuarto.qmd           ✓ (documento fuente)
├── ReporteQuarto.html          ✓ (reporte renderizado)
├── custom.css                  ✓ (estilos personalizados)
├── ReporteQuarto_files/        ✓ (recursos automáticos)
└── Data/                       ✓ (9 CSVs analíticos)
```

**Características**:
- ✅ Regenerable automáticamente
- ✅ Insumos tabulares en Data
- ✅ Integración tablas + figuras + narrativa
- ✅ Separación datos/visualizaciones/documento

---

## **2. PROCEDIMIENTO DE DESPLIEGUE REPRODUCIBLE** ✓

### **2.1 Entorno de Ejecución** ✓

**Archivo de dependencias**: env_tic_requirements.txt

**Entornos virtuales verificados**:
- ✅ env_tic (Python environment activo)
- ✅ env_dtic (entorno alternativo)

**Dependencias críticas**:
- pandas, numpy
- pyyaml
- rapidfuzz
- deep-translator
- matplotlib
- requests

---

### **2.2 Configuración del Componente** ✓

**Archivos de configuración**:

#### platforms.yml
```yaml
# Parámetros de extracción por plataforma
# Fuentes habilitadas (enabled: true/false)
# Keywords por carrera (375 líneas)
```

**Contenido verificado**:
- ✅ Claves API por plataforma
- ✅ 26 carreras configuradas
- ✅ Keywords específicos por carrera
- ✅ Control de habilitación por fuente

#### skills.yml
```yaml
# Diccionario EURACE
# 7 categorías raíz
# Términos canónicos, patrones regex, banco fuzzy
```

---

### **2.3 Ejecución del Pipeline** ✓

**Flujo completo documentado**:

#### **FASE 1: Extracción** → main.py
```
Entrada: config/platforms.yml
Salida: data/outputs/[plataforma]/[Carrera]/
        + logs/[plataforma]_log.json
```

**Funciones implementadas**:
- ✅ `ejecutar_jooble()` - línea 56
- ✅ `ejecutar_rapidapi_1()` - línea 79
- ✅ `ejecutar_rapidapi_2()` - línea 128
- ✅ `ejecutar_coresignal()` - línea 101

**Características**:
- ✅ Control de re-extracción diaria
- ✅ Actualización automática de logs
- ✅ Unión por carrera post-extracción
- ✅ Copia a carpeta global

---

#### **FASE 2: Unificación y Deduplicación** → file_manager.py

**Scripts ejecutables**:

```python
# 1) Unir archivos por plataforma y fecha
unir_corpus_por_carrera(fuente, carrera, fecha)  # línea 169

# 2) Copiar a carpeta global
copiar_corpus_diario_a_global(fuente, carrera, fecha)  # línea 53

# 3) Unir y deduplicar corpus completo
unir_corpus_acumulado_por_carrera()  # línea 71
```

**Proceso implementado**:
- ✅ Recalcula `job_id` con SHA256
- ✅ Deduplica por `job_id` único
- ✅ Extrae países a `location_final`
- ✅ Reordena columnas lógicamente

**Invocación desde main.py**:
```python
if seleccion in {"unir"}:
    unir_corpus_acumulado_por_carrera()
```

---

#### **FASE 3: Traducción** → Traductor_Descripcion.py

**Función principal**: `translate_all_careers()` (inferido del código)

**Características implementadas**:
- ✅ Traducción a inglés con Google Translator
- ✅ Generación de `description_final`
- ✅ Limpieza HTML/URLs/emails/emojis
- ✅ Normalización de markdown y viñetas
- ✅ Control de fallos con marcador `[GT_FAIL]`
- ✅ Caché de traducciones previas
- ✅ Procesamiento multihilo (MAX_WORKERS=2)

**Código clave** (líneas 1-80):
```python
DESCRIPTION_COL = "description"
NEW_COL = "description_final"
FAIL_MARKER = "[GT_FAIL]"
# Extenso pipeline de limpieza regex
```

---

#### **FASE 4: Normalización** → Normalizador_Independiente.py

**Función**: Normalizar `description_final`

**Operaciones implementadas** (líneas 1-80):
- ✅ Limpieza HTML/URLs/emails/emojis adicional
- ✅ Remoción de viñetas y markdown
- ✅ Eliminación de separadores decorativos
- ✅ Normalización de tags de idioma
- ✅ Colapso de puntos repetidos
- ✅ Normalización de Q&A → QA
- ✅ Espaciado y puntuación consistente

**Código clave**:
```python
FINAL_COL = "description_final"
FAIL_MARKER = "[GT_FAIL]"  # No modifica filas fallidas
# Múltiples regex para normalización avanzada
```

---

#### **FASE 5: Traducción de Skills** → Traductor_Skills.py

**Función**: Traducir columna `skills` cuando existe

*Script mencionado en la descripción pero pendiente de análisis completo*

---

#### **FASE 6: Extracción de Habilidades EURACE** → Extract_Habilidades.py

**Función principal**: `run_all()` (línea 243)

**Columnas generadas**:
- ✅ `EURACE_skills` - Categorías detectadas (orden YAML)
- ✅ `initial_skills` - Términos específicos agrupados por categoría

**Características implementadas** (líneas 1-255):
- ✅ Carga diccionario desde skills.yml
- ✅ Compilación de patrones regex
- ✅ Detección explícita + implícita
- ✅ Rescate fuzzy con rapidfuzz (umbral 90%)
- ✅ Sobrescritura controlada del CSV original
- ✅ Sin detección de negaciones

**Código clave**:
```python
EURACE_COL = "EURACE_skills"
INIT_COL = "initial_skills"
OVERWRITE = True  # Sobrescribe CSV original
FUZZY_THRESHOLD = 90
```

**Flujo de extracción**:
```python
def extract_from_text(raw_text, order, compiled, ...):
    # 1) Regex (explícito + implícito)
    # 2) Rescate difuso por categoría
    # 3) Construcción EURACE_skills (orden YAML)
    # 4) Construcción initial_skills agrupadas
```

---

#### **FASE 7: Eliminación de Filas Vacías** → Eliminar_Filas_Vacias.py

**Función principal**: `clean_file(file_path)` (línea 46)

**Criterio implementado** (líneas 1-102):
- ✅ Elimina filas donde AMBAS columnas están vacías:
  - `description` vacía/NaN/"[]"
  - `skills` vacía/NaN/"[]"
- ✅ Mantiene filas con AL MENOS una columna con contenido
- ✅ Detección de "[]" como vacío con regex

**Código clave**:
```python
DESCRIPTION_COL = "description"
SKILLS_COL = "skills"
BRACKETS_EMPTY_RE = re.compile(r"^\s*\[\s*\]\s*$")

def series_is_empty_like(s):
    # NaN | blank | "[]" → True
```

---

#### **FASE 8: Generación de Reportes** → representations.py + chart_generator.py

**Función orquestadora**: `process_job_data()` en representations.py

**Pipeline implementado** (líneas 234-289):
```python
def process_job_data(base_dir, output_dir):
    # FASE 1: Carga y limpieza
    df = load_all_from_tree(base_dir)
    df = clean_dataframe(df)
    
    # FASE 2: Procesamiento geográfico
    # Usa location_final pre-procesada
    
    # FASE 3: Resumen de datos
    print_data_summary(df)
    
    # FASE 4: Generación de reportes
    generate_all_charts(df, output_dir, TOP_N_CAREERS, TOP_N_COUNTRIES)
```

**Funciones de generación** en chart_generator.py:

**Gráficos PNG**:
- ✅ `plot_platform_vs_career()` - línea 18 (agrupa LinkedIn)
- ✅ `plot_top_countries()` - línea 52 (excluye USA)
- ✅ `plot_region_share()` - línea 104
- ✅ `plot_career_distribution()` - línea 146

**Exportaciones CSV**:
- ✅ `export_top_countries_csv()` - línea 173
- ✅ `export_career_country_counts_csv()` - línea 189
- ✅ `export_career_platform_table()` - línea 220
- ✅ `export_platform_summary()` - línea 259
- ✅ `generate_region_share_table()` - línea 273

**Análisis de habilidades EURACE**:
- ✅ `generate_most_demanded_skills()` - línea 308 (top 50 global)
- ✅ `generate_skills_by_career()` - línea 367 (top 20 por carrera)
- ✅ `generate_skills_by_country()` - línea 419 (top 30 por país)
- ✅ `generate_skills_by_career_and_country()` - línea 473 (top 15 combinado)

**Entrada**: todas_las_plataformas
**Salida**: Data

---

## **3. VERIFICACIÓN DE DESPLIEGUE** ⚠️

### **Criterios definidos vs Implementados**:

| Criterio | Estado | Ubicación código |
|----------|--------|------------------|
| Existencia de `[Carrera]_Merged.csv` | ✅ Verificado (26 carreras) | Sistema de archivos |
| Presencia de columnas esenciales | ✅ Implementado | file_manager.py |
| Unicidad de `job_id` | ✅ Implementado | file_manager.py (deduplicación) |
| Validez de `EURACE_skills` | ⚠️ **NO automatizado** | - |
| Existencia de reportes | ✅ Verificado | 9 CSVs + 4 PNGs + mapa |
| **Script de verificación automatizado** | ❌ **FALTANTE** | - |

---

## **4. CONSUMO DE RESULTADOS** ✓

### **4.1 Consumo Analítico**

**Archivos para análisis directo**:
```python
# Cargar corpus por carrera
df = pd.read_csv("data/outputs/todas_las_plataformas/Ciencia_de_Datos/Ciencia_de_Datos_Merged.csv")

# Columnas disponibles para análisis
df.columns:
    - job_id, source, url, extraction_date (trazabilidad)
    - description_final (texto procesado)
    - EURACE_skills, initial_skills (habilidades)
    - location_final (países)
```

---

### **4.2 Consumo Comunicacional (Tesis)**

**Artefactos disponibles**:
- ✅ Reporte Quarto reproducible (HTML + QMD)
- ✅ 9 tablas CSV con estadísticas
- ✅ 4 gráficos PNG publicables
- ✅ Mapa interactivo HTML
- ✅ Trazabilidad completa hasta CSVs finales

---

## **5. CONSIDERACIONES DE MANTENIMIENTO** ✓

### **5.1 Actualización del Corpus**

**Mecanismos implementados**:
- ✅ Logs permiten continuidad por keyword/página (file_manager.py)
- ✅ Deduplicación por `job_id` evita inflación (file_manager.py)
- ✅ Re-ejecución de pipeline actualiza datasets

**Comando de actualización**:
```bash
# 1) Extraer nuevas ofertas
python main.py
# Seleccionar plataformas → extrae → unifica → actualiza logs

# 2) Unir corpus acumulado
python main.py
# Escribir "unir" → deduplica y regenera [Carrera]_Merged.csv

# 3) Procesar textos
python utils/Traductor_Descripcion.py
python utils/Normalizador_Independiente.py
python utils/Extract_Habilidades.py
python utils/Eliminar_Filas_Vacias.py

# 4) Regenerar reportes
python utils/representations.py
```

---

### **5.2 Regeneración de Reportes**

**Script automatizado**: representations.py

```python
from utils.representations import process_job_data

# Regenera TODOS los reportes desde CSVs finales
process_job_data()
```

**Características**:
- ✅ Consume `[Carrera]_Merged.csv` automáticamente
- ✅ Genera CSVs en `Quarto_View/Data/`
- ✅ Reporte Quarto puede regenerarse con `quarto render`
- ✅ Sin necesidad de edición manual

---

## **6. ELEMENTOS FALTANTES O MEJORABLES** ⚠️

### **6.1 Script de Verificación Automatizado** ❌

**No implementado**: Un script que ejecute todos los criterios de aceptación

**Propuesta de implementación**:
```python
# utils/verificar_despliegue.py (NUEVO)

def verificar_despliegue():
    """
    Ejecuta checklist de verificación de despliegue:
    - Existencia de [Carrera]_Merged.csv para todas las carreras
    - Presencia de columnas esenciales
    - Unicidad de job_id
    - Validez de EURACE_skills (7 categorías raíz)
    - Existencia de reportes esperados
    """
    pass
```

---

### **6.2 Script Orquestador Completo del Pipeline** ⚠️

**Parcialmente implementado**: main.py solo hace extracción + unión básica

**Faltante**: Script que ejecute **TODA** la secuencia:
```bash
main.py → Traductor_Descripcion → Normalizador → 
Traductor_Skills → Extract_Habilidades → Eliminar_Filas_Vacias → 
representations.py
```

**Propuesta**:
```python
# pipeline_completo.py (NUEVO)

def ejecutar_pipeline_completo(plataformas=None):
    """
    Ejecuta el pipeline de despliegue completo:
    1. Extracción (main.py)
    2. Unificación (file_manager)
    3. Traducción (Traductor_Descripcion)
    4. Normalización (Normalizador_Independiente)
    5. Traducción skills (Traductor_Skills)
    6. Extracción habilidades (Extract_Habilidades)
    7. Limpieza (Eliminar_Filas_Vacias)
    8. Reportes (representations)
    9. Verificación (verificar_despliegue)
    """
    pass
```

---

### **6.3 Documentación del Orden de Ejecución** ⚠️

**Parcialmente documentado**: README muestra la estructura pero no el flujo completo

**Propuesta**: Agregar sección en README:
```markdown
## 🔄 Pipeline de Despliegue Completo

### Orden de Ejecución (CRÍTICO - Seguir secuencia)

1. **Extracción**: `python main.py`
2. **Unificación**: `python main.py` (opción "unir")
3. **Traducción**: `python utils/Traductor_Descripcion.py`
4. **Normalización**: `python utils/Normalizador_Independiente.py`
5. **Traducción skills**: `python utils/Traductor_Skills.py`
6. **Extracción habilidades**: `python utils/Extract_Habilidades.py`
7. **Limpieza**: `python utils/Eliminar_Filas_Vacias.py`
8. **Reportes**: `python utils/representations.py`
9. **Verificación**: `python utils/verificar_despliegue.py`
```

---

### **6.4 Tests Automatizados** ❌

**No implementados**: Tests unitarios o de integración

**Propuesta**:
```python
# tests/test_despliegue.py (NUEVO)
import pytest

def test_job_id_uniqueness():
    """Verifica unicidad de job_id en corpus final"""
    pass

def test_eurace_categories_valid():
    """Verifica que EURACE_skills contenga solo categorías válidas"""
    pass

def test_required_columns_present():
    """Verifica presencia de columnas esenciales"""
    pass
```

---

## **7. DIAGRAMA DE FLUJO DEL DESPLIEGUE**

```
┌─────────────────────────────────────────────────────────┐
│                   COMPONENTE DESPLIEGUE                  │
└─────────────────────────────────────────────────────────┘

┌─────────────┐
│  main.py    │ ← config/platforms.yml
│ Extracción  │
└──────┬──────┘
       │ Salida: data/outputs/[plataforma]/[Carrera]/
       │         logs/[plataforma]_log.json
       ↓
┌────────────────────┐
│  file_manager.py   │
│  1) unir_corpus_   │
│     por_carrera()  │
│  2) copiar a       │
│     global         │
│  3) unir_corpus_   │
│     acumulado()    │
└─────────┬──────────┘
          │ Salida: [Carrera]_Merged.csv (preliminar)
          ↓
┌─────────────────────────┐
│ Traductor_Descripcion   │ ← Google Translator API
│ description_final       │
└──────────┬──────────────┘
           │
           ↓
┌──────────────────────────┐
│ Normalizador_            │
│ Independiente            │
│ (limpieza description_   │
│  final)                  │
└──────────┬───────────────┘
           │
           ↓
┌─────────────────────┐
│ Traductor_Skills    │
│ (traduce skills)    │
└──────────┬──────────┘
           │
           ↓
┌──────────────────────────┐
│ Extract_Habilidades      │ ← config/skills.yml
│ EURACE_skills            │
│ initial_skills           │
└──────────┬───────────────┘
           │ Sobrescribe [Carrera]_Merged.csv
           ↓
┌──────────────────────┐
│ Eliminar_Filas_      │
│ Vacias               │
│ (filas sin desc      │
│  ni skills)          │
└──────────┬───────────┘
           │
           ↓
┌─────────────────────────────────────┐
│ [Carrera]_Merged.csv FINAL          │
│ ✓ job_id, source, url, extraction_  │
│   date                               │
│ ✓ description_final (limpio)        │
│ ✓ EURACE_skills, initial_skills     │
│ ✓ location_final (países)           │
└──────────┬──────────────────────────┘
           │
           ↓
┌──────────────────────────┐
│ representations.py       │
│ + chart_generator.py     │
│                          │
│ Genera:                  │
│ - 4 gráficos PNG         │
│ - 9 CSVs analíticos      │
│ - mapa.html              │
└──────────┬───────────────┘
           │
           ↓
┌───────────────────────────────────┐
│ ENTREGABLES FINALES               │
│                                   │
│ 1) [Carrera]_Merged.csv (26)      │
│ 2) Archivos por plataforma/fecha  │
│ 3) Logs JSON (4)                  │
│ 4) Reportes PNG (4)               │
│ 5) Reportes CSV (9)               │
│ 6) ReporteQuarto.html             │
│ 7) mapa.html                      │
└───────────────────────────────────┘
```

---

## **8. RESUMEN EJECUTIVO**

### ✅ **Completamente Implementado**:
- Corpus consolidado por carrera (26 carreras)
- Artefactos intermedios por plataforma
- Logs de extracción (trazabilidad)
- Reportes visuales y tabulares
- Reporte Quarto reproducible
- Configuración YAML (plataformas + skills)
- Pipeline de procesamiento (8 scripts)

### ⚠️ **Parcialmente Implementado**:
- Script orquestador completo
- Documentación de flujo secuencial
- Verificación de EURACE válidas

### ❌ **Faltante**:
- Script de verificación automatizado
- Tests automatizados
- Manejo de errores robusto en pipeline

---

## **9. RECOMENDACIONES PARA ENRIQUECER EL DESPLIEGUE**

### **Alta Prioridad**:

1. **Crear `pipeline_completo.py`** que ejecute toda la secuencia
2. **Crear `verificar_despliegue.py`** con checklist automatizado
3. **Documentar orden de ejecución** en README con comandos exactos

### **Prioridad Media**:

4. **Agregar logging robusto** (módulo `logging` de Python)
5. **Implementar tests unitarios** para funciones críticas
6. **Crear script de rollback** ante fallos en procesamiento

### **Baja Prioridad**:

7. **Dashboard interactivo** (Streamlit/Dash) para visualizar corpus
8. **CI/CD pipeline** (GitHub Actions) para regeneración automática
9. **Containerización** (Docker) para reproducibilidad perfecta
