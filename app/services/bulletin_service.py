from app.data.fetchers.google_sheets import load_primer_ciclo, load_segundo_ciclo


def find_student_by_id(student_id: str) -> dict | None:
    student_id = str(student_id).strip()

    primer = load_primer_ciclo()
    segundo = load_segundo_ciclo()

    primer["ID_ESTUDIANTE"] = primer["ID_ESTUDIANTE"].astype(str).str.strip()
    segundo["ID_ESTUDIANTE"] = segundo["ID_ESTUDIANTE"].astype(str).str.strip()

    student_primer = primer[primer["ID_ESTUDIANTE"] == student_id]
    if not student_primer.empty:
        row = student_primer.iloc[0]
        return {
            "found": True,
            "cycle": "Primer_Ciclo",
            "student": {
                "id_estudiante": row.get("ID_ESTUDIANTE", ""),
                "nombre_estudiante": row.get("NOMBRE_ESTUDIANTE", ""),
                "curso": row.get("CURSO", ""),
                "prof_titular": row.get("PROF_TITULAR", "")
            }
        }

    student_segundo = segundo[segundo["ID_ESTUDIANTE"] == student_id]
    if not student_segundo.empty:
        row = student_segundo.iloc[0]
        return {
            "found": True,
            "cycle": "Segundo_Ciclo",
            "student": {
                "id_estudiante": row.get("ID_ESTUDIANTE", ""),
                "nombre_estudiante": row.get("NOMBRE_ESTUDIANTE", ""),
                "curso": row.get("CURSO", ""),
                "prof_titular": row.get("PROF_TITULAR", "")
            }
        }

    return {
        "found": False,
        "message": f"No se encontró ningún estudiante con el ID {student_id}"
    }