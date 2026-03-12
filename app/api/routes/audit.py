import json
import os
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["audit"])

AUDIT_FILE = "logs/bulletin_audit.jsonl"


def load_audit_events(limit=100):
    if not os.path.exists(AUDIT_FILE):
        return []

    events = []

    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                events.append(json.loads(line))
            except:
                pass

    events.reverse()

    return events[:limit]


@router.get("/audit", response_class=HTMLResponse)
def view_audit():
    events = load_audit_events()

    rows = ""

    for e in events:
        rows += f"""
        <tr>
            <td>{e.get("timestamp","")}</td>
            <td>{e.get("generated_by","")}</td>
            <td>{e.get("generated_role","")}</td>
            <td>{e.get("event_type","")}</td>
            <td>{e.get("cycle","")}</td>
            <td>{e.get("course","")}</td>
            <td>{e.get("student_name","")}</td>
            <td>{e.get("filename","")}</td>
        </tr>
        """

    html = f"""
    <html>
    <head>
        <title>Auditoría del Sistema</title>
        <style>
        body {{
            font-family: Arial;
            padding: 40px;
            background:#F8FAFC;
        }}

        table {{
            border-collapse: collapse;
            width:100%;
            background:white;
        }}

        th, td {{
            border:1px solid #ddd;
            padding:8px;
            font-size:13px;
        }}

        th {{
            background:#6366F1;
            color:white;
        }}

        h1 {{
            margin-bottom:20px;
        }}
        </style>
    </head>

    <body>

    <h1>Registro de Auditoría</h1>

    <table>
        <tr>
            <th>Fecha</th>
            <th>Usuario</th>
            <th>Rol</th>
            <th>Evento</th>
            <th>Ciclo</th>
            <th>Curso</th>
            <th>Estudiante</th>
            <th>Archivo</th>
        </tr>

        {rows}

    </table>

    </body>
    </html>
    """

    return HTMLResponse(content=html)