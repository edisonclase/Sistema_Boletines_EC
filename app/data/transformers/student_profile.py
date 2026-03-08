import pandas as pd

from app.utils.helpers import safe_value


SUBJECTS_BY_CYCLE = {
    "Primer_Ciclo": [
        ("LEN", "Lengua Española"),
        ("ING", "Inglés"),
        ("FRA", "Francés"),
        ("MAT", "Matemática"),
        ("SOC", "Ciencias Sociales"),
        ("NAT", "Ciencias de la Naturaleza"),
        ("ART", "Educación Artística"),
        ("FIS", "Educación Física"),
        ("FOR", "Formación Integral Humana y Religiosa"),
    ],
    "Segundo_Ciclo": [
        ("LEN", "Lengua Española"),
        ("ING", "Inglés"),
        ("MAT", "Matemática"),
        ("SOC", "Ciencias Sociales"),
        ("NAT", "Ciencias de la Naturaleza"),
        ("ART", "Educación Artística"),
        ("FIS", "Educación Física"),
        ("FOR", "Formación Integral Humana y Religiosa"),
    ],
}


def _extract_scalar(value):
    if isinstance(value, pd.Series):
        values = value.tolist()
        for item in values:
            if safe_value(item) != "":
                return item
        return values[0] if values else None

    if isinstance(value, (list, tuple)):
        for item in value:
            if safe_value(item) != "":
                return item
        return value[0] if value else None

    try:
        if hasattr(value, "tolist") and not isinstance(value, (str, bytes)):
            as_list = value.tolist()
            if isinstance(as_list, list):
                for item in as_list:
                    if safe_value(item) != "":
                        return item
                return as_list[0] if as_list else None
    except Exception:
        pass

    return value


def _get_value(row, column_name):
    try:
        if column_name not in row.index:
            return ""
        value = row[column_name]
        value = _extract_scalar(value)
        return safe_value(value)
    except Exception:
        return ""


def _build_subject(prefix, label, row):
    return {
        "asignatura": label,

        "p1_c1": _get_value(row, f"{prefix}_C1_P1"),
        "p1_c2": _get_value(row, f"{prefix}_C2_P1"),
        "p1_c3": _get_value(row, f"{prefix}_C3_P1"),
        "p1_c4": _get_value(row, f"{prefix}_C4_P1"),

        "p2_c1": _get_value(row, f"{prefix}_C1_P2"),
        "p2_c2": _get_value(row, f"{prefix}_C2_P2"),
        "p2_c3": _get_value(row, f"{prefix}_C3_P2"),
        "p2_c4": _get_value(row, f"{prefix}_C4_P2"),

        "p3_c1": _get_value(row, f"{prefix}_C1_P3"),
        "p3_c2": _get_value(row, f"{prefix}_C2_P3"),
        "p3_c3": _get_value(row, f"{prefix}_C3_P3"),
        "p3_c4": _get_value(row, f"{prefix}_C4_P3"),

        "p4_c1": _get_value(row, f"{prefix}_C1_P4"),
        "p4_c2": _get_value(row, f"{prefix}_C2_P4"),
        "p4_c3": _get_value(row, f"{prefix}_C3_P4"),
        "p4_c4": _get_value(row, f"{prefix}_C4_P4"),

        "pc1": _get_value(row, f"{prefix}_PC1"),
        "pc2": _get_value(row, f"{prefix}_PC2"),
        "pc3": _get_value(row, f"{prefix}_PC3"),
        "pc4": _get_value(row, f"{prefix}_PC4"),

        "final": _get_value(row, f"{prefix}_CF_FINAL"),
        "asistencia_pct": _get_value(row, f"{prefix}_ASIST_PCT"),

        "comp_50cf": _get_value(row, f"{prefix}_COMP_50CF"),
        "comp_cec": _get_value(row, f"{prefix}_COMP_CEC"),
        "comp_50cec": _get_value(row, f"{prefix}_COMP_50CEC"),
        "ccf": _get_value(row, f"{prefix}_CCF"),

        "ext_30cf": _get_value(row, f"{prefix}_EXT_30CF"),
        "ext_ceex": _get_value(row, f"{prefix}_EXT_CEEX"),
        "ext_70ceex": _get_value(row, f"{prefix}_EXT_70CEEX"),
        "cexf": _get_value(row, f"{prefix}_CEXF"),

        "ce_especial": _get_value(row, f"{prefix}_CE_ESPECIAL"),

        "situ_a": _get_value(row, f"{prefix}_SITU_A"),
        "situ_r": _get_value(row, f"{prefix}_SITU_R"),
    }


def build_subjects(row, cycle):
    subjects_config = SUBJECTS_BY_CYCLE.get(cycle, [])
    subjects = []

    for prefix, label in subjects_config:
        subjects.append(_build_subject(prefix, label, row))

    return subjects


def _build_module(row, mod_number):
    name = _get_value(row, f"MOD{mod_number}_NOMBRE")

    if name == "":
        return None

    return {
        "modulo": name,
        "ra1": _get_value(row, f"MOD{mod_number}_RA1"),
        "ra2": _get_value(row, f"MOD{mod_number}_RA2"),
        "ra3": _get_value(row, f"MOD{mod_number}_RA3"),
        "ra4": _get_value(row, f"MOD{mod_number}_RA4"),
        "ra5": _get_value(row, f"MOD{mod_number}_RA5"),
        "ra6": _get_value(row, f"MOD{mod_number}_RA6"),
        "ra7": _get_value(row, f"MOD{mod_number}_RA7"),
        "ra8": _get_value(row, f"MOD{mod_number}_RA8"),
        "ra9": _get_value(row, f"MOD{mod_number}_RA9"),
        "ra10": _get_value(row, f"MOD{mod_number}_RA10"),
        "cf": _get_value(row, f"MOD{mod_number}_CF"),
        "situ_a": _get_value(row, f"MOD{mod_number}_SITU_A"),
    }


def build_modules(row):
    modules = []

    for mod_number in range(1, 6):
        module = _build_module(row, mod_number)
        if module:
            modules.append(module)

    return modules