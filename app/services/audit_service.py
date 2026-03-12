from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.utils.helpers import safe_value


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _logs_dir() -> Path:
    path = _project_root() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _audit_file_path() -> Path:
    return _logs_dir() / "bulletin_audit.jsonl"


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _clean_value(value: Any) -> Any:
    if isinstance(value, str):
        return safe_value(value)
    return value


def _write_event(event: dict) -> None:
    """
    Escribe un evento de auditoría como una línea JSON.
    Nunca debe romper la generación principal si falla.
    """
    try:
        path = _audit_file_path()
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as exc:
        print(f"[AUDIT] No se pudo registrar el evento: {exc}", flush=True)


def log_student_bulletin_event(
    *,
    result: dict,
    output_format: str,
    bulletin_type: str,
    filename: str,
    generated_by: str,
    generated_role: str,
) -> None:
    student = result.get("student", {})

    event = {
        "timestamp": _now_iso(),
        "event_type": "student_bulletin",
        "output_format": _clean_value(output_format),      # html / pdf
        "bulletin_type": _clean_value(bulletin_type),      # complete / blocks / modules_only / blocks_and_modules
        "cycle": _clean_value(result.get("cycle")),
        "course": _clean_value(student.get("curso")),
        "student_id": _clean_value(student.get("id_estudiante")),
        "student_name": _clean_value(student.get("nombre_estudiante")),
        "filename": _clean_value(filename),
        "generated_by": _clean_value(generated_by),
        "generated_role": _clean_value(generated_role),
    }

    _write_event(event)


def log_course_zip_event(
    *,
    cycle: str,
    course: str,
    bulletin_type: str,
    filename: str,
    student_count: int,
    generated_by: str,
    generated_role: str,
) -> None:
    event = {
        "timestamp": _now_iso(),
        "event_type": "course_zip",
        "output_format": "zip",
        "bulletin_type": _clean_value(bulletin_type),      # complete / blocks / modules_only / blocks_and_modules
        "cycle": _clean_value(cycle),
        "course": _clean_value(course),
        "student_count": student_count,
        "filename": _clean_value(filename),
        "generated_by": _clean_value(generated_by),
        "generated_role": _clean_value(generated_role),
    }

    _write_event(event)