# AULA NOVA ACADEMIC CORE

## Documento de Arquitectura Inicial

**Versión:** 1.0
**Estado:** Borrador arquitectónico inicial
**Proyecto:** Aula Nova
**Módulo:** Academic Core
**Propósito:** Definir la arquitectura base para la evolución académica integral de Aula Nova.

---

# 1. Visión General

**Aula Nova Academic Core** será el núcleo académico de Aula Nova.

No se construirá como un sistema independiente, sino como una evolución natural de la plataforma existente, respetando todos los módulos que ya funcionan.

El objetivo principal es que toda la información académica nazca dentro de Aula Nova y pueda alimentar automáticamente:

* Registro Digital de Grado.
* Boletines.
* Academic Tracking.
* Reportes.
* Completivo.
* Extraordinario.
* Especial.
* Meritorios.
* Estadísticas.
* Constancias.
* Certificaciones.
* Consulta estudiantil.
* Portal de padres y estudiantes en el futuro.
* Registro oficial en PDF.

PostgreSQL será la fuente oficial de datos. Excel y Google Sheets podrán utilizarse solo como mecanismos de importación, exportación, respaldo o transición.

---

# 2. Principio Rector

La regla principal del proyecto es:

> No romper ninguna funcionalidad existente de Aula Nova.

Antes de modificar archivos ya existentes, se deberá:

1. Analizar el impacto.
2. Identificar riesgos.
3. Buscar primero una solución por extensión.
4. Documentar la razón del cambio.
5. Aplicar la modificación solo si es estrictamente necesaria.

---

# 3. Alcance del Módulo

Academic Core deberá contemplar todo lo que aparece en los registros oficiales de grado:

* Datos del centro educativo.
* Datos del estudiante.
* Datos de emergencia.
* Parentesco.
* Asistencia.
* Puntualidad.
* Asignaturas.
* Módulos formativos.
* Docentes asignados.
* Calificaciones por período.
* Recuperación pedagógica.
* Completivo.
* Extraordinario.
* Especial.
* Especificaciones curriculares.
* Evaluación de aprendizajes.
* Calificaciones de rendimiento.
* Promoción del grado.
* Acta final.
* Registro de experiencias.
* Registro de acompañamiento pedagógico.
* Práctica pedagógica.
* Estadísticas finales.
* Firma y validación.

---

# 4. Arquitectura General

La plataforma se organizará en capas:

```text
Aula Nova
│
├── Core existente
│   ├── Centros
│   ├── Usuarios
│   ├── Roles
│   ├── Dashboard
│   └── Módulos aprobados
│
├── Academic Core
│   ├── Gestión académica multicentro
│   ├── Registro digital
│   ├── Motor de reglas académicas
│   ├── Publicación de calificaciones
│   ├── Asistencia
│   ├── Validaciones
│   ├── Auditoría
│   ├── Boletines desde PostgreSQL
│   └── Registro PDF
│
├── Reportes
├── Boletines
├── Comunicaciones
├── Nova ID
├── Consulta estudiantil
└── Futuros portales
```

---

# 5. Modelo Multicentro

El sistema será estrictamente multicentro.

Cada entidad académica deberá estar asociada directa o indirectamente a un `center_id`.

Ningún usuario podrá acceder a datos de un centro al que no pertenezca.

La unidad académica principal será:

```text
Centro + Año Escolar + Grado + Sección
```

Ejemplo:

```text
CEJOMA + 2026-2027 + Segundo Grado + Sección A
CEJOMA + 2026-2027 + Segundo Grado + Sección B
CEJOMA + 2026-2027 + Segundo Grado + Sección C
```

Cada combinación representa un registro oficial independiente.

---

# 6. Estructura Académica

La jerarquía base será:

```text
Centro
└── Año Escolar
    └── Grado
        └── Sección
            ├── Estudiantes
            ├── Docente Encargado
            ├── Asignaturas
            │   └── Profesor asignado
            ├── Módulos Formativos
            │   └── Profesor asignado
            ├── Asistencia
            ├── Calificaciones
            ├── Observaciones
            ├── Validaciones
            └── Registro PDF
```

Una misma asignatura puede existir en varias secciones con profesores diferentes.

Ejemplo:

```text
Segundo A - Matemática - Profesor 1
Segundo B - Matemática - Profesor 2
Segundo C - Matemática - Profesor 1
```

Por eso se requiere una tabla intermedia tipo:

```text
section_subjects
```

Y para módulos técnicos:

```text
section_modules
```

---

# 7. Roles Iniciales

El sistema deberá contemplar, como mínimo:

* Super Administrador.
* Administrador del Centro.
* Registro y Control Académico.
* Dirección.
* Coordinación.
* Orientación.
* Psicología.
* Secretaría.
* Docente Encargado.
* Profesor de Asignatura.
* Profesor de Módulo.
* Consulta.
* Padre, futuro.
* Estudiante, futuro.

---

# 8. Autenticación y Acceso

Actualmente los docentes utilizan cuentas personales.

Por tanto, el sistema no dependerá de Google Workspace.

La autenticación deberá manejarse internamente desde Aula Nova, permitiendo:

* Usuarios con correo personal.
* Invitación o creación controlada.
* Vinculación obligatoria a centro educativo.
* Roles por centro.
* Estado activo/inactivo.
* Posibilidad futura de autenticación con Google.

---

# 9. Seguridad

El proyecto debe seguir estándares internacionales, tomando como referencia:

* OWASP ASVS.
* OWASP Top 10.
* Buenas prácticas de seguridad web.

Medidas mínimas:

* Autenticación segura.
* Contraseñas cifradas.
* Autorización por roles.
* Separación estricta por centro.
* Protección CSRF.
* Protección XSS.
* Protección contra inyección SQL.
* Validación de entradas.
* Rate limiting.
* Auditoría completa.
* Logs seguros.
* Backups automáticos.
* Sesiones seguras.
* Control de permisos por acción.
* No exponer información sensible en URLs.
* No guardar contraseñas en texto plano.
* Manejo seguro de archivos PDF y adjuntos.

---

# 10. Cierre y Reapertura de Períodos

Registro y Control Académico será el rol responsable de:

* Abrir períodos.
* Cerrar períodos.
* Reabrir períodos.
* Validar publicaciones.
* Autorizar correcciones.
* Firmar cierres.

Los docentes solamente podrán editar mientras el período esté abierto.

Los períodos contemplados serán:

* P1.
* P2.
* P3.
* P4.
* Recuperación Pedagógica.
* Completivo.
* Extraordinario.
* Especial.
* Asistencia.

---

# 11. Auditoría

Toda acción importante deberá dejar rastro.

La auditoría debe registrar:

* Usuario.
* Centro.
* Rol.
* Fecha.
* Hora.
* IP.
* Acción realizada.
* Entidad afectada.
* Valor anterior.
* Valor nuevo.
* Motivo.
* Estado anterior.
* Estado nuevo.
* Firma o confirmación digital cuando aplique.

No se debe eliminar historial.

---

# 12. Firma y Constancia de Validación

Las acciones académicas importantes deberán generar evidencia formal.

Ejemplos:

* Publicación de calificaciones.
* Cierre de período.
* Reapertura.
* Validación de recuperación pedagógica.
* Validación de completivo.
* Validación de extraordinario.
* Validación de especial.
* Generación de registro PDF.
* Generación de boletín final.

Cada constancia deberá tener:

* Código único.
* Centro.
* Año escolar.
* Grado.
* Sección.
* Usuario responsable.
* Rol.
* Fecha.
* Hora.
* Acción.
* Firma digital interna.
* Estado.

---

# 13. Motor de Reglas Académicas

El sistema deberá tener un motor centralizado de reglas académicas.

Este motor determinará:

* Promoción.
* Reprobación.
* Recuperación pedagógica.
* Completivo.
* Extraordinario.
* Especial.
* Meritorios.
* Estadísticas.
* Estado final del estudiante.
* Aprobación de módulos.
* Decisiones por asistencia.
* Generación de constancias.
* Validación de boletines.
* Cierre académico.

Las reglas no deberán estar dispersas en múltiples archivos.

---

# 14. Gestión de Calificaciones

Los docentes podrán registrar calificaciones según sus asignaciones.

El sistema validará que:

* El docente tenga permiso sobre esa sección.
* El período esté abierto.
* El estudiante pertenezca a esa sección.
* La asignatura o módulo esté asignado a esa sección.
* La calificación esté dentro del rango permitido.
* No se modifiquen registros cerrados sin autorización.

---

# 15. Asistencia

El módulo debe contemplar asistencia y puntualidad.

Debe permitir registrar:

* Presente.
* Ausente.
* Tardanza.
* Excusa.
* Retiro.
* Días trabajados.
* Totales.
* Porcentajes.
* Alertas por baja asistencia.

La asistencia debe alimentar:

* Registro PDF.
* Boletines.
* Decisiones académicas.
* Reportes.
* Estadísticas finales.

---

# 16. Especificaciones Curriculares y Textos Pedagógicos

Los docentes podrán escribir textos relacionados con:

* Especificaciones curriculares.
* Observaciones.
* Experiencias.
* Prácticas pedagógicas.
* Acompañamiento pedagógico.

El sistema podrá asistir con IA para:

* Corregir ortografía.
* Corregir gramática.
* Mejorar redacción.
* Mantener tono institucional.
* Evitar repeticiones.
* Sugerir versiones más claras.
* Adaptar el texto al espacio disponible del PDF.

Flujo sugerido:

```text
Borrador del docente
→ Corrección sugerida
→ Revisión del docente
→ Versión aprobada
→ Impresión en PDF
```

---

# 17. Registro PDF

El PDF no debe ser una tabla simple.

Debe reproducir el libro oficial del registro de grado según corresponda:

* Primer ciclo.
* Segundo ciclo académico.
* Segundo ciclo técnico profesional.

El PDF deberá generarse por sección.

Ejemplo:

```text
Registro_2026_2027_CEJOMA_2A.pdf
Registro_2026_2027_CEJOMA_2B.pdf
Registro_2026_2027_CEJOMA_2C.pdf
```

Debe respetar:

* Tamaño del registro.
* Distribución visual.
* Encabezados.
* Tablas.
* Paginación.
* Secciones.
* Espacios de firma.
* Textos ajustados.
* Datos oficiales.

---

# 18. Boletines

El módulo de boletines existente no debe romperse.

Durante la transición, deben coexistir dos fuentes de datos:

```text
1. Excel / hojas de cálculo
2. PostgreSQL / Academic Core
```

Cuando Academic Core esté validado, PostgreSQL será la fuente principal.

Excel quedará como respaldo, importación o exportación.

---

# 19. Integración con Módulos Existentes

Academic Core deberá integrarse sin romper:

* Dashboard.
* Academic Tracking.
* Boletines automáticos.
* Reportes.
* Comunicaciones.
* Nova ID.
* QR.
* Carnets.
* Consulta estudiantil futura.
* Otros módulos existentes.

Toda integración debe realizarse con bajo acoplamiento.

---

# 20. Tecnologías

Tecnologías principales:

* Python.
* FastAPI.
* PostgreSQL.
* SQLAlchemy.
* Alembic.
* Pydantic.
* Jinja2.
* HTML5.
* CSS3.
* JavaScript.
* JSON.
* WeasyPrint o Playwright para PDF.
* Google Cloud.
* Git.
* GitHub.

---

# 21. Despliegue

La plataforma debe estar preparada para operar en la nube.

Ruta recomendada:

```text
Desarrollo local
→ GitHub
→ Google Cloud Run
→ Cloud SQL PostgreSQL
→ Cloud Storage
→ Backups automáticos
→ Dominio propio
→ HTTPS
```

No se recomienda depender de una computadora local del centro educativo para producción.

---

# 22. Base de Datos Inicial Propuesta

Tablas conceptuales iniciales:

```text
centers
school_years
users
roles
user_center_roles
teachers
students
guardians
grades
sections
grade_sections
enrollments
subjects
modules
section_subjects
section_modules
academic_periods
period_statuses
attendance_records
grade_entries
recovery_entries
completive_entries
extraordinary_entries
special_entries
curricular_specifications
pedagogical_experiences
pedagogical_practices
validation_records
digital_signatures
audit_logs
pdf_generation_logs
academic_rule_versions
```

---

# 23. Principios de Código

Todo código deberá ser:

* Claro.
* Tipado.
* Modular.
* Documentado.
* Probado.
* Mantenible.
* Escalable.
* Seguro.

Debe evitarse:

* Código duplicado.
* Lógica académica dispersa.
* Consultas SQL inseguras.
* Acoplamiento innecesario.
* Mezclar presentación con lógica de negocio.
* Modificar archivos existentes sin justificación.

---

# 24. Estructura Sugerida de Carpetas

```text
app/
│
├── core/
│   ├── config.py
│   ├── security.py
│   ├── permissions.py
│   └── database.py
│
├── academic_core/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── repositories/
│   ├── rules/
│   ├── routers/
│   ├── templates/
│   ├── pdf/
│   ├── audit/
│   └── tests/
│
├── existing_modules/
│
└── main.py
```

La estructura final deberá adaptarse al proyecto real existente de Aula Nova.

---

# 25. Pruebas

Cada fase deberá incluir pruebas.

Tipos recomendados:

* Pruebas unitarias.
* Pruebas de servicios.
* Pruebas de reglas académicas.
* Pruebas de permisos.
* Pruebas de integración.
* Pruebas de generación PDF.
* Pruebas de seguridad básicas.

No avanzar si las pruebas críticas fallan.

---

# 26. Git

Cada etapa deberá finalizar con:

```bash
git status
git add .
git commit -m "mensaje profesional"
git push
```

Los commits deben ser claros y representar avances cerrados.

Ejemplos:

```bash
git commit -m "Add Academic Core initial architecture"
git commit -m "Add multicenter academic data model"
git commit -m "Add period closure workflow"
git commit -m "Add academic audit logging"
```

---

# 27. Fases de Desarrollo

## Fase 0: Arquitectura

* Crear `ARCHITECTURE.md`.
* Revisar módulos existentes.
* Definir impacto.
* Definir estructura de carpetas.
* Definir modelo inicial.

## Fase 1: Modelo Multicentro

* Centros.
* Años escolares.
* Grados.
* Secciones.
* Unidad del registro.
* Separación por centro.

## Fase 2: Usuarios, Roles y Permisos

* Roles.
* Permisos.
* Usuarios por centro.
* Profesores asignados.
* Acceso restringido.

## Fase 3: Estructura Académica

* Asignaturas.
* Módulos.
* Secciones.
* Docentes por asignatura.
* Docentes por módulo.
* Matrícula de estudiantes.

## Fase 4: Períodos y Cierres

* Apertura.
* Cierre.
* Reapertura.
* Validación.
* Historial.

## Fase 5: Publicación Docente

* Asistencia.
* Calificaciones.
* Recuperación pedagógica.
* Completivo.
* Extraordinario.
* Especial.

## Fase 6: Motor Académico

* Promoción.
* Reprobación.
* Meritorios.
* Estadísticas.
* Estados finales.

## Fase 7: Boletines desde PostgreSQL

* Integrar con boletines existentes.
* Mantener Excel como respaldo.
* Validar resultados.

## Fase 8: Registro PDF

* Plantillas.
* Diseño.
* Datos.
* Pruebas.
* Generación por sección.

## Fase 9: Auditoría y Firmas

* Logs.
* Constancias.
* Firmas.
* Validaciones.

## Fase 10: Despliegue

* Google Cloud.
* Cloud SQL.
* Cloud Run.
* Backups.
* Seguridad.
* Monitoreo.

---

# 28. Criterios de Aceptación

Una fase se considera terminada cuando:

* No rompe módulos existentes.
* Cumple su objetivo.
* Tiene pruebas básicas.
* Está documentada.
* Fue validada.
* Tiene commit.
* Tiene instrucciones de uso.
* Tiene rollback posible si aplica.

---

# 29. Decisiones Pendientes

Antes de iniciar código se deben confirmar:

* Estructura real actual de Aula Nova.
* Base de datos actual.
* Módulos existentes.
* Rutas existentes.
* Modelos existentes.
* Sistema actual de autenticación.
* Sistema actual de roles.
* Estrategia de migración desde Excel.
* Estructura de boletines actuales.
* Motor actual de Academic Tracking.
* Forma actual de generación PDF.
* Despliegue actual.

---

# 30. Conclusión

Aula Nova Academic Core será el corazón académico de Aula Nova.

Su propósito no es solamente digitalizar el registro.

Su propósito es crear una fuente única, segura, multicentro y profesional para toda la información académica.

Desde Academic Core deberán generarse todos los documentos, reportes y decisiones académicas del sistema.

La prioridad será siempre:

1. Seguridad.
2. Calidad.
3. Mantenibilidad.
4. Escalabilidad.
5. Compatibilidad con Aula Nova existente.
6. Experiencia de usuario.
7. Cumplimiento académico.
