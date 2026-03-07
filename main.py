import os
import pdfkit
from modulos.ciclo1 import procesar_ciclo1
from modulos.ciclo2 import procesar_ciclo2
import config

class PDFGenerator:
    def __init__(self):
        self.config = pdfkit.configuration(wkhtmltopdf=os.getenv("WKHTMLTOPDF_PATH"))

    def generar(self, datos, template, carpeta):
        html = template.render(d=datos)
        nombre = f"{datos['NOMBRE_ESTUDIANTE']}.pdf"
        ruta = os.path.join("boletines", carpeta, nombre)
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        pdfkit.from_string(html, ruta, configuration=self.config)

def menu():
    gen = PDFGenerator()
    op = input("1. Ciclo 1, 2. Ciclo 2, 3. Consulta: ")
    if op == "1": procesar_ciclo1(os.getenv("URL_1"), gen)
    elif op == "2": procesar_ciclo2(os.getenv("URL_2"), gen)
    # ... resto del menú

if __name__ == "__main__":
    menu()
