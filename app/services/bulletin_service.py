from app.data.fetchers.google_sheets import load_primer_ciclo, load_segundo_ciclo
from app.data.transformers.student_profile import build_subjects, build_modules
from app.utils.helpers import safe_value


def normalize_student_id(value) -> str:
    text = safe_value(value)

    if text.endswith(".0"):
        text = text[:-2]

    return text


def find_student_by_id(student_id: str) -> dict:
    student_id = normalize_student_id(student_id)

    primer = load_primer_ciclo().copy()
    segundo = load_segundo_ciclo().copy()

    if "ID_ESTUDIANTE" in primer.columns:
        primer["ID_ESTUDIANTE"] = primer["ID_ESTUDIANTE"].apply(normalize_student_id)

    if "ID_ESTUDIANTE" in segundo.columns:
        segundo["ID_ESTUDIANTE"] = segundo["ID_ESTUDIANTE"].apply(normalize_student_id)

    student_primer = primer[primer["ID_ESTUDIANTE"] == student_id]
    if not student_primer.empty:
        row = student_primer.iloc[0]
        return {
            "found": True,
            "cycle": "Primer_Ciclo",
            "student": {
                "id_estudiante": safe_value(row.get("ID_ESTUDIANTE")),
                "nombre_estudiante": safe_value(row.get("NOMBRE_ESTUDIANTE")),
                "numero": safe_value(row.get("NUMERO")),
                "curso": safe_value(row.get("CURSO")),
                "prof_titular": safe_value(row.get("PROF_TITULAR")),
                "asistencia_anual_pct": safe_value(row.get("ASIST_ANUAL_PCT")),
                "situacion_promovido": safe_value(row.get("SITUACION_PROMOVIDO")),
                "situacion_repitente": safe_value(row.get("SITUACION_REPITENTE")),
                "comentario_final": safe_value(row.get("COMENTARIO_FINAL")),
                "subjects": build_subjects(row, "Primer_Ciclo"),
                "modules": []
            }
        }

    student_segundo = segundo[segundo["ID_ESTUDIANTE"] == student_id]
    if not student_segundo.empty:
        row = student_segundo.iloc[0]
        return {
            "found": True,
            "cycle": "Segundo_Ciclo",
            "student": {
                "id_estudiante": safe_value(row.get("ID_ESTUDIANTE")),
                "nombre_estudiante": safe_value(row.get("NOMBRE_ESTUDIANTE")),
                "numero": safe_value(row.get("NUMERO")),
                "curso": safe_value(row.get("CURSO")),
                "prof_titular": safe_value(row.get("PROF_TITULAR")),
                "situacion_promovido": safe_value(row.get("SITUACION_PROMOVIDO")),
                "situacion_repitente": safe_value(row.get("SITUACION_REPITENTE")),
                "situacion_pendiente": safe_value(row.get("SITUACION_PENDIENTE")),
                "subjects": build_subjects(row, "Segundo_Ciclo"),
                "modules": build_modules(row)
            }
        }

    return {
        "found": False,
        "message": f"No se encontró ningún estudiante con el ID {student_id}"
    }