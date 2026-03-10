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
        <title>Sistema de Boletines Automatizados EC</title>
        <style>
            * {
                box-sizing: border-box;
            }

            body {
                margin: 0;
                font-family: Arial, Helvetica, sans-serif;
                background: #f4f7f4;
                color: #111;
            }

            .wrapper {
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 24px;
            }

            .card {
                width: 100%;
                max-width: 760px;
                background: #ffffff;
                border: 2px solid #66BB6A;
                border-radius: 16px;
                box-shadow: 0 10px 28px rgba(0, 0, 0, 0.08);
                padding: 28px;
            }

            .title {
                margin: 0 0 8px 0;
                text-align: center;
                font-size: 28px;
                font-weight: bold;
                color: #1b5e20;
            }

            .subtitle {
                margin: 0 0 24px 0;
                text-align: center;
                font-size: 14px;
                color: #555;
            }

            .form-group {
                margin-bottom: 18px;
            }

            label {
                display: block;
                font-weight: bold;
                margin-bottom: 8px;
                font-size: 15px;
            }

            input[type="text"] {
                width: 100%;
                padding: 14px 16px;
                border: 1px solid #b7d9bb;
                border-radius: 10px;
                font-size: 18px;
                outline: none;
            }

            input[type="text"]:focus {
                border-color: #43a047;
                box-shadow: 0 0 0 3px rgba(67, 160, 71, 0.12);
            }

            .buttons-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 14px;
                margin-top: 18px;
            }

            button {
                border: none;
                border-radius: 12px;
                padding: 16px 14px;
                font-size: 15px;
                font-weight: bold;
                cursor: pointer;
                transition: transform 0.08s ease, opacity 0.08s ease;
            }

            button:hover {
                opacity: 0.95;
            }

            button:active {
                transform: scale(0.99);
            }

            .btn-primary {
                background: #2e7d32;
                color: white;
            }

            .btn-secondary {
                background: #388e3c;
                color: white;
            }

            .btn-outline {
                background: #e8f5e9;
                color: #1b5e20;
                border: 1px solid #a5d6a7;
            }

            .btn-outline-dark {
                background: #f1f8f1;
                color: #0f3d12;
                border: 1px solid #b7d9bb;
            }

            .help-box {
                margin-top: 22px;
                padding: 14px 16px;
                border-radius: 10px;
                background: #f8fff8;
                border: 1px solid #d8ecd9;
                font-size: 13px;
                color: #444;
                line-height: 1.5;
            }

            .footer {
                margin-top: 20px;
                text-align: center;
                font-size: 12px;
                color: #666;
            }

            @media (max-width: 680px) {
                .buttons-grid {
                    grid-template-columns: 1fr;
                }

                .card {
                    padding: 20px;
                }

                .title {
                    font-size: 24px;
                }
            }
        </style>
    </head>
    <body>
        <div class="wrapper">
            <div class="card">
                <h1 class="title">Sistema de Boletines Automatizados EC</h1>
                <p class="subtitle">Generación rápida de boletines académicos</p>

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

                    <button class="btn-outline" onclick="openRoute('/students/' + getStudentId() + '/bulletin-blocks-html')">
                        Ver boletín por bloques (HTML)
                    </button>

                    <button class="btn-outline-dark" onclick="openRoute('/students/' + getStudentId() + '/bulletin-blocks-pdf')">
                        Descargar boletín por bloques (PDF)
                    </button>
                </div>

                <div class="help-box">
                    Escribe el ID del estudiante y selecciona el tipo de boletín que deseas visualizar o descargar.
                </div>

                <div class="footer">
                    Panel inicial del proyecto
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

            function openRoute(url) {
                window.open(url, "_blank");
            }

            document.getElementById("studentId").addEventListener("keydown", function(event) {
                if (event.key === "Enter") {
                    openRoute('/students/' + getStudentId() + '/bulletin-pdf');
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)