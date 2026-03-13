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
        <link rel="icon" type="image/svg+xml" href='data:image/svg+xml;utf8,
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <defs>
                <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stop-color="%236366F1"/>
                    <stop offset="100%" stop-color="%23818CF8"/>
                </linearGradient>
            </defs>
            <rect x="4" y="4" width="56" height="56" rx="14" fill="url(%23g)"/>
            <text x="50%" y="54%" text-anchor="middle" font-family="Arial, Helvetica, sans-serif"
                  font-size="24" font-weight="700" fill="white">CE</text>
        </svg>' />
        <style>
            * {
                box-sizing: border-box;
            }

            :root {
                --bg: #F1F5F9;
                --panel: #FFFFFF;
                --panel-soft: #F8FAFF;
                --text: #1E293B;
                --muted: #64748B;
                --primary: #6366F1;
                --primary-2: #818CF8;
                --hover: #4F46E5;
                --accent: #0F172A;
                --line: #D9E2F1;
                --line-strong: #C7D2FE;
                --shadow: 0 18px 45px rgba(79, 70, 229, 0.12);
                --radius: 20px;
                --success-bg: rgba(15, 118, 110, 0.10);
                --success-border: rgba(15, 118, 110, 0.25);
                --success-text: #0F766E;
            }

            body {
                margin: 0;
                font-family: Arial, Helvetica, sans-serif;
                background:
                    radial-gradient(circle at top left, rgba(99, 102, 241, 0.16) 0%, transparent 32%),
                    radial-gradient(circle at top right, rgba(129, 140, 248, 0.16) 0%, transparent 28%),
                    linear-gradient(180deg, #F8FAFC 0%, var(--bg) 100%);
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
                margin-bottom: 24px;
            }

            .hero-badge {
                display: inline-block;
                padding: 8px 14px;
                border-radius: 999px;
                background: rgba(99, 102, 241, 0.12);
                color: var(--hover);
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 0.3px;
                margin-bottom: 14px;
                border: 1px solid rgba(99, 102, 241, 0.20);
            }

            .hero-title {
                margin: 0;
                font-size: 40px;
                font-weight: 800;
                color: var(--accent);
                letter-spacing: -0.5px;
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
                gap: 24px;
            }

            .card {
                background: var(--panel);
                border: 1px solid var(--line);
                border-radius: var(--radius);
                box-shadow: var(--shadow);
                padding: 26px;
            }

            .card-header {
                margin-bottom: 18px;
            }

            .card-kicker {
                font-size: 12px;
                font-weight: bold;
                color: var(--hover);
                text-transform: uppercase;
                letter-spacing: 0.7px;
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
                border-radius: 16px;
                padding: 18px;
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
                border: 1px solid #CBD5E1;
                border-radius: 12px;
                font-size: 15px;
                outline: none;
                background: #FFFFFF;
                color: var(--text);
                transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.08s ease;
            }

            select:focus {
                border-color: var(--primary);
                box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.14);
            }

            .buttons-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
                margin-top: 8px;
            }

            button {
                border: none;
                border-radius: 14px;
                padding: 15px 14px;
                font-size: 14px;
                font-weight: bold;
                cursor: pointer;
                transition: transform 0.08s ease, opacity 0.08s ease, box-shadow 0.12s ease, background 0.12s ease;
                min-height: 58px;
                line-height: 1.2;
            }

            button:hover {
                opacity: 0.99;
                box-shadow: 0 12px 22px rgba(79, 70, 229, 0.16);
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

            .btn-primary:hover {
                background: var(--hover);
            }

            .btn-secondary {
                background: var(--primary-2);
                color: white;
            }

            .btn-secondary:hover {
                background: #6D78F7;
            }

            .btn-soft {
                background: rgba(99, 102, 241, 0.10);
                color: var(--hover);
                border: 1px solid rgba(99, 102, 241, 0.22);
            }

            .btn-soft:hover {
                background: rgba(99, 102, 241, 0.16);
            }

            .btn-dark {
                background: #1E293B;
                color: white;
            }

            .btn-dark:hover {
                background: #0F172A;
            }

            .btn-success {
                background: #0F766E;
                color: white;
            }

            .btn-success:hover {
                background: #0B5E58;
            }

            .btn-violet {
                background: #7C3AED;
                color: white;
            }

            .btn-violet:hover {
                background: #6D28D9;
            }

            .btn-outline {
                background: #FFFFFF;
                color: var(--accent);
                border: 1px solid #CBD5E1;
            }

            .btn-outline:hover {
                background: #F8FAFC;
            }

            .help-box {
                margin-top: 18px;
                padding: 14px 15px;
                border-radius: 14px;
                background: #F8FAFC;
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
                border-radius: 14px;
                background: rgba(99, 102, 241, 0.10);
                border: 1px solid rgba(99, 102, 241, 0.18);
                font-size: 13px;
                color: var(--hover);
                line-height: 1.5;
                transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
            }

            .status-box.success {
                background: var(--success-bg);
                border-color: var(--success-border);
                color: var(--success-text);
            }

            .last-query-box {
                margin-top: 18px;
                padding: 16px;
                border-radius: 16px;
                background: #FFFFFF;
                border: 1px solid var(--line);
                box-shadow: 0 10px 24px rgba(79, 70, 229, 0.08);
                display: none;
            }

            .last-query-title {
                margin: 0 0 10px 0;
                font-size: 14px;
                font-weight: bold;
                color: var(--accent);
            }

            .last-query-meta {
                margin: 4px 0;
                font-size: 14px;
                color: var(--muted);
            }

            .last-query-meta strong {
                color: var(--text);
            }

            .last-query-actions {
                margin-top: 14px;
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
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

                .buttons-grid,
                .last-query-actions {
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
                                    <option value="">Seleccione un ciclo</option>
                                    <option value="Primer_Ciclo">Primer Ciclo</option>
                                    <option value="Segundo_Ciclo">Segundo Ciclo</option>
                                </select>
                            </div>

                            <div class="form-group">
                                <label for="studentCourse">Curso</label>
                                <select id="studentCourse" onchange="loadStudents()">
                                    <option value="">Seleccione un ciclo primero</option>
                                </select>
                            </div>

                            <div class="form-group">
                                <label for="studentSelect">Estudiante</label>
                                <select id="studentSelect" onchange="updateStudentButtons()">
                                    <option value="">Seleccione un curso primero</option>
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
                            <strong>Selecciona un ciclo:</strong> luego podrás elegir el curso y el estudiante.
                        </div>

                        <div class="last-query-box" id="lastQueryBox">
                            <h4 class="last-query-title">Última consulta realizada</h4>
                            <p class="last-query-meta"><strong>Ciclo:</strong> <span id="lastQueryCycle">-</span></p>
                            <p class="last-query-meta"><strong>Curso:</strong> <span id="lastQueryCourse">-</span></p>
                            <p class="last-query-meta"><strong>Estudiante:</strong> <span id="lastQueryStudent">-</span></p>

                            <div class="last-query-actions">
                                <button id="btnRepeatLastQuery" class="btn-primary" onclick="repeatLastQuery()">
                                    Abrir nuevamente
                                </button>
                                <button class="btn-outline" onclick="clearLastQuery()">
                                    Limpiar última consulta
                                </button>
                            </div>
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
                                    <option value="">Seleccione un ciclo</option>
                                    <option value="Primer_Ciclo">Primer Ciclo</option>
                                    <option value="Segundo_Ciclo">Segundo Ciclo</option>
                                </select>
                            </div>

                            <div class="form-group">
                                <label for="massiveCourse">Curso</label>
                                <select id="massiveCourse" onchange="updateMassiveButtons()">
                                    <option value="">Seleccione un ciclo primero</option>
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
                                Selecciona un ciclo para continuar.
                            </div>
                        </div>

                        <div class="help-box">
                            <strong>Comportamiento por ciclo:</strong>
                            <br>• <strong>Primer Ciclo:</strong> ZIP completo + ZIP por bloques.
                            <br>• <strong>Segundo Ciclo:</strong> ZIP completo + ZIP solo módulos + ZIP bloques + módulos.
                        </div>

                        <div class="last-query-box" id="lastMassiveQueryBox">
                            <h4 class="last-query-title">Última generación masiva</h4>
                            <p class="last-query-meta"><strong>Ciclo:</strong> <span id="lastMassiveCycle">-</span></p>
                            <p class="last-query-meta"><strong>Curso:</strong> <span id="lastMassiveCourse">-</span></p>
                            <p class="last-query-meta"><strong>Tipo:</strong> <span id="lastMassiveType">-</span></p>

                            <div class="last-query-actions">
                                <button id="btnRepeatLastMassiveQuery" class="btn-primary" onclick="repeatLastMassiveQuery()">
                                    Abrir nuevamente
                                </button>
                                <button class="btn-outline" onclick="clearLastMassiveQuery()">
                                    Limpiar última generación
                                </button>
                            </div>
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
            let lastIndividualQuery = null;
            let lastMassiveQuery = null;

            const STORAGE_KEYS = {
                lastIndividualQuery: "clase_edutech_last_individual_query",
                lastMassiveQuery: "clase_edutech_last_massive_query"
            };

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

            function getCycleLabel(cycle) {
                if (cycle === "Primer_Ciclo") return "Primer Ciclo";
                if (cycle === "Segundo_Ciclo") return "Segundo Ciclo";
                return cycle || "-";
            }

            function getSelectedStudentLabel() {
                const select = document.getElementById("studentSelect");
                if (!select.value) {
                    return "";
                }
                return select.options[select.selectedIndex]?.textContent || "";
            }

            function persistToStorage(key, value) {
                try {
                    localStorage.setItem(key, JSON.stringify(value));
                } catch (error) {
                    console.warn("No se pudo guardar en localStorage:", error);
                }
            }

            function loadFromStorage(key) {
                try {
                    const raw = localStorage.getItem(key);
                    if (!raw) {
                        return null;
                    }
                    return JSON.parse(raw);
                } catch (error) {
                    console.warn("No se pudo leer desde localStorage:", error);
                    return null;
                }
            }

            function removeFromStorage(key) {
                try {
                    localStorage.removeItem(key);
                } catch (error) {
                    console.warn("No se pudo limpiar localStorage:", error);
                }
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

            function setMassiveStatus(message, tone = "info") {
                const status = document.getElementById("massiveStatus");
                status.innerHTML = message;

                if (tone === "success") {
                    status.classList.add("success");
                } else {
                    status.classList.remove("success");
                }
            }

            function updateIndividualHelp() {
                const cycle = getIndividualCycle();
                const help = document.getElementById("individualHelp");

                if (!cycle) {
                    help.innerHTML = "<strong>Selecciona un ciclo:</strong> luego podrás elegir el curso y el estudiante.";
                } else if (cycle === "Primer_Ciclo") {
                    help.innerHTML = "<strong>Primer Ciclo:</strong> boletín completo y boletín por bloques.";
                } else {
                    help.innerHTML = "<strong>Segundo Ciclo:</strong> boletín completo, boletín de módulos y boletín por bloques + módulos.";
                }
            }

            function resetIndividualSelectors() {
                document.getElementById("studentCycle").value = "";
                setOptions("studentCourse", [], "Seleccione un ciclo primero");
                setOptions("studentSelect", [], "Seleccione un curso primero");
                individualStudents = [];
                setIndividualButtonsDisabled(true);
                updateIndividualHelp();
            }

            function resetMassiveSelectors() {
                document.getElementById("massiveCycle").value = "";
                setOptions("massiveCourse", [], "Seleccione un ciclo primero");
                updateMassiveButtons();
            }

            function saveLastQuery(data) {
                lastIndividualQuery = data;
                persistToStorage(STORAGE_KEYS.lastIndividualQuery, data);
                document.getElementById("lastQueryCycle").textContent = getCycleLabel(data.cycle);
                document.getElementById("lastQueryCourse").textContent = data.course || "-";
                document.getElementById("lastQueryStudent").textContent = data.studentLabel || data.studentId || "-";
                document.getElementById("lastQueryBox").style.display = "block";
            }

            function clearLastQuery() {
                lastIndividualQuery = null;
                removeFromStorage(STORAGE_KEYS.lastIndividualQuery);
                document.getElementById("lastQueryBox").style.display = "none";
                document.getElementById("lastQueryCycle").textContent = "-";
                document.getElementById("lastQueryCourse").textContent = "-";
                document.getElementById("lastQueryStudent").textContent = "-";
            }

            function restoreLastQuery() {
                const saved = loadFromStorage(STORAGE_KEYS.lastIndividualQuery);
                if (!saved || !saved.url) {
                    return;
                }
                lastIndividualQuery = saved;
                document.getElementById("lastQueryCycle").textContent = getCycleLabel(saved.cycle);
                document.getElementById("lastQueryCourse").textContent = saved.course || "-";
                document.getElementById("lastQueryStudent").textContent = saved.studentLabel || saved.studentId || "-";
                document.getElementById("lastQueryBox").style.display = "block";
            }

            function repeatLastQuery() {
                if (!lastIndividualQuery) {
                    return;
                }
                openRoute(lastIndividualQuery.url);
            }

            function saveLastMassiveQuery(data) {
                lastMassiveQuery = data;
                persistToStorage(STORAGE_KEYS.lastMassiveQuery, data);
                document.getElementById("lastMassiveCycle").textContent = getCycleLabel(data.cycle);
                document.getElementById("lastMassiveCourse").textContent = data.course || "-";
                document.getElementById("lastMassiveType").textContent = data.typeLabel || "-";
                document.getElementById("lastMassiveQueryBox").style.display = "block";
            }

            function clearLastMassiveQuery() {
                lastMassiveQuery = null;
                removeFromStorage(STORAGE_KEYS.lastMassiveQuery);
                document.getElementById("lastMassiveQueryBox").style.display = "none";
                document.getElementById("lastMassiveCycle").textContent = "-";
                document.getElementById("lastMassiveCourse").textContent = "-";
                document.getElementById("lastMassiveType").textContent = "-";
                updateMassiveButtons();
            }

            function restoreLastMassiveQuery() {
                const saved = loadFromStorage(STORAGE_KEYS.lastMassiveQuery);
                if (!saved || !saved.url) {
                    return;
                }
                lastMassiveQuery = saved;
                document.getElementById("lastMassiveCycle").textContent = getCycleLabel(saved.cycle);
                document.getElementById("lastMassiveCourse").textContent = saved.course || "-";
                document.getElementById("lastMassiveType").textContent = saved.typeLabel || "-";
                document.getElementById("lastMassiveQueryBox").style.display = "block";
            }

            function repeatLastMassiveQuery() {
                if (!lastMassiveQuery) {
                    return;
                }

                openRoute(lastMassiveQuery.url);
                setMassiveStatus(
                    "Se volvió a abrir la <strong>última generación masiva</strong> guardada.",
                    "success"
                );
            }

            async function loadStudentCourses() {
                const cycle = getIndividualCycle();
                setIndividualButtonsDisabled(true);
                setOptions("studentCourse", [], "Seleccione un ciclo primero");
                setOptions("studentSelect", [], "Seleccione un curso primero");
                updateIndividualHelp();

                if (!cycle) {
                    return;
                }

                setOptions("studentCourse", [], "Cargando cursos...");

                try {
                    const data = await fetchJson(`/students/options/courses?cycle=${encodeURIComponent(cycle)}`);
                    setOptions("studentCourse", data.courses || [], "Seleccione un curso");
                } catch (error) {
                    setOptions("studentCourse", [], "No se pudieron cargar los cursos");
                }
            }

            async function loadStudents() {
                const cycle = getIndividualCycle();
                const course = getIndividualCourse();
                setIndividualButtonsDisabled(true);

                if (!cycle) {
                    setOptions("studentCourse", [], "Seleccione un ciclo primero");
                    setOptions("studentSelect", [], "Seleccione un curso primero");
                    return;
                }

                if (!course) {
                    setOptions("studentSelect", [], "Seleccione un curso primero");
                    return;
                }

                setOptions("studentSelect", [], "Cargando estudiantes...");

                try {
                    const data = await fetchJson(`/students/options/students?cycle=${encodeURIComponent(cycle)}&course=${encodeURIComponent(course)}`);
                    individualStudents = data.students || [];
                    setOptions("studentSelect", individualStudents, "Seleccione un estudiante");
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

                if (cycle === "Primer_Ciclo" || !cycle) {
                    document.getElementById("btnModulesHtml").disabled = true;
                    document.getElementById("btnModulesPdf").disabled = true;
                } else {
                    document.getElementById("btnModulesHtml").disabled = disabled;
                    document.getElementById("btnModulesPdf").disabled = disabled;
                }
            }

            function buildStudentRoute(routeSuffix) {
                const studentId = getSelectedStudentId();
                return `/students/${studentId}/${routeSuffix}`;
            }

            function openStudentRoute(routeSuffix) {
                const cycle = getIndividualCycle();
                const course = getIndividualCourse();
                const studentId = document.getElementById("studentSelect").value;
                const studentLabel = getSelectedStudentLabel();
                const url = buildStudentRoute(routeSuffix);

                saveLastQuery({
                    cycle: cycle,
                    course: course,
                    studentId: studentId,
                    studentLabel: studentLabel,
                    routeSuffix: routeSuffix,
                    url: url
                });

                openRoute(url);
                resetIndividualSelectors();
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
                setOptions("massiveCourse", [], "Seleccione un ciclo primero");

                if (!cycle) {
                    updateMassiveButtons();
                    return;
                }

                setOptions("massiveCourse", [], "Cargando cursos...");

                try {
                    const data = await fetchJson(`/students/options/courses?cycle=${encodeURIComponent(cycle)}`);
                    setOptions("massiveCourse", data.courses || [], "Seleccione un curso");
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

                if (!cycle) {
                    setMassiveStatus("Selecciona un ciclo para continuar.");
                } else if (cycle === "Primer_Ciclo") {
                    setMassiveStatus("Para <strong>Primer Ciclo</strong> están disponibles el ZIP completo y el ZIP por bloques.");
                } else {
                    setMassiveStatus("Para <strong>Segundo Ciclo</strong> están disponibles el ZIP completo, el ZIP solo módulos y el ZIP bloques + módulos.");
                }
            }

            function finalizeMassiveDownload(data) {
                saveLastMassiveQuery(data);
                openRoute(data.url);
                setMassiveStatus(
                    `Descarga preparada: <strong>${data.typeLabel}</strong> del curso <strong>${data.course}</strong>. Puedes reabrirla desde la tarjeta de última generación.`,
                    "success"
                );
                resetMassiveSelectors();
            }

            function openCompleteZip() {
                const cycle = getMassiveCycle();
                const course = getMassiveCourse();

                if (!course) {
                    alert("Debes seleccionar un curso.");
                    return;
                }

                const url = `/students/course/${encodeURIComponent(cycle)}/${encodeURIComponent(course)}/bulletins-zip`;

                finalizeMassiveDownload({
                    cycle: cycle,
                    course: course,
                    typeLabel: "ZIP completo",
                    url: url
                });
            }

            function openBlocksZip() {
                const course = getMassiveCourse();

                if (!course) {
                    alert("Debes seleccionar un curso.");
                    return;
                }

                const url = `/students/course/Primer_Ciclo/${encodeURIComponent(course)}/bulletins-blocks-zip`;

                finalizeMassiveDownload({
                    cycle: "Primer_Ciclo",
                    course: course,
                    typeLabel: "ZIP por bloques",
                    url: url
                });
            }

            function openSecondCycleModulesZip() {
                const course = getMassiveCourse();

                if (!course) {
                    alert("Debes seleccionar un curso.");
                    return;
                }

                const url = `/students/course/Segundo_Ciclo/${encodeURIComponent(course)}/bulletins-modules-zip`;

                finalizeMassiveDownload({
                    cycle: "Segundo_Ciclo",
                    course: course,
                    typeLabel: "ZIP solo módulos",
                    url: url
                });
            }

            function openSecondCycleBlocksAndModulesZip() {
                const course = getMassiveCourse();

                if (!course) {
                    alert("Debes seleccionar un curso.");
                    return;
                }

                const url = `/students/course/Segundo_Ciclo/${encodeURIComponent(course)}/bulletins-blocks-and-modules-zip`;

                finalizeMassiveDownload({
                    cycle: "Segundo_Ciclo",
                    course: course,
                    typeLabel: "ZIP bloques + módulos",
                    url: url
                });
            }

            function initializeUI() {
                updateIndividualHelp();
                updateStudentButtons();
                updateMassiveButtons();
                clearLastQuery();
                clearLastMassiveQuery();
                restoreLastQuery();
                restoreLastMassiveQuery();
            }

            initializeUI();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)