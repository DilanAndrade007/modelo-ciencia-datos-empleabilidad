## Proyecto: Extracción de Ofertas de Empleo para Análisis de Habilidades Blandas

---

### 🎯 Objetivo

Este sistema permite la **extracción automatizada, trazable y escalable** de descripciones de ofertas laborales desde múltiples plataformas (iniciando con Jooble), clasificadas por **carrera universitaria** y preparadas para análisis posteriores de habilidades blandas mediante procesamiento de lenguaje natural (NLP).

---

### 📁 Estructura del Proyecto

```
soft_skills_scraper/
│
├── main.py
├── config/
│   └── platforms.yml                # Configuración de plataformas, API keys y términos por carrera
│
├── extractors/
│   ├── jooble_api.py               # Módulo específico para extracción desde Jooble API
│   └── rapidapi_api.py             # Módulo específico para extracción desde RapidApi API
│
├── utils/
│   └── file_manager.py             # Funciones auxiliares para manejo de logs, corpus y carpetas
│
├── logs/
│   ├── jooble_log.json             # Registro de estado por término de búsqueda y fecha
│   └── rapidapi_log.json           # Registro de estado por término de búsqueda y fecha
│
├── data/
│   └── outputs/
│       └── jooble/
│           ├── <Carrera>/
│           │   ├── jooble__<término>__<YYYY-MM-DD>.csv
│           │   └── corpus_unido/
│           │       └── jooble__<Carrera>__<YYYY-MM-DD>__merged.csv
│           rapidapi/
│           ├── <Carrera>/
│           │   ├── rapidapi__<término>__<YYYY-MM-DD>.csv
│           │   └── corpus_unido/
│           │       └── rapidapi__<Carrera>__<YYYY-MM-DD>__merged.csv
│           todas_las_plataformas/
│           └── <Carrera>/
│               ├── jooble__<Carrera>__<YYYY-MM-DD>__merged.csv
│               └── rapidapi__<Carrera>__<YYYY-MM-DD>__merged.csv
│                   
│
│
└── README.md
```
  pip install selenium beautifulsoup4 pandas 

---

### ⚙️ ¿Qué hace este sistema?

1. Lee términos de búsqueda por carrera desde `config/platforms.yml`.
2. Extrae resultados desde la API de Jooble, con paginación completa.
3. Verifica si el scraping ya se ejecutó hoy y pregunta si deseas repetirlo.
4. Reanuda automáticamente si una extracción fue interrumpida.
5. Evita duplicados mediante `job_id` inteligente.
6. Guarda los resultados organizados por plataforma y carrera.
7. Une automáticamente todos los `.csv` diarios por carrera en un único corpus consolidado en `corpus_unido/`.
8. Mantiene un registro histórico por plataforma, término y fecha.

---

### 🧪 Campos estándar del corpus generado

Cada fila del corpus `.csv` contiene:

| Campo                  | Descripción                                       |
| ---------------------- | ------------------------------------------------- |
| `job_id`               | Hash único (título + empresa + ubicación + fecha) |
| `source`               | Plataforma de origen (ej. `jooble`)               |
| `job_title`            | Título del empleo                                 |
| `company`              | Nombre de la empresa                              |
| `location`             | Ubicación geográfica                              |
| `description`          | Texto completo de la oferta                       |
| `skills`               | Skils recuperadas de la oferta                    |
| `careers_required`     | Carrera requerida en la oferta                    |
| `date_posted`          | Fecha de publicación                              |
| `url`                  | Enlace original a la oferta                       |
| `career_tag`           | Vacío (clasificación futura)                      |
| `soft_skills_detected` | Vacío (para análisis posterior)                   |
| `extraction_date`      | Fecha en que se realizó la extracción             |

---

### 🧭 Ejecución

```bash
python main.py
```

El sistema:

* Recorrerá todas las carreras y términos definidos para cada plataforma activa.
* Detectará si ya hiciste scraping hoy y te preguntará si deseas repetirlo.
* Guardará y unificará los resultados por carrera en `corpus_unido/`.

---

### 🧠 Control de extracción

El sistema mantiene un log estructurado por plataforma en `logs/<plataforma>_log.json`, por ejemplo:

```json
{
  "administración": {
    "last_extraction_date": "2025-06-11",
    "total_offers_extracted": 86,
    "last_page_extracted": 5
  }
}

---

### 🛠️ Configuración del archivo `platforms.yml`

```yaml
jooble:
  enabled: true
  api_key: "TU_API_KEY"
  carreras:
    Administración de Empresas:
      - administración
      - administrador
    Ingeniería Química:
      - Ingeniería Química
```

* Cada carrera puede tener múltiples términos de búsqueda.
* Todas las consultas se agrupan por carrera en la carpeta correspondiente.

---

### 🗂️ Consolidación de corpus entre plataformas

Además de guardar los corpus diarios por plataforma y carrera, el sistema genera una **copia adicional de cada corpus diario unificado** en una carpeta común para facilitar el análisis multifuente:

```
data/outputs/todas_las_plataformas/<Carrera>/jooble__<Carrera>__YYYY-MM-DD__merged.csv
```

---

### 📦 Corpus acumulado por carrera

El sistema también crea automáticamente un archivo **acumulado por carrera**, que incluye todos los corpus diarios históricos (de todas las fechas) ya unificados:

```
data/outputs/jooble/<Carrera>/corpus_unido/corpus__<Carrera>__acumulado.csv
```

Este archivo se actualiza en cada ejecución y elimina duplicados por `job_id`.

---

### Cambios

Se busca integrear coresignal como api para poder extraer datos desde linkedin
---