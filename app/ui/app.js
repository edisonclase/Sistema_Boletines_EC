let individualStudents = [];
let lastIndividualQuery = null;
let lastMassiveQuery = null;

let progressInterval = null;
let progressValue = 0;
let progressTarget = 0;
let progressLocked = false;
let progressCompletionTimeout = null;

const STORAGE_KEYS = {
    lastIndividualQuery: "clase_edutech_last_individual_query",
    lastMassiveQuery: "clase_edutech_last_massive_query",
    authToken: "clase_edutech_auth_token",
    authUser: "clase_edutech_auth_user"
};

const progressPresets = {
    "bulletin-html": {
        title: "Abriendo boletín completo",
        subtitle: "Estamos preparando la vista HTML del estudiante seleccionado.",
        steps: [
            { percent: 18, label: "Validando selección del estudiante..." },
            { percent: 42, label: "Consultando información académica..." },
            { percent: 72, label: "Renderizando vista HTML..." },
            { percent: 92, label: "Abriendo boletín..." }
        ]
    },
    "bulletin-pdf": {
        title: "Generando boletín completo",
        subtitle: "Estamos preparando el PDF individual con los datos académicos.",
        steps: [
            { percent: 16, label: "Validando datos del estudiante..." },
            { percent: 39, label: "Construyendo contenido del boletín..." },
            { percent: 67, label: "Generando PDF..." },
            { percent: 91, label: "Preparando descarga..." }
        ]
    },
    "bulletin-blocks-html": {
        title: "Abriendo boletín por bloques",
        subtitle: "Se está preparando la vista por bloques del estudiante.",
        steps: [
            { percent: 18, label: "Verificando ciclo académico..." },
            { percent: 44, label: "Consultando bloques..." },
            { percent: 74, label: "Renderizando vista..." },
            { percent: 92, label: "Abriendo boletín..." }
        ]
    },
    "bulletin-blocks-pdf": {
        title: "Generando PDF por bloques",
        subtitle: "Se está preparando el PDF del boletín por bloques.",
        steps: [
            { percent: 18, label: "Verificando ciclo académico..." },
            { percent: 41, label: "Armando estructura..." },
            { percent: 68, label: "Convirtiendo a PDF..." },
            { percent: 92, label: "Preparando descarga..." }
        ]
    },
    "second-cycle-blocks-html": {
        title: "Abriendo bloques y módulos",
        subtitle: "Se está preparando la vista combinada de bloques y módulos.",
        steps: [
            { percent: 18, label: "Verificando segundo ciclo..." },
            { percent: 45, label: "Consultando bloques y módulos..." },
            { percent: 74, label: "Renderizando vista..." },
            { percent: 92, label: "Abriendo boletín..." }
        ]
    },
    "second-cycle-blocks-pdf": {
        title: "Generando PDF de bloques y módulos",
        subtitle: "Se está preparando el PDF combinado del segundo ciclo.",
        steps: [
            { percent: 16, label: "Validando perfil académico..." },
            { percent: 43, label: "Armando contenido..." },
            { percent: 70, label: "Generando PDF..." },
            { percent: 92, label: "Preparando descarga..." }
        ]
    },
    "modules-only-html": {
        title: "Abriendo boletín de módulos",
        subtitle: "Estamos preparando la vista HTML de módulos técnicos.",
        steps: [
            { percent: 18, label: "Verificando segundo ciclo..." },
            { percent: 46, label: "Consultando módulos técnicos..." },
            { percent: 74, label: "Renderizando vista..." },
            { percent: 92, label: "Abriendo boletín..." }
        ]
    },
    "modules-only-pdf": {
        title: "Generando PDF de módulos",
        subtitle: "Estamos preparando el PDF de módulos técnicos.",
        steps: [
            { percent: 16, label: "Verificando segundo ciclo..." },
            { percent: 42, label: "Preparando módulos..." },
            { percent: 69, label: "Generando PDF..." },
            { percent: 92, label: "Preparando descarga..." }
        ]
    },
    "zip-complete": {
        title: "Generando ZIP completo",
        subtitle: "Estamos preparando todos los boletines completos del curso seleccionado.",
        steps: [
            { percent: 12, label: "Validando curso y ciclo..." },
            { percent: 31, label: "Consultando estudiantes..." },
            { percent: 58, label: "Generando boletines..." },
            { percent: 84, label: "Comprimiendo archivos..." },
            { percent: 94, label: "Preparando descarga..." }
        ]
    },
    "zip-blocks": {
        title: "Generando ZIP por bloques",
        subtitle: "Estamos preparando todos los boletines por bloques del curso.",
        steps: [
            { percent: 12, label: "Validando Primer Ciclo..." },
            { percent: 31, label: "Consultando estudiantes..." },
            { percent: 58, label: "Generando PDFs..." },
            { percent: 84, label: "Comprimiendo archivos..." },
            { percent: 94, label: "Preparando descarga..." }
        ]
    },
    "zip-modules": {
        title: "Generando ZIP de módulos",
        subtitle: "Estamos preparando los boletines de módulos del curso seleccionado.",
        steps: [
            { percent: 12, label: "Validando Segundo Ciclo..." },
            { percent: 31, label: "Consultando estudiantes..." },
            { percent: 58, label: "Generando PDFs..." },
            { percent: 84, label: "Comprimiendo archivos..." },
            { percent: 94, label: "Preparando descarga..." }
        ]
    },
    "zip-blocks-modules": {
        title: "Generando ZIP bloques + módulos",
        subtitle: "Estamos preparando la generación masiva combinada del segundo ciclo.",
        steps: [
            { percent: 12, label: "Validando Segundo Ciclo..." },
            { percent: 31, label: "Consultando estudiantes..." },
            { percent: 58, label: "Generando PDFs..." },
            { percent: 84, label: "Comprimiendo archivos..." },
            { percent: 94, label: "Preparando descarga..." }
        ]
    }
};

function persistToStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
        console.warn("No se pudo guardar en localStorage:", error);
    }
}

function loadFromStorage(key) {
    try {
        const raw = localStorage.getItem(key);
        if (!raw) {
            return null;
        }
        return JSON.parse(raw);
    } catch (error) {
        console.warn("No se pudo leer desde localStorage:", error);
        return null;
    }
}

function removeFromStorage(key) {
    try {
        localStorage.removeItem(key);
    } catch (error) {
        console.warn("No se pudo limpiar localStorage:", error);
    }
}

function getToken() {
    return loadFromStorage(STORAGE_KEYS.authToken);
}

function setToken(token) {
    persistToStorage(STORAGE_KEYS.authToken, token);
}

function clearToken() {
    removeFromStorage(STORAGE_KEYS.authToken);
}

function setAuthUser(user) {
    persistToStorage(STORAGE_KEYS.authUser, user);
}

function getAuthUser() {
    return loadFromStorage(STORAGE_KEYS.authUser);
}

function clearAuthUser() {
    removeFromStorage(STORAGE_KEYS.authUser);
}

function setLoginStatus(message, tone = "info") {
    const box = document.getElementById("loginStatus");
    if (!box) return;
    box.textContent = message;
    box.classList.remove("success", "error");
    if (tone === "success") box.classList.add("success");
    if (tone === "error") box.classList.add("error");
}

async function authFetch(url, options = {}) {
    const token = getToken();
    if (!token) {
        throw new Error("Debes iniciar sesión.");
    }

    const headers = new Headers(options.headers || {});
    headers.set("Authorization", `Bearer ${token}`);

    const response = await fetch(url, {
        ...options,
        headers
    });

    if (response.status === 401) {
        logout(false);
        throw new Error("Tu sesión expiró. Inicia sesión nuevamente.");
    }

    return response;
}

async function fetchJson(url) {
    const response = await authFetch(url);
    if (!response.ok) {
        throw new Error("No se pudo cargar la información.");
    }
    return await response.json();
}

async function loginAndGoToPanel() {
    const email = document.getElementById("loginEmail")?.value.trim() || "";
    const password = document.getElementById("loginPassword")?.value || "";

    if (!email || !password) {
        setLoginStatus("Debes escribir el correo y la contraseña.", "error");
        return;
    }

    const body = new URLSearchParams();
    body.append("username", email);
    body.append("password", password);

    const btn = document.getElementById("btnLogin");
    if (btn) btn.disabled = true;
    setLoginStatus("Validando credenciales...");

    try {
        const response = await fetch("/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "No se pudo iniciar sesión.");
        }

        setToken(data.access_token);
        setAuthUser(data.user);
        setLoginStatus(`Sesión iniciada correctamente como ${data.user.role}.`, "success");

        setTimeout(() => {
            window.location.href = "/panel";
        }, 350);
    } catch (error) {
        clearToken();
        clearAuthUser();
        setLoginStatus(error.message || "No se pudo iniciar sesión.", "error");
    } finally {
        if (btn) btn.disabled = false;
    }
}

function updatePanelUserUI(user) {
    const nameEl = document.getElementById("sessionUserName");
    const roleEl = document.getElementById("sessionUserRole");
    const emailEl = document.getElementById("sessionUserEmail");

    if (nameEl) nameEl.textContent = user?.full_name || "-";
    if (roleEl) roleEl.textContent = user?.role || "-";
    if (emailEl) emailEl.textContent = user?.email || "-";
}

function logout(redirect = true) {
    clearToken();
    clearAuthUser();
    if (redirect) {
        window.location.href = "/";
    }
}

function logoutToLogin() {
    logout(true);
}

async function requirePanelSession() {
    const token = getToken();
    const user = getAuthUser();

    if (!token || !user) {
        window.location.href = "/";
        return false;
    }

    try {
        const response = await authFetch("/auth/me");
        if (!response.ok) {
            throw new Error("No se pudo validar la sesión.");
        }

        const me = await response.json();
        setAuthUser(me);
        updatePanelUserUI(me);
        return true;
    } catch (error) {
        logout(true);
        return false;
    }
}

function setOptions(selectId, items, placeholder) {
    const select = document.getElementById(selectId);
    if (!select) return;

    select.innerHTML = "";

    const firstOption = document.createElement("option");
    firstOption.value = "";
    firstOption.textContent = placeholder;
    select.appendChild(firstOption);

    for (const item of items) {
        const option = document.createElement("option");
        if (typeof item === "string") {
            option.value = item;
            option.textContent = item;
        } else {
            option.value = item.id_estudiante;
            option.textContent = item.label;
        }
        select.appendChild(option);
    }
}

function getProgressElements() {
    return {
        overlay: document.getElementById("progressOverlay"),
        title: document.getElementById("progressTitle"),
        subtitle: document.getElementById("progressSubtitle"),
        bar: document.getElementById("progressBar"),
        percent: document.getElementById("progressPercent"),
        step: document.getElementById("progressStep"),
        note: document.getElementById("progressNote"),
        closeBtn: document.getElementById("progressCloseBtn"),
        spinner: document.getElementById("progressSpinner")
    };
}

function updateProgressUI(stepLabel = "") {
    const elements = getProgressElements();
    if (!elements.bar) return;
    elements.bar.style.width = `${progressValue}%`;
    elements.percent.textContent = `${Math.round(progressValue)}%`;
    if (stepLabel) {
        elements.step.textContent = stepLabel;
    }
}

function stopProgressAnimation() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
}

function showProgressModal(presetKey) {
    const preset = progressPresets[presetKey] || progressPresets["zip-complete"];
    const elements = getProgressElements();
    if (!elements.overlay) return;

    stopProgressAnimation();
    if (progressCompletionTimeout) {
        clearTimeout(progressCompletionTimeout);
        progressCompletionTimeout = null;
    }

    progressLocked = true;
    progressValue = 4;
    progressTarget = 8;

    document.body.classList.add("progress-lock");
    elements.overlay.classList.add("show");
    elements.overlay.setAttribute("aria-hidden", "false");
    elements.title.textContent = preset.title;
    elements.subtitle.textContent = preset.subtitle;
    elements.note.classList.remove("error");
    elements.note.textContent = "Este indicador acompaña el proceso mientras el sistema prepara la apertura o descarga.";
    elements.closeBtn.classList.remove("show");
    elements.spinner.style.display = "block";

    updateProgressUI("Inicializando proceso...");

    const steps = preset.steps || [];
    let currentStepIndex = 0;
    let nextAutomaticLabel = steps.length ? steps[0].label : "Procesando solicitud...";

    progressInterval = setInterval(() => {
        if (!progressLocked) {
            stopProgressAnimation();
            return;
        }

        if (currentStepIndex < steps.length && progressValue >= steps[currentStepIndex].percent - 2) {
            progressTarget = steps[currentStepIndex].percent;
            nextAutomaticLabel = steps[currentStepIndex].label;
            currentStepIndex += 1;
        }

        if (progressValue < progressTarget) {
            progressValue = Math.min(progressValue + 2, progressTarget);
            updateProgressUI(nextAutomaticLabel);
            return;
        }

        const lastSafeCap = 95;
        if (progressValue < lastSafeCap) {
            progressTarget = Math.min(progressValue + 4, lastSafeCap);
            progressValue = Math.min(progressValue + 1, progressTarget);
            updateProgressUI(nextAutomaticLabel);
        }
    }, 220);
}

function completeProgressModal(successMessage = "La solicitud fue enviada al navegador.") {
    const elements = getProgressElements();
    if (!elements.overlay) return;

    progressLocked = false;
    stopProgressAnimation();

    progressValue = 100;
    updateProgressUI("Proceso completado.");
    elements.note.classList.remove("error");
    elements.note.textContent = successMessage;
    elements.closeBtn.classList.add("show");
    elements.spinner.style.display = "none";

    progressCompletionTimeout = setTimeout(() => {
        closeProgressModal();
    }, 1100);
}

function failProgressModal(errorMessage = "No se pudo completar la operación.") {
    const elements = getProgressElements();
    if (!elements.overlay) return;

    progressLocked = false;
    stopProgressAnimation();

    elements.note.classList.add("error");
    elements.note.textContent = errorMessage;
    elements.step.textContent = "Ocurrió un problema.";
    elements.closeBtn.classList.add("show");
    elements.spinner.style.display = "none";
}

function closeProgressModal() {
    const elements = getProgressElements();
    if (!elements.overlay) return;

    stopProgressAnimation();

    if (progressCompletionTimeout) {
        clearTimeout(progressCompletionTimeout);
        progressCompletionTimeout = null;
    }

    progressLocked = false;
    progressValue = 0;
    progressTarget = 0;
    elements.overlay.classList.remove("show");
    elements.overlay.setAttribute("aria-hidden", "true");
    elements.bar.style.width = "0%";
    elements.percent.textContent = "0%";
    elements.step.textContent = "Inicializando proceso...";
    elements.note.classList.remove("error");
    elements.closeBtn.classList.remove("show");
    elements.spinner.style.display = "block";
    document.body.classList.remove("progress-lock");
}

function openHtmlInNewTab(htmlText) {
    const newWindow = window.open("", "_blank");
    if (!newWindow) {
        throw new Error("El navegador bloqueó la nueva pestaña.");
    }
    newWindow.document.open();
    newWindow.document.write(htmlText);
    newWindow.document.close();
}

function triggerBlobDownload(blob, filename) {
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = blobUrl;
    link.download = filename || "archivo";
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => window.URL.revokeObjectURL(blobUrl), 1500);
}

function getFileNameFromDisposition(disposition, fallbackName) {
    if (!disposition) return fallbackName;
    const match = disposition.match(/filename="?([^"]+)"?/i);
    return match ? match[1] : fallbackName;
}

function getSelectedStudentId() {
    const value = document.getElementById("studentSelect").value;
    if (!value) {
        throw new Error("Debes seleccionar un estudiante.");
    }
    return encodeURIComponent(value);
}

function getIndividualCycle() {
    return document.getElementById("studentCycle").value;
}

function getIndividualCourse() {
    return document.getElementById("studentCourse").value;
}

function getMassiveCycle() {
    return document.getElementById("massiveCycle").value;
}

function getMassiveCourse() {
    return document.getElementById("massiveCourse").value;
}

function getCycleLabel(cycle) {
    if (cycle === "Primer_Ciclo") return "Primer Ciclo";
    if (cycle === "Segundo_Ciclo") return "Segundo Ciclo";
    return cycle || "-";
}

function getSelectedStudentLabel() {
    const select = document.getElementById("studentSelect");
    if (!select || !select.value) return "";
    return select.options[select.selectedIndex]?.textContent || "";
}

function setIndividualButtonsDisabled(disabled) {
    document.getElementById("btnBulletinHtml").disabled = disabled;
    document.getElementById("btnBulletinPdf").disabled = disabled;
    document.getElementById("btnBlocksHtml").disabled = disabled;
    document.getElementById("btnBlocksPdf").disabled = disabled;
    document.getElementById("btnModulesHtml").disabled = disabled;
    document.getElementById("btnModulesPdf").disabled = disabled;
}

function setMassiveStatus(message, tone = "info") {
    const status = document.getElementById("massiveStatus");
    if (!status) return;
    status.innerHTML = message;
    status.classList.remove("success");
    if (tone === "success") {
        status.classList.add("success");
    }
}

function updateIndividualHelp() {
    const cycle = getIndividualCycle();
    const help = document.getElementById("individualHelp");
    if (!help) return;

    if (!cycle) {
        help.innerHTML = "<strong>Selecciona un ciclo:</strong> luego podrás elegir el curso y el estudiante.";
    } else if (cycle === "Primer_Ciclo") {
        help.innerHTML = "<strong>Primer Ciclo:</strong> boletín completo y boletín por bloques.";
    } else {
        help.innerHTML = "<strong>Segundo Ciclo:</strong> boletín completo, boletín de módulos y boletín por bloques + módulos.";
    }
}

function resetIndividualSelectors() {
    const cycle = document.getElementById("studentCycle");
    if (cycle) cycle.value = "";
    setOptions("studentCourse", [], "Seleccione un ciclo primero");
    setOptions("studentSelect", [], "Seleccione un curso primero");
    individualStudents = [];
    setIndividualButtonsDisabled(true);
    updateIndividualHelp();
}

function resetMassiveSelectors() {
    const cycle = document.getElementById("massiveCycle");
    if (cycle) cycle.value = "";
    setOptions("massiveCourse", [], "Seleccione un ciclo primero");
    updateMassiveButtons();
}

function saveLastQuery(data) {
    lastIndividualQuery = data;
    persistToStorage(STORAGE_KEYS.lastIndividualQuery, data);

    document.getElementById("lastQueryCycle").textContent = getCycleLabel(data.cycle);
    document.getElementById("lastQueryCourse").textContent = data.course || "-";
    document.getElementById("lastQueryStudent").textContent = data.studentLabel || data.studentId || "-";
    document.getElementById("lastQueryBox").style.display = "block";
}

function clearLastQuery() {
    lastIndividualQuery = null;
    removeFromStorage(STORAGE_KEYS.lastIndividualQuery);

    document.getElementById("lastQueryBox").style.display = "none";
    document.getElementById("lastQueryCycle").textContent = "-";
    document.getElementById("lastQueryCourse").textContent = "-";
    document.getElementById("lastQueryStudent").textContent = "-";
}

function restoreLastQuery() {
    const saved = loadFromStorage(STORAGE_KEYS.lastIndividualQuery);
    if (!saved) return;

    lastIndividualQuery = saved;
    document.getElementById("lastQueryCycle").textContent = getCycleLabel(saved.cycle);
    document.getElementById("lastQueryCourse").textContent = saved.course || "-";
    document.getElementById("lastQueryStudent").textContent = saved.studentLabel || saved.studentId || "-";
    document.getElementById("lastQueryBox").style.display = "block";
}

async function repeatLastQuery() {
    if (!lastIndividualQuery) return;
    try {
        await executeProtectedRoute(lastIndividualQuery.url, getPresetKeyForStudentRoute(lastIndividualQuery.routeSuffix));
    } catch (_) {}
}

function saveLastMassiveQuery(data) {
    lastMassiveQuery = data;
    persistToStorage(STORAGE_KEYS.lastMassiveQuery, data);

    document.getElementById("lastMassiveCycle").textContent = getCycleLabel(data.cycle);
    document.getElementById("lastMassiveCourse").textContent = data.course || "-";
    document.getElementById("lastMassiveType").textContent = data.typeLabel || "-";
    document.getElementById("lastMassiveQueryBox").style.display = "block";
}

function clearLastMassiveQuery() {
    lastMassiveQuery = null;
    removeFromStorage(STORAGE_KEYS.lastMassiveQuery);

    document.getElementById("lastMassiveQueryBox").style.display = "none";
    document.getElementById("lastMassiveCycle").textContent = "-";
    document.getElementById("lastMassiveCourse").textContent = "-";
    document.getElementById("lastMassiveType").textContent = "-";
    updateMassiveButtons();
}

function restoreLastMassiveQuery() {
    const saved = loadFromStorage(STORAGE_KEYS.lastMassiveQuery);
    if (!saved) return;

    lastMassiveQuery = saved;
    document.getElementById("lastMassiveCycle").textContent = getCycleLabel(saved.cycle);
    document.getElementById("lastMassiveCourse").textContent = saved.course || "-";
    document.getElementById("lastMassiveType").textContent = saved.typeLabel || "-";
    document.getElementById("lastMassiveQueryBox").style.display = "block";
}

async function repeatLastMassiveQuery() {
    if (!lastMassiveQuery) return;
    try {
        await executeProtectedRoute(lastMassiveQuery.url, getPresetKeyForMassiveType(lastMassiveQuery.typeLabel));
        setMassiveStatus(
            "Se volvió a abrir la <strong>última generación masiva</strong> guardada.",
            "success"
        );
    } catch (_) {}
}

async function loadStudentCourses() {
    const cycle = getIndividualCycle();
    setIndividualButtonsDisabled(true);
    setOptions("studentCourse", [], "Seleccione un ciclo primero");
    setOptions("studentSelect", [], "Seleccione un curso primero");
    updateIndividualHelp();

    if (!cycle) return;

    setOptions("studentCourse", [], "Cargando cursos...");

    try {
        const data = await fetchJson(`/students/options/courses?cycle=${encodeURIComponent(cycle)}`);
        setOptions("studentCourse", data.courses || [], "Seleccione un curso");
    } catch (error) {
        setOptions("studentCourse", [], "No se pudieron cargar los cursos");
    }
}

async function loadStudents() {
    const cycle = getIndividualCycle();
    const course = getIndividualCourse();
    setIndividualButtonsDisabled(true);

    if (!cycle) {
        setOptions("studentCourse", [], "Seleccione un ciclo primero");
        setOptions("studentSelect", [], "Seleccione un curso primero");
        return;
    }

    if (!course) {
        setOptions("studentSelect", [], "Seleccione un curso primero");
        return;
    }

    setOptions("studentSelect", [], "Cargando estudiantes...");

    try {
        const data = await fetchJson(`/students/options/students?cycle=${encodeURIComponent(cycle)}&course=${encodeURIComponent(course)}`);
        individualStudents = data.students || [];
        setOptions("studentSelect", individualStudents, "Seleccione un estudiante");
    } catch (error) {
        individualStudents = [];
        setOptions("studentSelect", [], "No se pudieron cargar los estudiantes");
    }
}

function updateStudentButtons() {
    const cycle = getIndividualCycle();
    const studentId = document.getElementById("studentSelect").value;
    const role = (getAuthUser()?.role || "").toLowerCase();
    const canGenerate = ["admin", "registro"].includes(role);
    const disabled = !studentId || !canGenerate;

    document.getElementById("btnBulletinHtml").disabled = disabled;
    document.getElementById("btnBulletinPdf").disabled = disabled;
    document.getElementById("btnBlocksHtml").disabled = disabled;
    document.getElementById("btnBlocksPdf").disabled = disabled;

    if (cycle === "Primer_Ciclo" || !cycle) {
        document.getElementById("btnModulesHtml").disabled = true;
        document.getElementById("btnModulesPdf").disabled = true;
    } else {
        document.getElementById("btnModulesHtml").disabled = disabled;
        document.getElementById("btnModulesPdf").disabled = disabled;
    }
}

function buildStudentRoute(routeSuffix) {
    const studentId = getSelectedStudentId();
    return `/students/${studentId}/${routeSuffix}`;
}

function getPresetKeyForStudentRoute(routeSuffix) {
    const map = {
        "bulletin-html": "bulletin-html",
        "bulletin-pdf": "bulletin-pdf",
        "bulletin-blocks-html": "bulletin-blocks-html",
        "bulletin-blocks-pdf": "bulletin-blocks-pdf",
        "second-cycle-blocks-html": "second-cycle-blocks-html",
        "second-cycle-blocks-pdf": "second-cycle-blocks-pdf",
        "modules-only-html": "modules-only-html",
        "modules-only-pdf": "modules-only-pdf"
    };
    return map[routeSuffix] || "bulletin-pdf";
}

function getPresetKeyForMassiveType(typeLabel) {
    const map = {
        "ZIP completo": "zip-complete",
        "ZIP por bloques": "zip-blocks",
        "ZIP solo módulos": "zip-modules",
        "ZIP bloques + módulos": "zip-blocks-modules"
    };
    return map[typeLabel] || "zip-complete";
}

async function executeProtectedRoute(url, presetKey) {
    showProgressModal(presetKey);

    try {
        const response = await authFetch(url);

        if (!response.ok) {
            let message = "No se pudo completar la operación.";
            try {
                const text = await response.text();
                if (text) {
                    message = text.replace(/<[^>]*>/g, "").trim() || message;
                }
            } catch (_) {}
            throw new Error(message);
        }

        const contentType = response.headers.get("content-type") || "";
        const disposition = response.headers.get("content-disposition") || "";

        if (contentType.includes("text/html")) {
            const html = await response.text();
            openHtmlInNewTab(html);
            completeProgressModal("La vista se abrió correctamente.");
            return;
        }

        const blob = await response.blob();

        if (contentType.includes("application/pdf")) {
            const filename = getFileNameFromDisposition(disposition, "boletin.pdf");
            triggerBlobDownload(blob, filename);
            completeProgressModal("El PDF fue enviado al navegador.");
            return;
        }

        if (contentType.includes("application/zip")) {
            const filename = getFileNameFromDisposition(disposition, "boletines.zip");
            triggerBlobDownload(blob, filename);
            completeProgressModal("El archivo ZIP fue enviado al navegador.");
            return;
        }

        throw new Error("Tipo de archivo no reconocido.");
    } catch (error) {
        failProgressModal(error.message || "No se pudo completar la operación.");
        throw error;
    }
}

async function openStudentRoute(routeSuffix) {
    try {
        const cycle = getIndividualCycle();
        const course = getIndividualCourse();
        const studentId = document.getElementById("studentSelect").value;
        const studentLabel = getSelectedStudentLabel();
        const url = buildStudentRoute(routeSuffix);
        const presetKey = getPresetKeyForStudentRoute(routeSuffix);

        saveLastQuery({
            cycle,
            course,
            studentId,
            studentLabel,
            routeSuffix,
            url
        });

        await executeProtectedRoute(url, presetKey);
        resetIndividualSelectors();
    } catch (_) {}
}

function openCycleSpecificHtml() {
    const cycle = getIndividualCycle();
    if (cycle === "Primer_Ciclo") {
        openStudentRoute("bulletin-blocks-html");
    } else {
        openStudentRoute("second-cycle-blocks-html");
    }
}

function openCycleSpecificPdf() {
    const cycle = getIndividualCycle();
    if (cycle === "Primer_Ciclo") {
        openStudentRoute("bulletin-blocks-pdf");
    } else {
        openStudentRoute("second-cycle-blocks-pdf");
    }
}

async function loadMassiveCourses() {
    const cycle = getMassiveCycle();
    setOptions("massiveCourse", [], "Seleccione un ciclo primero");

    if (!cycle) {
        updateMassiveButtons();
        return;
    }

    setOptions("massiveCourse", [], "Cargando cursos...");

    try {
        const data = await fetchJson(`/students/options/courses?cycle=${encodeURIComponent(cycle)}`);
        setOptions("massiveCourse", data.courses || [], "Seleccione un curso");
    } catch (error) {
        setOptions("massiveCourse", [], "No se pudieron cargar los cursos");
    }

    updateMassiveButtons();
}

function updateMassiveButtons() {
    const cycle = getMassiveCycle();
    const course = getMassiveCourse();
    const role = (getAuthUser()?.role || "").toLowerCase();
    const canGenerate = ["admin", "registro"].includes(role);
    const hasCourse = !!course && canGenerate;

    document.getElementById("btnZipComplete").disabled = !hasCourse;
    document.getElementById("btnZipBlocks").disabled = !(hasCourse && cycle === "Primer_Ciclo");
    document.getElementById("btnZipModules").disabled = !(hasCourse && cycle === "Segundo_Ciclo");
    document.getElementById("btnZipBlocksModules").disabled = !(hasCourse && cycle === "Segundo_Ciclo");

    if (!cycle) {
        setMassiveStatus("Selecciona un ciclo para continuar.");
    } else if (cycle === "Primer_Ciclo") {
        setMassiveStatus("Para <strong>Primer Ciclo</strong> están disponibles el ZIP completo y el ZIP por bloques.");
    } else {
        setMassiveStatus("Para <strong>Segundo Ciclo</strong> están disponibles el ZIP completo, el ZIP solo módulos y el ZIP bloques + módulos.");
    }
}

async function finalizeMassiveDownload(data, presetKey) {
    try {
        saveLastMassiveQuery(data);
        await executeProtectedRoute(data.url, presetKey);

        setMassiveStatus(
            `Descarga preparada: <strong>${data.typeLabel}</strong> del curso <strong>${data.course}</strong>.`,
            "success"
        );

        resetMassiveSelectors();
    } catch (_) {}
}

function openCompleteZip() {
    const cycle = getMassiveCycle();
    const course = getMassiveCourse();

    if (!course) {
        alert("Debes seleccionar un curso.");
        return;
    }

    const url = `/students/course/${encodeURIComponent(cycle)}/${encodeURIComponent(course)}/bulletins-zip`;

    finalizeMassiveDownload({
        cycle,
        course,
        typeLabel: "ZIP completo",
        url
    }, "zip-complete");
}

function openBlocksZip() {
    const course = getMassiveCourse();

    if (!course) {
        alert("Debes seleccionar un curso.");
        return;
    }

    const url = `/students/course/Primer_Ciclo/${encodeURIComponent(course)}/bulletins-blocks-zip`;

    finalizeMassiveDownload({
        cycle: "Primer_Ciclo",
        course,
        typeLabel: "ZIP por bloques",
        url
    }, "zip-blocks");
}

function openSecondCycleModulesZip() {
    const course = getMassiveCourse();

    if (!course) {
        alert("Debes seleccionar un curso.");
        return;
    }

    const url = `/students/course/Segundo_Ciclo/${encodeURIComponent(course)}/bulletins-modules-zip`;

    finalizeMassiveDownload({
        cycle: "Segundo_Ciclo",
        course,
        typeLabel: "ZIP solo módulos",
        url
    }, "zip-modules");
}

function openSecondCycleBlocksAndModulesZip() {
    const course = getMassiveCourse();

    if (!course) {
        alert("Debes seleccionar un curso.");
        return;
    }

    const url = `/students/course/Segundo_Ciclo/${encodeURIComponent(course)}/bulletins-blocks-and-modules-zip`;

    finalizeMassiveDownload({
        cycle: "Segundo_Ciclo",
        course,
        typeLabel: "ZIP bloques + módulos",
        url
    }, "zip-blocks-modules");
}

function initializeLoginPage() {
    const token = getToken();
    const user = getAuthUser();
    if (token && user) {
        window.location.href = "/panel";
    }
}

async function initializePanelPage() {
    const ok = await requirePanelSession();
    if (!ok) return;

    restoreLastQuery();
    restoreLastMassiveQuery();
    updateIndividualHelp();
    updateMassiveButtons();
}

document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("btnLogin")) {
        initializeLoginPage();
    }

    if (document.getElementById("studentCycle")) {
        initializePanelPage();
    }
});
