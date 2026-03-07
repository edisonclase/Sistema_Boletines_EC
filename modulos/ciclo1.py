import pandas as pd
from jinja2 import Environment, FileSystemLoader

def procesar_ciclo1(url, pdf_generator):
    df = pd.read_csv(url).fillna("")
    template = Environment(loader=FileSystemLoader('plantillas')).get_template('academica.html')
    
    for _, fila in df.iterrows():
        datos = fila.to_dict()
        # Aquí la lógica de generación específica del Ciclo 1
        pdf_generator.generar(datos, template, "PRIMER_CICLO")