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
        opcion = input("¿Qué ciclo desea generar? (1: Primer Ciclo / 2: Segundo Ciclo): ")
        
        if opcion == "1":
            url = self.url_primero
            plantilla = 'academica.html'
            print("--- Procesando Primer Ciclo ---")
        else:
            url = self.url_segundo
            plantilla = 'tecnica.html'
            print("--- Procesando Segundo Ciclo ---")

        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        
        for _, fila in df.iterrows():
            self.generar_pdf_general(fila.to_dict(), plantilla)

if __name__ == "__main__":
    app = GeneradorBoletines()
    app.ejecutar()
