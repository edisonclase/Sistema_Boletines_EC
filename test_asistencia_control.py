from academic_tracking.services.data_loader_service import (
    load_completivo_attendance_control_rows_from_source,
)

control = load_completivo_attendance_control_rows_from_source()

print("Primer ciclo:", len(control["primer_ciclo"]))
print("Segundo ciclo:", len(control["segundo_ciclo"]))

for ciclo_key in ["primer_ciclo", "segundo_ciclo"]:
    print("\n---", ciclo_key, "---")

    rows = control[ciclo_key]
    print("Filas:", len(rows))

    if rows:
        print("Columnas:")
        print(list(rows[0].keys()))

    total_completivo = 0

    for row in rows:
        for key, value in row.items():
            if key.endswith("_DECISION_GESTION"):
                if str(value).strip().upper() == "COMPLETIVO":
                    total_completivo += 1

    print("Decisiones COMPLETIVO:", total_completivo)

    if rows:
        print("Primera fila:")
        print(rows[0])