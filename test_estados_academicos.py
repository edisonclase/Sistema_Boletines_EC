# test_estados_academicos.py

from collections import Counter

from academic_tracking.services.data_loader_service import load_academic_rows_from_source


rows = load_academic_rows_from_source()

counter = Counter()

for row in rows:
    estado = str(row.get("ESTADO") or "").strip()
    counter[estado] += 1

print("Estados encontrados:")
for estado, total in counter.most_common():
    print(f"{repr(estado)}: {total}")