# 🔄 DIAGRAMA DE FLUJO - COMPONENTE DE DESPLIEGUE

## Pipeline Completo de Procesamiento

```mermaid
graph TD
    A[📋 config/platforms.yml] --> B[🚀 main.py<br/>EXTRACCIÓN]
    B --> C[📊 data/outputs/plataforma/Carrera/]
    B --> D[📝 logs/plataforma_log.json]
    
    C --> E[🔧 file_manager.py<br/>1. unir_corpus_por_carrera]
    E --> F[🔧 file_manager.py<br/>2. copiar_corpus_diario_a_global]
    F --> G[🔧 file_manager.py<br/>3. unir_corpus_acumulado_por_carrera]
    
    G --> H[📄 Carrera_Merged.csv<br/>PRELIMINAR]
    
    H --> I[🌐 Traductor_Descripcion.py<br/>Genera: description_final]
    I --> J[🧹 Normalizador_Independiente.py<br/>Limpia: description_final]
    J --> K[🔤 Traductor_Skills.py<br/>Traduce: skills]
    K --> L[🎯 Extract_Habilidades.py<br/>Genera: EURACE_skills, initial_skills]
    L --> M[🗑️ Eliminar_Filas_Vacias.py<br/>Filtra: desc Y skills vacías]
    
    M --> N[✅ Carrera_Merged.csv<br/>FINAL]
    
    N --> O[📈 representations.py<br/>+ chart_generator.py]
    
    O --> P[📊 REPORTES]
    P --> Q[🖼️ 4 Gráficos PNG]
    P --> R[📋 9 Tablas CSV]
    P --> S[🗺️ mapa.html]
    P --> T[📄 ReporteQuarto.html]
    
    U[⚙️ config/skills.yml] --> L

    style B fill:#e1f5ff
    style G fill:#fff3cd
    style N fill:#d4edda
    style O fill:#f8d7da
    style P fill:#d1ecf1