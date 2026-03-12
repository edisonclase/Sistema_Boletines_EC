from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])


@router.get("/", response_class=HTMLResponse)
def home():
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>CLASE EducTech</title>
        <style>
            * {
                box-sizing: border-box;
            }

            :root {
                --bg: #f4f7fb;
                --panel: #ffffff;
                --panel-soft: #f8fbff;
                --text: #172033;
                --muted: #5f6b85;
                --primary: #1e3a8a;
                --primary-2: #2563eb;
                --accent: #0f172a;
                --line: #d8e2f0;
                --line-strong: #bfd1ea;
                --shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
                --radius: 18px;
            }

            body {
                margin: 0;
                font-family: Arial, Helvetica, sans-serif;
                background:
                    radial-gradient(circle at top left, #eaf2ff 0%, transparent 32%),
                    radial-gradient(circle at top right, #eef4ff 0%, transparent 28%),
                    var(--bg);
                color: var(--text);
            }

            .wrapper {
                min-height: 100vh;
                padding: 28px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .shell {
                width: 100%;
                max-width: 1320px;
            }

            .hero {
                text-align: center;
                margin-bottom: 22px;
            }

            .hero-badge {
                display: inline-block;
                padding: 7px 12px;
                border-radius: 999px;
                background: #e8f0ff;
                color: var(--primary);
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 0.3px;
                margin-bottom: 12px;
            }

            .hero-title {
                margin: 0;
                font-size: 38px;
                font-weight: 800;
                color: var(--accent);
            }

            .hero-subtitle {
                margin: 10px auto 0 auto;
                max-width: 860px;
                font-size: 16px;
                color: var(--muted);
                line-height: 1.55;
            }

            .grid {
                display: grid;
                grid-template-columns: 1.1fr 1fr;
                gap: 22px;
            }

            .card {
                background: var(--panel);
                border: 1px solid var(--line);
                border-radius: var(--radius);
                box-shadow: var(--shadow);
                padding: 24px;
            }

            .card-header {
                margin-bottom: 18px;
            }

            .card-kicker {
                font-size: 12px;
                font-weight: bold;
                color: var(--primary-2);
                text-transform: uppercase;
                letter-spacing: 0.6px;
                margin-bottom: 6px;
            }

            .card-title {
                margin: 0;
                font-size: 24px;
                color: var(--accent);
            }

            .card-subtitle {
                margin: 8px 0 0 0;
                color: var(--muted);
                font-size: 14px;
                line-height: 1.5;
            }

            .section {
                border: 1px solid var(--line);
                background: var(--panel-soft);
                border-radius: 14px;
                padding: 16px;
                margin-top: 18px;
            }

            .section-title {
                margin: 0 0 14px 0;
                font-size: 15px;
                font-weight: bold;
                color: var(--accent);
            }

            .subsection {
                margin-top: 16px;
                padding-top: 14px;
                border-top: 1px dashed var(--line-strong);
            }

            .subsection:first-of-type {
                margin-top: 8px;
                padding-top: 0;
                border-top: none;
            }

            .subsection-title {
                margin: 0 0 10px 0;
                font-size: 13px;
                font-weight: bold;
                color: var(--primary);
                text-transform: uppercase;
                letter-spacing: 0.4px;
            }

            .form-group {
                margin-bottom: 15px;
            }

            label {
                display: block;
                font-weight: bold;
                margin-bottom: 8px;
                font-size: 14px;
                color: var(--text);
            }

            select {
                width: 100%;
                padding: 13px 14px;
                border: 1px solid var(--line-strong);
                border-radius: 12px;
                font-size: 15px;
                outline: none;
                background: #fff;
                color: var(--text);
            }

            select:focus {
                border-color: var(--primary-2);
                box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12);
            }

            .buttons-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
                margin-top: 8px;
            }

            button {
                border: none;
                border-radius: 12px;
                padding: 15px 14px;
                font-size: 14px;
                font-weight: bold;
                cursor: pointer;
                transition: transform 0.08s ease, opacity 0.08s ease, box-shadow 0.12s ease;
                min-height: 58px;
                line-height: 1.2;
            }

            button:hover {
                opacity: 0.97;
                box-shadow: 0 10px 18px rgba(15, 23, 42, 0.08);
            }

            button:active {
                transform: scale(0.99);
            }

            button:disabled {
                opacity: 0.55;
                cursor: not-allowed;
                box-shadow: none;
            }

            .btn-primary {
                background: var(--primary);
                color: white;
            }

            .btn-secondary {
                background: var(--primary-2);
                color: white;
            }

            .btn-soft {
                background: #e8f0ff;
                color: var(--primary);
                border: 1px solid #c8d8fb;
            }

            .btn-dark {
                background: #0f172a;
                color: white;
            }

            .btn-success {
                background: #0f766e;
                color: white;
            }

            .btn-violet {
                background: #5b21b6;
                color: white;
            }

            .btn-outline {
                background: #ffffff;
                color: var(--accent);
                border: 1px solid var(--line-strong);
            }

            .help-box {
                margin-top: 18px;
                padding: 14px 15px;
                border-radius: 12px;
                background: #f9fbff;
                border: 1px solid var(--line);
                font-size: 13px;
                color: var(--muted);
                line-height: 1.6;
            }

            .help-box strong {
                color: var(--accent);
            }

            .status-box {
                margin-top: 14px;
                padding: 12px 14px;
                border-radius: 12px;
                background: #eef6ff;
                border: 1px solid #cfe0fb;
                font-size: 13px;
                color: #35517d;
                line-height: 1.5;
            }

            .footer {
                margin-top: 18px;
                text-align: center;
                font-size: 12px;
                color: var(--muted);
            }

            .footer strong {
                color: var(--accent);
            }

            @media (max-width: 1100px) {
                .grid {
                    grid-template-columns: 1fr;
                }
            }

            @media (max-width: 700px) {
                .wrapper {
                    padding: 16px;
                }

                .card {
                    padding: 18px;
                }

                .hero-title {
                    font-size: 30px;
                }

                .buttons-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="wrapper">
            <div class="shell">
                <div class="hero">
                    <div class="hero-badge">Plataforma de Seguimiento Académico.</div>
                    <h1 class="hero-title">CLASE EducTech</h1>
                    <p class="hero-subtitle">
                        Sistema de Generación de Boletines.
                    </p>
                </div>

                <div class="grid">
                    <div class="card">
                        <div class="card-header">
                            <div class="card-kicker">Modo individual</div>
                            <h2 class="card-title">Boletines por estudiante</h2>
                            <p class="card-subtitle">
                                Selecciona el ciclo, el curso y el estudiante.
                            </p>
                        </div>

                        <div class="section">
                            <h3 class="section-title">Consulta Individual</h3>

                            <div class="form-group">
                                <label for="studentCycle">Ciclo</label>
                                <select id="studentCycle" onchange="loadStudentCourses()">
                                    <option value="Primer_Ciclo">Primer Ciclo</option>
                                    <option value="Segundo_Ciclo">Segundo Ciclo</option>
                                </select>
                            </div>

                            <div class="form-group">
                                <label for="studentCourse">Curso</label>
                                <select id="studentCourse" onchange="loadStudents()">
                                    <option value="">Cargando cursos...</option>
                                </select>
                            </div>

                            <div class="form-group">
                                <label for="studentSelect">Estudiante</label>
                                <select id="studentSelect" onchange="updateStudentButtons()">
                                    <option value="">Selecciona un curso primero</option>
                                </select>
                            </div>

                            <div class="subsection">
                                <h4 class="subsection-title">Boletín general</h4>
                                <div class="buttons-grid">
                                    <button id="btnBulletinHtml" class="btn-primary" onclick="openStudentRoute('bulletin-html')" disabled>
                                        Ver boletín completo (HTML)
                                    </button>

                                    <button id="btnBulletinPdf" class="btn-secondary" onclick="openStudentRoute('bulletin-pdf')" disabled>
                                        Descargar boletín completo (PDF)
                                    </button>
                                </div>
                            </div>

                            <div class="subsection">
                                <h4 class="subsection-title">Boletín por bloques / módulos</h4>
                                <div class="buttons-grid">
                                    <button id="btnBlocksHtml" class="btn-soft" onclick="openCycleSpecificHtml()" disabled>
                                        Ver boletín por bloques (HTML)
                                    </button>

                                    <button id="btnBlocksPdf" class="btn-dark" onclick="openCycleSpecificPdf()" disabled>
                                        Descargar boletín por bloques (PDF)
                                    </button>

                                    <button id="btnModulesHtml" class="btn-success" onclick="openStudentRoute('modules-only-html')" disabled>
                                        Ver boletín de módulos (HTML)
                                    </button>

                                    <button id="btnModulesPdf" class="btn-violet" onclick="openStudentRoute('modules-only-pdf')" disabled>
                                        Descargar boletín de módulos (PDF)
                                    </button>
                                </div>
                            </div>
                        </div>

                        <div class="help-box" id="individualHelp">
                            <strong>Primer Ciclo:</strong> boletín completo y boletín por bloques.
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <div class="card-kicker">Modo masivo</div>
                            <h2 class="card-title">Boletines por curso</h2>
                            <p class="card-subtitle">
                                Genera un ZIP con todos los boletines del curso seleccionado.
                                La filosofía institucional se agrega una sola vez al ZIP.
                            </p>
                        </div>

                        <div class="section">
                            <h3 class="section-title">Generación masiva</h3>

                            <div class="form-group">
                                <label for="massiveCycle">Ciclo</label>
                                <select id="massiveCycle" onchange="loadMassiveCourses()">
                                    <option value="Primer_Ciclo">Primer Ciclo</option>
                                    <option value="Segundo_Ciclo">Segundo Ciclo</option>
                                </select>
                            </div>

                            <div class="form-group">
                                <label for="massiveCourse">Curso</label>
                                <select id="massiveCourse" onchange="updateMassiveButtons()">
                                    <option value="">Cargando cursos...</option>
                                </select>
                            </div>

                            <div class="buttons-grid">
                                <button id="btnZipComplete" class="btn-primary" onclick="openCompleteZip()" disabled>
                                    Descargar ZIP completo
                                </button>

                                <button id="btnZipBlocks" class="btn-outline" onclick="openBlocksZip()" disabled>
                                    Descargar ZIP por bloques
                                </button>

                                <button id="btnZipModules" class="btn-dark" onclick="openSecondCycleModulesZip()" disabled>
                                    Descargar ZIP solo módulos
                                </button>

                                <button id="btnZipBlocksModules" class="btn-violet" onclick="openSecondCycleBlocksAndModulesZip()" disabled>
                                    Descargar ZIP bloques + módulos
                                </button>
                            </div>

                            <div class="status-box" id="massiveStatus">
                                Cargando configuración del ciclo...
                            </div>
                        </div>

                        <div class="help-box">
                            <strong>Comportamiento por ciclo:</strong>
                            <br>• <strong>Primer Ciclo:</strong> ZIP completo + ZIP por bloques.
                            <br>• <strong>Segundo Ciclo:</strong> ZIP completo + ZIP solo módulos + ZIP bloques + módulos.
                        </div>
                    </div>
                </div>

                <div class="footer">
                    Panel inicial del proyecto · futura capa de acceso por <strong>roles</strong> pendiente
                </div>
            </div>
        </div>

        <script>
            let individualStudents = [];

            function openRoute(url) {
                window.open(url, "_blank");
            }

            function getSelectedStudentId() {
                const value = document.getElementById("studentSelect").value;
                if (!value) {
                    alert("Debes seleccionar un estudiante.");
                    throw new Error("Estudiante no seleccionado");
                }
                return encodeURIComponent(value);
            }

            function getIndividualCycle() {
                return document.getElementById("studentCycle").value;
            }

            function getIndividualCourse() {
                return document.getElementById("studentCourse").value;
            }

            function getMassiveCycle() {
                return document.getElementById("massiveCycle").value;
            }

            function getMassiveCourse() {
                return document.getElementById("massiveCourse").value;
            }

            async function fetchJson(url) {
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error("No se pudo cargar la información.");
                }
                return await response.json();
            }

            function setOptions(selectId, items, placeholder) {
                const select = document.getElementById(selectId);
                select.innerHTML = "";

                const firstOption = document.createElement("option");
                firstOption.value = "";
                firstOption.textContent = placeholder;
                select.appendChild(firstOption);

                for (const item of items) {
                    const option = document.createElement("option");
                    if (typeof item === "string") {
                        option.value = item;
                        option.textContent = item;
                    } else {
                        option.value = item.id_estudiante;
                        option.textContent = item.label;
                    }
                    select.appendChild(option);
                }
            }

            function setIndividualButtonsDisabled(disabled) {
                document.getElementById("btnBulletinHtml").disabled = disabled;
                document.getElementById("btnBulletinPdf").disabled = disabled;
                document.getElementById("btnBlocksHtml").disabled = disabled;
                document.getElementById("btnBlocksPdf").disabled = disabled;
                document.getElementById("btnModulesHtml").disabled = disabled;
                document.getElementById("btnModulesPdf").disabled = disabled;
            }

            function updateIndividualHelp() {
                const cycle = getIndividualCycle();
                const help = document.getElementById("individualHelp");

                if (cycle === "Primer_Ciclo") {
                    help.innerHTML = "<strong>Primer Ciclo:</strong> boletín completo y boletín por bloques.";
                } else {
                    help.innerHTML = "<strong>Segundo Ciclo:</strong> boletín completo, boletín de módulos y boletín por bloques + módulos.";
                }
            }

            async function loadStudentCourses() {
                const cycle = getIndividualCycle();
                setIndividualButtonsDisabled(true);
                setOptions("studentCourse", [], "Cargando cursos...");
                setOptions("studentSelect", [], "Selecciona un curso primero");
                updateIndividualHelp();

                try {
                    const data = await fetchJson(`/students/options/courses?cycle=${encodeURIComponent(cycle)}`);
                    setOptions("studentCourse", data.courses || [], "Selecciona un curso");
                } catch (error) {
                    setOptions("studentCourse", [], "No se pudieron cargar los cursos");
                }
            }

            async function loadStudents() {
                const cycle = getIndividualCycle();
                const course = getIndividualCourse();
                setIndividualButtonsDisabled(true);

                if (!course) {
                    setOptions("studentSelect", [], "Selecciona un curso primero");
                    return;
                }

                setOptions("studentSelect", [], "Cargando estudiantes...");

                try {
                    const data = await fetchJson(`/students/options/students?cycle=${encodeURIComponent(cycle)}&course=${encodeURIComponent(course)}`);
                    individualStudents = data.students || [];
                    setOptions("studentSelect", individualStudents, "Selecciona un estudiante");
                } catch (error) {
                    individualStudents = [];
                    setOptions("studentSelect", [], "No se pudieron cargar los estudiantes");
                }
            }

            function updateStudentButtons() {
                const cycle = getIndividualCycle();
                const studentId = document.getElementById("studentSelect").value;
                const disabled = !studentId;

                document.getElementById("btnBulletinHtml").disabled = disabled;
                document.getElementById("btnBulletinPdf").disabled = disabled;
                document.getElementById("btnBlocksHtml").disabled = disabled;
                document.getElementById("btnBlocksPdf").disabled = disabled;

                if (cycle === "Primer_Ciclo") {
                    document.getElementById("btnModulesHtml").disabled = true;
                    document.getElementById("btnModulesPdf").disabled = true;
                } else {
                    document.getElementById("btnModulesHtml").disabled = disabled;
                    document.getElementById("btnModulesPdf").disabled = disabled;
                }
            }

            function openStudentRoute(routeSuffix) {
                const studentId = getSelectedStudentId();
                openRoute(`/students/${studentId}/${routeSuffix}`);
            }

            function openCycleSpecificHtml() {
                const cycle = getIndividualCycle();
                if (cycle === "Primer_Ciclo") {
                    openStudentRoute("bulletin-blocks-html");
                } else {
                    openStudentRoute("second-cycle-blocks-html");
                }
            }

            function openCycleSpecificPdf() {
                const cycle = getIndividualCycle();
                if (cycle === "Primer_Ciclo") {
                    openStudentRoute("bulletin-blocks-pdf");
                } else {
                    openStudentRoute("second-cycle-blocks-pdf");
                }
            }

            async function loadMassiveCourses() {
                const cycle = getMassiveCycle();
                setOptions("massiveCourse", [], "Cargando cursos...");

                try {
                    const data = await fetchJson(`/students/options/courses?cycle=${encodeURIComponent(cycle)}`);
                    setOptions("massiveCourse", data.courses || [], "Selecciona un curso");
                } catch (error) {
                    setOptions("massiveCourse", [], "No se pudieron cargar los cursos");
                }

                updateMassiveButtons();
            }

            function updateMassiveButtons() {
                const cycle = getMassiveCycle();
                const course = getMassiveCourse();
                const hasCourse = !!course;

                document.getElementById("btnZipComplete").disabled = !hasCourse;
                document.getElementById("btnZipBlocks").disabled = !(hasCourse && cycle === "Primer_Ciclo");
                document.getElementById("btnZipModules").disabled = !(hasCourse && cycle === "Segundo_Ciclo");
                document.getElementById("btnZipBlocksModules").disabled = !(hasCourse && cycle === "Segundo_Ciclo");

                const status = document.getElementById("massiveStatus");
                if (cycle === "Primer_Ciclo") {
                    status.innerHTML = "Para <strong>Primer Ciclo</strong> están disponibles el ZIP completo y el ZIP por bloques.";
                } else {
                    status.innerHTML = "Para <strong>Segundo Ciclo</strong> están disponibles el ZIP completo, el ZIP solo módulos y el ZIP bloques + módulos.";
                }
            }

            function openCompleteZip() {
                const cycle = getMassiveCycle();
                const course = getMassiveCourse();

                if (!course) {
                    alert("Debes seleccionar un curso.");
                    return;
                }

                openRoute(`/students/course/${encodeURIComponent(cycle)}/${encodeURIComponent(course)}/bulletins-zip`);
            }

            function openBlocksZip() {
                const course = getMassiveCourse();

                if (!course) {
                    alert("Debes seleccionar un curso.");
                    return;
                }

                openRoute(`/students/course/Primer_Ciclo/${encodeURIComponent(course)}/bulletins-blocks-zip`);
            }

            function openSecondCycleModulesZip() {
                const course = getMassiveCourse();

                if (!course) {
                    alert("Debes seleccionar un curso.");
                    return;
                }

                openRoute(`/students/course/Segundo_Ciclo/${encodeURIComponent(course)}/bulletins-modules-zip`);
            }

            function openSecondCycleBlocksAndModulesZip() {
                const course = getMassiveCourse();

                if (!course) {
                    alert("Debes seleccionar un curso.");
                    return;
                }

                openRoute(`/students/course/Segundo_Ciclo/${encodeURIComponent(course)}/bulletins-blocks-and-modules-zip`);
            }

            async function initializeUI() {
                await loadStudentCourses();
                await loadMassiveCourses();
                updateStudentButtons();
                updateMassiveButtons();
            }

            initializeUI();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)