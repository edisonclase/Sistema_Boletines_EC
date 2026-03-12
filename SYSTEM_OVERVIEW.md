# SYSTEM_OVERVIEW.md

## Proyecto
Sistema Automatizado de Boletines Académicos

**Autor:** Edison Clase  
**Lenguaje principal:** Python  
**Framework:** FastAPI  
**Renderizado de boletines:** HTML + CSS → PDF  

Este documento describe la arquitectura general del sistema, sus componentes principales, el flujo de generación de boletines y las reglas académicas implementadas.

Este archivo debe ser leído por cualquier desarrollador o asistente de IA antes de modificar el código.

---

# 1. Propósito del sistema

El sistema tiene como objetivo automatizar la generación de boletines académicos oficiales para centros educativos.

Busca reemplazar procesos manuales realizados en:

- Excel
- Word
- Sistemas administrativos no integrados

El sistema debe permitir generar boletines académicos directamente desde datos estructurados.

---

# 2. Arquitectura general

El sistema está basado en una arquitectura de API utilizando FastAPI.

Flujo general:
