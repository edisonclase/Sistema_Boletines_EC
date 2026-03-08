import pandas as pd
from jinja2 import Environment, FileSystemLoader

def procesar_ciclo2(url, pdf_generator):
    df = pd.read_csv(url).fillna("")
    template = Environment(loader=FileSystemLoader('plantillas')).get_template('tecnica.html')
    
    for _, fila in df.iterrows():
        datos = fila.to_dict()
        # Aquí la lógica específica para incluir los 5 módulos técnicos
        pdf_generator.generar(datos, template, "SEGUNDO_CICLO")