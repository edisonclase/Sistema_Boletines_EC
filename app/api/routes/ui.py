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
        <title>Sistema Automatizado de Boletines Académicos</title>
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
                max-width: 1180px;
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
                max-width: 760px;
                font-size: 16px;
                color: var(--muted);
                line-height: 1.55;
            }

            .grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
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

            input[type="text"],
            select {
                width: 100%;
                padding: 13px 14px;
                border: 1px solid var(--line-strong);
                border-radius: 12px;
                font-size: 16px;
                outline: none;
                background: #fff;
                color: var(--text);
            }

            input[type="text"]:focus,
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
            }

            button:hover {
                opacity: 0.97;
                box-shadow: 0 10px 18px rgba(15, 23, 42, 0.08);
            }

            button:active {
                transform: scale(0.99);
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

            .footer {
                margin-top: 18px;
                text-align: center;
                font-size: 12px;
                color: var(--muted);
            }

            .footer strong {
                color: var(--accent);
            }

            @media (max-width: 980px) {
                .grid {
                    grid-template-columns: 1fr;
                }
            }

            @media (max-width: 640px) {
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
                    <div class="hero-badge">Plataforma de generación académica</div>
                    <h1 class="hero-title">Sistema Automatizado de Boletines Académicos</h1>
                    <p class="hero-subtitle">
                        Genera boletines individuales y masivos desde una interfaz simple.
                        Esta versión ya permite trabajar por estudiante y por curso.
                    </p>
                </div>

                <div class="grid">
                    <div class="card">
                        <div class="card-header">
                            <div class="card-kicker">Modo individual</div>
                            <h2 class="card-title">Boletines por estudiante</h2>
                            <p class="card-subtitle">
                                Introduce el ID del estudiante para visualizar o descargar
                                sus boletines en HTML o PDF.
                            </p>
                        </div>

                        <div class="section">
                            <h3 class="section-title">Consulta individual</h3>

                            <div class="form-group">
                                <label for="studentId">ID del estudiante</label>
                                <input
                                    type="text"
                                    id="studentId"
                                    placeholder="Ejemplo: 32387390"
                                    autofocus
                                />
                            </div>

                            <div class="buttons-grid">
                                <button class="btn-primary" onclick="openRoute('/students/' + getStudentId() + '/bulletin-html')">
                                    Ver boletín completo (HTML)
                                </button>

                                <button class="btn-secondary" onclick="openRoute('/students/' + getStudentId() + '/bulletin-pdf')">
                                    Descargar boletín completo (PDF)
                                </button>

                                <button class="btn-soft" onclick="openRoute('/students/' + getStudentId() + '/bulletin-blocks-html')">
                                    Ver boletín por bloques (HTML)
                                </button>

                                <button class="btn-dark" onclick="openRoute('/students/' + getStudentId() + '/bulletin-blocks-pdf')">
                                    Descargar boletín por bloques (PDF)
                                </button>
                            </div>
                        </div>

                        <div class="help-box">
                            <strong>Nota:</strong> el boletín por bloques está disponible actualmente
                            para <strong>Primer Ciclo</strong>. La versión por bloques de
                            <strong>Segundo Ciclo</strong> está en desarrollo. El boletín completo
                            funciona según el ciclo del estudiante.
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <div class="card-kicker">Modo masivo</div>
                            <h2 class="card-title">Boletines por curso</h2>
                            <p class="card-subtitle">
                                Genera un ZIP con todos los boletines de un curso. En la descarga masiva,
                                la filosofía institucional se agrega una sola vez dentro del ZIP.
                            </p>
                        </div>

                        <div class="section">
                            <h3 class="section-title">Generación masiva</h3>

                            <div class="form-group">
                                <label for="cycle">Ciclo</label>
                                <select id="cycle">
                                    <option value="Primer_Ciclo">Primer Ciclo</option>
                                    <option value="Segundo_Ciclo">Segundo Ciclo</option>
                                </select>
                            </div>

                            <div class="form-group">
                                <label for="course">Curso</label>
                                <input
                                    type="text"
                                    id="course"
                                    placeholder="Ejemplo: 2do A"
                                />
                            </div>

                            <div class="buttons-grid">
                                <button class="btn-primary" onclick="openCompleteZip()">
                                    Descargar ZIP completo
                                </button>

                                <button class="btn-outline" onclick="openBlocksZip()">
                                    Descargar ZIP por bloques
                                </button>
                            </div>
                        </div>

                        <div class="help-box">
                            <strong>Nota:</strong> el ZIP por bloques se genera solo para
                            <strong>Primer Ciclo</strong>. Para <strong>Segundo Ciclo</strong>,
                            utiliza por ahora el ZIP completo mientras finaliza la versión por bloques.
                        </div>
                    </div>
                </div>

                <div class="footer">
                    Panel inicial del proyecto · futura capa de acceso por <strong>roles</strong> pendiente
                </div>
            </div>
        </div>

        <script>
            function getStudentId() {
                const value = document.getElementById("studentId").value.trim();

                if (!value) {
                    alert("Debes escribir el ID del estudiante.");
                    throw new Error("ID vacío");
                }

                return encodeURIComponent(value);
            }

            function getCourse() {
                const value = document.getElementById("course").value.trim();

                if (!value) {
                    alert("Debes escribir el curso.");
                    throw new Error("Curso vacío");
                }

                return encodeURIComponent(value);
            }

            function getCycle() {
                return document.getElementById("cycle").value;
            }

            function openRoute(url) {
                window.open(url, "_blank");
            }

            function openCompleteZip() {
                const cycle = getCycle();
                const course = getCourse();
                openRoute('/students/course/' + cycle + '/' + course + '/bulletins-zip');
            }

            function openBlocksZip() {
                const cycle = getCycle();

                if (cycle !== 'Primer_Ciclo') {
                    alert('El ZIP por bloques solo está disponible para Primer Ciclo.');
                    return;
                }

                const course = getCourse();
                openRoute('/students/course/Primer_Ciclo/' + course + '/bulletins-blocks-zip');
            }

            document.getElementById("studentId").addEventListener("keydown", function(event) {
                if (event.key === "Enter") {
                    openRoute('/students/' + getStudentId() + '/bulletin-pdf');
                }
            });

            document.getElementById("course").addEventListener("keydown", function(event) {
                if (event.key === "Enter") {
                    openCompleteZip();
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)