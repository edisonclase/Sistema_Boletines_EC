from academic_tracking.services.data_loader_service import (
    load_academic_rows_from_source,
    load_completivo_attendance_control_rows_from_source,
)
from academic_tracking.services.completivo_service import build_completivo_report

rows = load_academic_rows_from_source()
control = load_completivo_attendance_control_rows_from_source()

report = build_completivo_report(
    rows=rows,
    attendance_rows_primer_ciclo=control["primer_ciclo"],
    attendance_rows_segundo_ciclo=control["segundo_ciclo"],
)

print("Total casos:", report["summary"]["total_cases"])
print("Total estudiantes:", report["summary"]["total_students"])
print("Por calificación:", report["summary"]["by_grade"])
print("Por asistencia:", report["summary"]["by_attendance"])
print("Por ambas:", report["summary"]["by_both"])
print("Casos en módulos:", report["summary"]["modules_cases"])

if report["rows"]:
    print("Primer caso:")
    print(report["rows"][0])