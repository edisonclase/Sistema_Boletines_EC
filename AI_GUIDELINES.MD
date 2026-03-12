# AI_GUIDELINES.md

## Reglas obligatorias
- No modificar archivos sin mi aprobación previa.
- No borrar archivos ni carpetas automáticamente.
- Antes de cualquier cambio, recuérdame ejecutar:
  git status
  git add .
  git commit -m "checkpoint antes de cambios"
  git push
- Si detectas archivos, carpetas o plantillas sobrantes, primero repórtalos.
- Prioriza estabilidad del sistema.

## Contexto del proyecto
- Proyecto: sistema automatizado de boletines académicos.
- Stack principal: Python + FastAPI + HTML/CSS + generación de PDF.
- El proyecto fue renombrado y se eliminaron carpetas manualmente; es posible que existan archivos residuales.
- La etapa actual más importante está centrada en la plantilla:
  app/pdf/templates/second_cycle_blocks_and_modules.html

## Estado actual funcional
- Ya existe generación de boletines.
- Se trabaja el boletín de segundo ciclo con bloques de competencias, módulos y RA.
- Hay ajustes visuales pendientes para mantener el boletín compacto y, si es posible, en una sola página.

## Reglas visuales pendientes
- Si una calificación es 0.0, debe mostrarse vacía.
- Si una calificación es 0.0, no debe pintarse en amarillo.
- El amarillo aplica solo cuando la nota visible es menor de 70.

## Reglas de interacción
- Primero analizar.
- Luego proponer.
- Esperar aprobación.
- Después ejecutar.

## Auditoría inicial
En la primera fase debes:
1. Analizar la estructura completa del proyecto.
2. Detectar carpetas huérfanas, archivos no referenciados, plantillas viejas, assets no usados, imports rotos, rutas no conectadas y restos del nombre anterior del proyecto.
3. Entregarme un informe con evidencia.
4. No hacer cambios todavía.