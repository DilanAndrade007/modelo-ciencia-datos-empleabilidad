import os
import pandas as pd

BASE_PATH = "../data/outputs/todas_las_plataformas"

def contar_filas_por_csv(base_path):
    registros = []

    for carrera in os.listdir(base_path):
        carrera_path = os.path.join(base_path, carrera)
        if not os.path.isdir(carrera_path):
            continue

        for file in os.listdir(carrera_path):
            if not file.endswith(".csv"):
                continue

            archivo_path = os.path.join(carrera_path, file)
            plataforma = file.split("__")[0]

            try:
                df = pd.read_csv(archivo_path)
                num_filas = len(df)
                registros.append({
                    "Carrera": carrera,
                    "Plataforma": plataforma,
                    "Archivo": file,
                    "Filas": num_filas
                })
            except Exception as e:
                registros.append({
                    "Carrera": carrera,
                    "Plataforma": plataforma,
                    "Archivo": file,
                    "Filas": f"Error: {e}"
                })

    return pd.DataFrame(registros)

if __name__ == "__main__":
    df_resultado = contar_filas_por_csv(BASE_PATH)
    print("\n Resultado:")
    print(df_resultado.to_string(index=False))
