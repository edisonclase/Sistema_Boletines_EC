import os
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno del archivo .env
load_dotenv()

class GeneradorBoletines:
    def __init__(self):
        # Extraer enlaces de forma segura
        self.url_primero = os.getenv("URL_PRIMER_CICLO")
        self.url_segundo = os.getenv("URL_SEGUNDO_CICLO")
        self.path_wkhtml = os.getenv("WKHTMLTOPDF_PATH")
        
        # Validar que los enlaces existan
        if not self.url_primero or not self.url_segundo:
            raise ValueError("Error: No se encontraron los enlaces en el archivo .env")

    def obtener_datos(self, ciclo="primero"):
        """Descarga los datos de Google Sheets según el ciclo especificado."""
        url = self.url_primero if ciclo == "primero" else self.url_segundo
        print(f"--- Cargando datos del {ciclo} ciclo ---")
        try:
            return pd.read_csv(url)
        except Exception as e:
            print(f"Error al conectar con Google Sheets: {e}")
            return None

    def ejecutar(self):
        # Ejemplo de prueba de carga
        df_primero = self.obtener_datos("primero")
        if df_primero is not None:
            print(f"Éxito: Se cargaron {len(df_primero)} registros del primer ciclo.")
            # Aquí imprimiremos los nombres para verificar
            print(df_primero[['NOMBRE_ESTUDIANTE', 'CURSO']].head())

if __name__ == "__main__":
    app = GeneradorBoletines()
    app.ejecutar()
