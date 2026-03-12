REPORTE TÉCNICO DE CONTINUIDAD

Sistema Automatizado de Boletines Académicos

Autor: Edison Clase
Proyecto: Sistema Automatizado de Boletines Académicos
Repositorio: Sistema_Boletines_EC
Lenguaje principal: Python
Framework: FastAPI
Renderizado de boletines: HTML + CSS → PDF (WeasyPrint)

1. Propósito del proyecto

El sistema tiene como objetivo automatizar la generación de boletines académicos oficiales para centros educativos.

Busca reemplazar procesos manuales realizados en:

Excel

Word

Sistemas administrativos aislados

El sistema permite generar:

boletines individuales

boletines por bloques de competencias

boletines masivos por curso (ZIP)

reportes académicos derivados

El proyecto está diseñado para evolucionar hacia una plataforma SaaS para centros educativos.

2. Arquitectura general del sistema

El sistema está basado en una arquitectura API utilizando FastAPI.

Flujo general:

Fuentes de datos (Google Sheets / CSV / futuro SQL)
        ↓
Transformación de datos
        ↓
Servicios académicos
        ↓
Renderizado HTML
        ↓
Conversión HTML → PDF
        ↓
Entrega de boletines

Componentes principales:

API FastAPI

servicios académicos

motor de generación de boletines

plantillas HTML

renderizador PDF (WeasyPrint)

3. Estructura actual del proyecto

Directorio principal:

Sistema_Boletines_EC
│
├── app
│   ├── api
│   │   └── routes
│   │
│   ├── services
│   │   ├── bulletin_service.py
│   │   ├── html_service.py
│   │   └── pdf_service.py
│   │
│   ├── data
│   │   └── transformers
│   │       └── student_profile.py
│   │
│   ├── pdf
│   │   ├── templates
│   │   └── assets
│   │
│   └── utils
│
├── docs
├── .env
├── .env.example
├── SYSTEM_OVERVIEW.md
├── ROADMAP_SISTEMA_BOLETINES.md
├── AI_GUIDELINES.md
4. Flujo actual de generación de boletines
Paso 1: carga de datos

Los datos académicos se obtienen desde enlaces CSV publicados en Google Sheets.

Estos enlaces están definidos en .env.

Paso 2: transformación de datos

Archivo clave:

app/data/transformers/student_profile.py

Funciones principales:

build_subjects()

build_modules()

Estas funciones convierten la fila del estudiante en estructuras utilizables por el sistema.

Paso 3: construcción del perfil del estudiante

Archivo:

app/services/bulletin_service.py

Función central:

build_student_result_from_row()

Esta función genera el objeto:

student

Estructura:

{
    id_estudiante
    nombre_estudiante
    curso
    subjects
    modules
    modules_with_ras
}
5. Estructura académica del sistema
Asignaturas académicas (bloques de competencias)

Cada asignatura contiene:

p1_c1 ... p1_c4
p2_c1 ... p2_c4
p3_c1 ... p3_c4
p4_c1 ... p4_c4
pc1 ... pc4
final
asistencia_pct
Módulos técnicos

Cada módulo contiene:

modulo
ra1 ... ra10
cf
situ_a

Después se enriquecen con:

situ_r
ras_visibles
6. Estado actual del sistema

El sistema ya permite:

✓ generar boletines completos
✓ generar boletines por bloques
✓ generar ZIP masivo por curso
✓ consultar boletines por estudiante

El sistema levanta correctamente en FastAPI.

7. Auditoría técnica realizada

Se ejecutó una auditoría completa usando Codex.

Resultados principales:

Archivos eliminados

Se eliminaron archivos legacy:

config.py

data_processor.py

template_engine.py

carpetas vacías de schemas y tests

Código legado detectado

Persisten archivos que deben revisarse o eliminarse:

main.py (CLI antiguo con conflicto HEAD)
modulos/ciclo1.py
modulos/ciclo2.py

Estos pertenecían al sistema anterior basado en CSV.

8. Plantilla crítica pendiente

Archivo:

app/pdf/templates/second_cycle_blocks_and_modules.html

Estado:

archivo vacío (0 bytes)

Este archivo es la etapa actual del desarrollo.

Debe mostrar:

bloques de competencias

módulos formativos

resultados de aprendizaje (RA)

Actualmente existe el helper:

render_second_cycle_blocks_and_modules()

Pero:

no hay endpoint que lo invoque

no hay plantilla HTML implementada

9. Reglas visuales pendientes

El sistema debe implementar:

Regla 1

Si una calificación es:

0.0

Debe mostrarse:

celda vacía
Regla 2

El color amarillo se aplica cuando:

nota < 70

Pero:

si la nota es 0.0 no debe resaltarse
10. Sistema de méritos académicos

El sistema debe generar reportes de:

meritorios período 1

meritorios período 2

meritorios del año escolar

Problema detectado:

Los módulos técnicos tienen lógica de evaluación distinta.

Decisión provisional:

Los meritorios se calculan solo con asignaturas académicas

Propuesta futura:

Separar en:

meritorio académico

meritorio técnico

11. Interfaz de usuario

Archivo principal:

app/api/routes/ui.py

La UI permite:

consulta por estudiante

generación masiva por curso

El branding fue actualizado a:

Sistema Automatizado de Boletines Académicos
12. Acceso futuro por roles

El sistema deberá soportar:

Director

Coordinador

Digitador

Pendiente:

autenticación

permisos

acceso multiusuario en red LAN

13. Reglas para uso de IA

Antes de modificar código:

leer

SYSTEM_OVERVIEW.md
ROADMAP_SISTEMA_BOLETINES.md
AI_GUIDELINES.md
REPORTE_TECNICO_CONTINUIDAD.md

analizar proyecto

explicar cambios

esperar autorización

Las IA no deben modificar código sin aprobación.

14. Protocolo obligatorio de Git

Antes de cualquier cambio:

git status
git add .
git commit -m "checkpoint antes de cambios"
git push

Después de cambios:

git status
git add .
git commit -m "implementacion o mejora"
git push
15. Próxima etapa del proyecto

Prioridad inmediata:

Completar:

second_cycle_blocks_and_modules.html

Pasos:

diseñar estructura HTML

iterar student.subjects

iterar student.modules_with_ras

aplicar reglas de visualización

conectar endpoint HTML/PDF

16. Visión futura del proyecto

Este sistema puede evolucionar hacia:

plataforma SaaS para centros educativos

dashboards académicos

estadísticas institucionales

automatización administrativa

integración con sistemas de admisión