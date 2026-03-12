# ROADMAP_SISTEMA_BOLETINES.md

## Proyecto
Sistema Automatizado de Boletines Académicos

**Responsable:** Edison Clase  
**Tecnologías principales:** Python, FastAPI, HTML, CSS, renderizado PDF  
**Objetivo general:** Automatizar la generación de boletines académicos oficiales, con posibilidad de escalar a una solución profesional para múltiples centros educativos.

---

## 1. Estado actual del proyecto

El sistema ya cuenta con una base funcional para generar boletines en PDF a partir de plantillas HTML y datos académicos.

### Ya logrado
- Generación de boletines en PDF.
- Uso de plantillas HTML/CSS.
- Integración de datos académicos.
- Avances importantes en diseño institucional del boletín.
- Trabajo previo en boletines de primer ciclo.
- Estructura backend con FastAPI.
- Proyecto documentado por etapas mediante reportes técnicos.

### Etapa actual prioritaria
La etapa actual más importante del proyecto es:

`app/pdf/templates/second_cycle_blocks_and_modules.html`

Esta plantilla corresponde al **boletín de segundo ciclo con bloques de competencias, módulos y RA (Resultados de Aprendizaje)**.

---

## 2. Prioridad actual de desarrollo

### Prioridad 1
Finalizar y estabilizar el boletín de segundo ciclo con:
- bloques de competencias
- módulos formativos
- resultados de aprendizaje (RA)

### Prioridad 2
Ajustar el diseño para lograr:
- mejor compactación visual
- uso óptimo del espacio
- posibilidad de mantener el boletín en una sola página cuando sea viable

### Prioridad 3
Corregir reglas visuales de notas vacías y coloración.

---

## 3. Reglas visuales pendientes del boletín

### 3.1. Notas con valor `0.0`
Cuando una nota tenga valor `0.0`, en el boletín debe:
- mostrarse en blanco
- no mostrarse como `0.0`

### 3.2. Regla de color amarillo
El color amarillo debe usarse solamente cuando:
- la nota visible sea menor de 70

No debe aplicarse amarillo si:
- el valor original es `0.0`
- la celda debe mostrarse en blanco

### Ejemplos esperados

| Valor original | Mostrar | Color |
|---|---|---|
| 85.0 | 85 | normal |
| 69.0 | 69 | amarillo |
| 0.0 | vacío | normal |

---

## 4. Boletines especiales y variantes

El proyecto contempla variantes de boletines, incluyendo una versión que muestre solamente:
- bloques de competencias
- módulos
- RA

Esto se relaciona directamente con el archivo:

`app/pdf/templates/second_cycle_blocks_and_modules.html`

Debe revisarse cuidadosamente para asegurar que esa plantilla refleje correctamente la lógica pedagógica y visual del segundo ciclo técnico-profesional.

---

## 5. Fuentes de datos y enlaces

Las fuentes de datos del proyecto deben quedar claramente identificadas y documentadas.

### Pendiente importante
Documentar:
- enlaces de base de datos
- rutas de archivos de origen
- fuentes externas activas
- conectores usados por el sistema
- archivos o endpoints donde se define el origen de los datos

### Nota
Durante la auditoría inicial del proyecto, se debe pedir a Codex que identifique:
- archivos vinculados a fuentes de datos
- rutas activas
- configuraciones heredadas
- nombres antiguos del proyecto
- referencias obsoletas

---

## 6. Roles del sistema

El sistema debe evolucionar hacia manejo de acceso por roles.

### Roles previstos
- **Director**
  - acceso completo
  - generación de reportes
  - supervisión general

- **Coordinador**
  - validación académica
  - revisión de reportes
  - supervisión de calificaciones

- **Digitador**
  - entrada de datos
  - carga o actualización de notas

### Pendiente
Diseñar y documentar:
- autenticación
- permisos por rol
- acceso diferenciado a módulos del sistema

---

## 7. Acceso en red local

El sistema debe poder ser utilizado por varios usuarios dentro del centro educativo a través de red local.

### Objetivo
Permitir acceso por cable / LAN para que coordinadores, digitadores u otros usuarios autorizados puedan entrar al sistema desde otras máquinas del centro.

### Pendientes
- configurar despliegue en red local
- definir IP o hostname de acceso interno
- evaluar seguridad y permisos
- validar sesiones multiusuario

---

## 8. Méritos académicos (meritorios)

El sistema debe poder generar reportes de meritorios para:
- período 1
- período 2
- año escolar completo

### Situación actual
Los módulos técnicos tienen una lógica de evaluación que complica su incorporación al cálculo de meritorios.

### Regla provisional actual
Por ahora, los meritorios se calculan solo con las asignaturas académicas.

### Pendientes
- documentar exactamente la fórmula actual
- crear módulo o reporte de meritorios por período
- crear módulo o reporte de meritorios anuales
- evaluar si conviene mantener separados:
  - meritorio académico
  - meritorio técnico

### Propuesta de mejora
Manejar dos reconocimientos:
- **Meritorio académico:** basado solo en asignaturas académicas
- **Meritorio técnico:** basado en módulos técnicos, con una lógica aparte

Eso permitiría reconocer ambos desempeños sin distorsionar el ranking general.

---

## 9. Limpieza estructural del proyecto

El proyecto fue renombrado y algunas carpetas fueron eliminadas manualmente, por lo que es posible que aún queden:
- archivos huérfanos
- carpetas obsoletas
- plantillas duplicadas
- assets no usados
- imports rotos
- nombres antiguos del proyecto

### Pendiente inmediato
Antes de seguir desarrollando, se debe realizar una auditoría técnica completa del repositorio para identificar qué sobra y qué debe conservarse.

### Regla importante
Codex debe:
- analizar
- reportar
- proponer

Pero **no debe borrar nada automáticamente**.  
La eliminación debe hacerla Edison manualmente, luego de revisar el reporte.

---

## 10. Reglas obligatorias para trabajar con IA

### Antes de cualquier cambio
La IA debe:
1. leer la documentación del proyecto
2. analizar antes de editar
3. explicar qué piensa cambiar
4. pedir autorización antes de modificar archivos

### Regla crítica
**Antes de realizar cambios, siempre recordar guardar en Git.**

Comandos obligatorios antes de modificar:

```bash
git status
git add .
git commit -m "checkpoint antes de cambios"
git push