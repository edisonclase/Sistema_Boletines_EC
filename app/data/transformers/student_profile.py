from app.utils.helpers import safe_value, format_grade


FIRST_CYCLE_SUBJECTS = {
    "LEN": "Lengua Española",
    "ING": "Inglés",
    "FRA": "Francés",
    "MAT": "Matemática",
    "SOC": "Ciencias Sociales",
    "NAT": "Ciencias de la Naturaleza",
    "ART": "Educación Artística",
    "FIS": "Educación Física",
    "FOR": "Formación Humana",
}

SECOND_CYCLE_SUBJECTS = {
    "LEN": "Lengua Española",
    "ING": "Inglés",
    "MAT": "Matemática",
    "SOC": "Ciencias Sociales",
    "NAT": "Ciencias de la Naturaleza",
    "ART": "Educación Artística",
    "FIS": "Educación Física",
    "FOR": "Formación Humana",
}


def build_subjects(row, cycle: str) -> list:
    subjects_map = FIRST_CYCLE_SUBJECTS if cycle == "Primer_Ciclo" else SECOND_CYCLE_SUBJECTS
    subjects = []

    for code, name in subjects_map.items():
        subjects.append({
            "code": code,
            "name": name,
            "p1": [
                format_grade(row.get(f"{code}_C1_P1")),
                format_grade(row.get(f"{code}_C1_P2")),
                format_grade(row.get(f"{code}_C1_P3")),
                format_grade(row.get(f"{code}_C1_P4")),
            ],
            "p2": [
                format_grade(row.get(f"{code}_C2_P1")),
                format_grade(row.get(f"{code}_C2_P2")),
                format_grade(row.get(f"{code}_C2_P3")),
                format_grade(row.get(f"{code}_C2_P4")),
            ],
            "p3": [
                format_grade(row.get(f"{code}_C3_P1")),
                format_grade(row.get(f"{code}_C3_P2")),
                format_grade(row.get(f"{code}_C3_P3")),
                format_grade(row.get(f"{code}_C3_P4")),
            ],
            "p4": [
                format_grade(row.get(f"{code}_C4_P1")),
                format_grade(row.get(f"{code}_C4_P2")),
                format_grade(row.get(f"{code}_C4_P3")),
                format_grade(row.get(f"{code}_C4_P4")),
            ],
            "pc": [
                format_grade(row.get(f"{code}_PC1")),
                format_grade(row.get(f"{code}_PC2")),
                format_grade(row.get(f"{code}_PC3")),
                format_grade(row.get(f"{code}_PC4")),
            ],
            "cf_area": format_grade(row.get(f"{code}_CF_AREA")),
            "asistencia_pct": safe_value(row.get(f"{code}_ASIST_PCT")),
            "comp_50cf": format_grade(row.get(f"{code}_COMP_50CF")),
            "comp_cec": format_grade(row.get(f"{code}_COMP_CEC")),
            "comp_50cec": format_grade(row.get(f"{code}_COMP_50CEC")),
            "ccf": format_grade(row.get(f"{code}_CCF")),
            "ext_30cf": format_grade(row.get(f"{code}_EXT_30CF")),
            "ext_ceex": format_grade(row.get(f"{code}_EXT_CEEX")),
            "ext_70ceex": format_grade(row.get(f"{code}_EXT_70CEEX")),
            "cexf": format_grade(row.get(f"{code}_CEXF")),
            "cf_final": format_grade(row.get(f"{code}_CF_FINAL")),
            "ce_especial": format_grade(row.get(f"{code}_CE_ESPECIAL")),
            "situ_a": safe_value(row.get(f"{code}_SITU_A")),
            "situ_r": safe_value(row.get(f"{code}_SITU_R")),
        })

    return subjects


def build_modules(row) -> list:
    modules = []

    for i in range(1, 6):
        module_name = safe_value(row.get(f"MOD{i}_NOMBRE"))
        if not module_name:
            continue

        modules.append({
            "nombre": module_name,
            "ra": [
                safe_value(row.get(f"MOD{i}_RA1")),
                safe_value(row.get(f"MOD{i}_RA2")),
                safe_value(row.get(f"MOD{i}_RA3")),
                safe_value(row.get(f"MOD{i}_RA4")),
                safe_value(row.get(f"MOD{i}_RA5")),
                safe_value(row.get(f"MOD{i}_RA6")),
                safe_value(row.get(f"MOD{i}_RA7")),
                safe_value(row.get(f"MOD{i}_RA8")),
                safe_value(row.get(f"MOD{i}_RA9")),
                safe_value(row.get(f"MOD{i}_RA10")),
            ],
            "cf": safe_value(row.get(f"MOD{i}_CF")),
            "situ_a": safe_value(row.get(f"MOD{i}_SITU_A")),
        })

    return modules