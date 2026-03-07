import os
import pandas as pd
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
import pdfkit

# Cargar configuración segura
load_dotenv()

class GeneradorBoletines:
    def __init__(self):
        self.url_segundo = os.getenv("URL_SEGUNDO_CICLO")
        self.wkhtml_path = os.getenv("WKHTMLTOPDF_PATH")
        
        # Configurar pdfkit
        self.pdf_config = pdfkit.configuration(wkhtmltopdf=self.wkhtml_path)
        
        # Configurar Jinja2 para las plantillas
        self.env = Environment(loader=FileSystemLoader('plantillas'))

    def generar_boletin_tecnico(self, datos_estudiante):
        """Renderiza el HTML y lo convierte a PDF."""
        template = self.env.get_template('tecnica.html')
        
        # Pasamos los datos como un diccionario 'd' para la lógica del HTML
        html_renderizado = template.render(d=datos_estudiante, **datos_estudiante)
        
        # Crear ruta de salida: boletines_generados/CURSO/NOMBRE.pdf
        curso = str(datos_estudiante['CURSO']).replace("/", "-")
        ruta_carpeta = os.path.join("boletines_generados", curso)
        os.makedirs(ruta_carpeta, exist_ok=True)
        
        archivo_salida = os.path.join(ruta_carpeta, f"{datos_estudiante['NOMBRE_ESTUDIANTE']}.pdf")
        
        options = {
            'page-size': 'Letter',
            'encoding': "UTF-8",
            'quiet': ''
        }
        
        try:
            pdfkit.from_string(html_renderizado, archivo_salida, configuration=self.pdf_config, options=options)
            return True
        except Exception as e:
            print(f"Error generando PDF para {datos_estudiante['NOMBRE_ESTUDIANTE']}: {e}")
            return False

    def ejecutar(self):
        print("--- Iniciando proceso de Segundo Ciclo ---")
        df = pd.read_csv(self.url_segundo)
        
        # Limpiar nombres de columnas por si acaso hay espacios
        df.columns = df.columns.str.strip()
        
        count = 0
        for _, fila in df.iterrows():
            datos = fila.to_dict()
            if self.generar_boletin_tecnico(datos):
                count += 1
                print(f"[{count}] Boletín creado: {datos['NOMBRE_ESTUDIANTE']}")

if __name__ == "__main__":
    app = GeneradorBoletines()
    app.ejecutar()
