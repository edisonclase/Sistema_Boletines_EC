(function () {
    const cycleSelect = document.getElementById("ciclo");
    const gradeSelect = document.getElementById("grado");
    const sectionSelect = document.getElementById("seccion");

    function setupDependentFilters() {
        if (!cycleSelect || !gradeSelect || !sectionSelect) {
            return;
        }

        const originalGradeOptions = Array.from(gradeSelect.options).map((option) => ({
            value: option.value,
            text: option.text,
            cycle: option.getAttribute("data-cycle") || ""
        }));

        const originalSectionOptions = Array.from(sectionSelect.options).map((option) => ({
            value: option.value,
            text: option.text,
            cycle: option.getAttribute("data-cycle") || "",
            gradeList: option.getAttribute("data-grade-list") || ""
        }));

        function renderGrades() {
            const selectedCycle = cycleSelect.value || "";
            const currentGrade = gradeSelect.value || "";

            gradeSelect.innerHTML = "";

            originalGradeOptions.forEach((item) => {
                const option = document.createElement("option");
                option.value = item.value;
                option.textContent = item.text;

                if (item.value !== "" && selectedCycle && item.cycle !== selectedCycle) {
                    return;
                }

                if (item.value === currentGrade) {
                    option.selected = true;
                }

                gradeSelect.appendChild(option);
            });

            const availableGradeValues = Array.from(gradeSelect.options).map((opt) => opt.value);
            if (!availableGradeValues.includes(currentGrade)) {
                gradeSelect.value = "";
            }
        }

        function renderSections() {
            const selectedCycle = cycleSelect.value || "";
            const selectedGrade = gradeSelect.value || "";
            const currentSection = sectionSelect.value || "";

            sectionSelect.innerHTML = "";

            originalSectionOptions.forEach((item) => {
                const option = document.createElement("option");
                option.value = item.value;
                option.textContent = item.text;

                if (item.value === "") {
                    sectionSelect.appendChild(option);
                    return;
                }

                const grades = item.gradeList.split("|").filter(Boolean);
                const cycleOk = !selectedCycle || item.cycle === selectedCycle;
                const gradeOk = !selectedGrade || grades.includes(selectedGrade);

                if (!cycleOk || !gradeOk) {
                    return;
                }

                if (item.value === currentSection) {
                    option.selected = true;
                }

                sectionSelect.appendChild(option);
            });

            const availableSectionValues = Array.from(sectionSelect.options).map((opt) => opt.value);
            if (!availableSectionValues.includes(currentSection)) {
                sectionSelect.value = "";
            }
        }

        cycleSelect.addEventListener("change", function () {
            renderGrades();
            renderSections();
        });

        gradeSelect.addEventListener("change", renderSections);

        renderGrades();
        renderSections();
    }

    function printCurrentView() {
        window.print();
    }

    function getAllRowCheckboxes() {
        return Array.from(document.querySelectorAll(".student-row-checkbox"));
    }

    function getCheckedRows() {
        const checked = getAllRowCheckboxes().filter((checkbox) => checkbox.checked);
        return checked
            .map((checkbox) => checkbox.closest("tr"))
            .filter(Boolean);
    }

    function openPrintWindow(title, tableHtml) {
        const printWindow = window.open("", "_blank", "width=1200,height=800");

        if (!printWindow) {
            alert("No se pudo abrir la ventana de impresión. Verifica si el navegador bloqueó las ventanas emergentes.");
            return;
        }

        const styles = `
            <style>
                body {
                    font-family: Arial, Helvetica, sans-serif;
                    margin: 24px;
                    color: #1f2937;
                }

                h1 {
                    margin: 0 0 8px;
                    font-size: 24px;
                    color: #0b3d24;
                }

                p {
                    margin: 0 0 20px;
                    color: #475467;
                    font-size: 14px;
                }

                table {
                    width: 100%;
                    border-collapse: collapse;
                    table-layout: fixed;
                }

                th, td {
                    border: 1px solid #d9e3dc;
                    padding: 10px;
                    vertical-align: top;
                    font-size: 12px;
                    text-align: left;
                }

                th {
                    background: #f4f7f5;
                    color: #0b3d24;
                    text-transform: uppercase;
                }

                .badge {
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 999px;
                    font-size: 11px;
                    font-weight: 700;
                    border: 1px solid #d9e3dc;
                    background: #f8faf9;
                    color: #1f2937;
                }

                .subject-item-print {
                    margin-bottom: 8px;
                    padding-bottom: 8px;
                    border-bottom: 1px dashed #d9e3dc;
                }

                .subject-item-print:last-child {
                    border-bottom: none;
                    margin-bottom: 0;
                    padding-bottom: 0;
                }

                .block-line-print {
                    margin-top: 4px;
                    padding-left: 10px;
                }
            </style>
        `;

        printWindow.document.open();
        printWindow.document.write(`
            <html>
            <head>
                <title>${title}</title>
                ${styles}
            </head>
            <body>
                <h1>${title}</h1>
                <p>Seguimiento académico institucional</p>
                ${tableHtml}
            </body>
            </html>
        `);
        printWindow.document.close();

        printWindow.focus();
        setTimeout(() => {
            printWindow.print();
        }, 300);
    }

    function buildPrintableTableFromRows(rows) {
        const printableRows = rows.map((row) => {
            const cells = row.querySelectorAll("td");
            if (cells.length < 8) {
                return "";
            }

            const numero = cells[1].innerHTML;
            const estudiante = cells[2].innerHTML;
            const curso = cells[3].innerHTML;
            const periodo = cells[4].innerHTML;
            const incidencias = cells[5].innerHTML;
            const estado = cells[6].innerHTML;

            return `
                <tr>
                    <td>${numero}</td>
                    <td>${estudiante}</td>
                    <td>${curso}</td>
                    <td>${periodo}</td>
                    <td>${incidencias}</td>
                    <td>${estado}</td>
                </tr>
            `;
        }).join("");

        return `
            <table>
                <thead>
                    <tr>
                        <th>No.</th>
                        <th>Estudiante</th>
                        <th>Curso</th>
                        <th>Período</th>
                        <th>Asignaturas pendientes y bloques de competencias</th>
                        <th>Estado general</th>
                    </tr>
                </thead>
                <tbody>
                    ${printableRows}
                </tbody>
            </table>
        `;
    }

    function setupSelectionAndPrinting() {
        const selectAllCheckbox = document.getElementById("select-all-students");
        const printSelectedBtn = document.getElementById("print-selected-btn");
        const printCurrentViewBtn = document.getElementById("print-current-view-btn");
        const rowCheckboxes = getAllRowCheckboxes();
        const printOneButtons = Array.from(document.querySelectorAll(".btn-print-one"));

        if (printCurrentViewBtn) {
            printCurrentViewBtn.addEventListener("click", printCurrentView);
        }

        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener("change", function () {
                rowCheckboxes.forEach((checkbox) => {
                    checkbox.checked = selectAllCheckbox.checked;
                });
            });
        }

        rowCheckboxes.forEach((checkbox) => {
            checkbox.addEventListener("change", function () {
                if (!selectAllCheckbox) return;
                const allChecked = rowCheckboxes.length > 0 && rowCheckboxes.every((item) => item.checked);
                selectAllCheckbox.checked = allChecked;
            });
        });

        if (printSelectedBtn) {
            printSelectedBtn.addEventListener("click", function () {
                const selectedRows = getCheckedRows();

                if (!selectedRows.length) {
                    alert("Selecciona al menos un estudiante para imprimir.");
                    return;
                }

                const tableHtml = buildPrintableTableFromRows(selectedRows);
                openPrintWindow("Reporte de estudiantes seleccionados", tableHtml);
            });
        }

        printOneButtons.forEach((button) => {
            button.addEventListener("click", function () {
                const row = button.closest("tr");
                if (!row) return;

                const studentName = row.getAttribute("data-student-name") || "Estudiante";
                const tableHtml = buildPrintableTableFromRows([row]);

                openPrintWindow(`Reporte individual - ${studentName}`, tableHtml);
            });
        });
    }

    setupDependentFilters();
    setupSelectionAndPrinting();
})();