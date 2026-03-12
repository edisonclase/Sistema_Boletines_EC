from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])


@router.get("/", response_class=HTMLResponse)
def home():
    html = """
<!DOCTYPE html>
<html lang="es">
<head>

<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>

<title>CLASE EducTech</title>

<style>

*{
box-sizing:border-box;
}

:root{

--bg:#F1F5F9;
--panel:#FFFFFF;
--panel-soft:#F8FAFF;

--text:#1E293B;
--muted:#64748B;

--primary:#6366F1;
--primary-2:#818CF8;
--hover:#4F46E5;

--accent:#0F172A;

--line:#D9E2F1;
--line-strong:#C7D2FE;

--shadow:0 18px 45px rgba(79,70,229,0.12);

--radius:20px;

--success-bg:rgba(15,118,110,0.10);
--success-border:rgba(15,118,110,0.25);
--success-text:#0F766E;

}

body{

margin:0;

font-family:Arial,Helvetica,sans-serif;

background:

radial-gradient(circle at top left, rgba(99,102,241,0.16) 0%, transparent 32%),

radial-gradient(circle at top right, rgba(129,140,248,0.16) 0%, transparent 28%),

linear-gradient(180deg,#F8FAFC 0%,var(--bg) 100%);

color:var(--text);

}

.wrapper{

min-height:100vh;

padding:28px;

display:flex;

align-items:center;

justify-content:center;

}

.shell{

width:100%;
max-width:1320px;

}

.hero{

text-align:center;
margin-bottom:24px;

}

.hero-badge{

display:inline-block;

padding:8px 14px;

border-radius:999px;

background:rgba(99,102,241,0.12);

color:var(--hover);

font-size:12px;
font-weight:bold;

letter-spacing:0.3px;

margin-bottom:14px;

border:1px solid rgba(99,102,241,0.20);

}

.hero-title{

margin:0;

font-size:40px;
font-weight:800;

color:var(--accent);

letter-spacing:-0.5px;

}

.hero-subtitle{

margin:10px auto 0 auto;

max-width:860px;

font-size:16px;

color:var(--muted);

line-height:1.55;

}

.grid{

display:grid;

grid-template-columns:1.1fr 1fr;

gap:24px;

}

.card{

background:var(--panel);

border:1px solid var(--line);

border-radius:var(--radius);

box-shadow:var(--shadow);

padding:26px;

}

.card-header{

margin-bottom:18px;

}

.card-kicker{

font-size:12px;

font-weight:bold;

color:var(--hover);

text-transform:uppercase;

letter-spacing:0.7px;

margin-bottom:6px;

}

.card-title{

margin:0;

font-size:24px;

color:var(--accent);

}

.card-subtitle{

margin:8px 0 0 0;

color:var(--muted);

font-size:14px;

line-height:1.5;

}

.section{

border:1px solid var(--line);

background:var(--panel-soft);

border-radius:16px;

padding:18px;

margin-top:18px;

}

.section-title{

margin:0 0 14px 0;

font-size:15px;

font-weight:bold;

color:var(--accent);

}

.form-group{

margin-bottom:15px;

}

label{

display:block;

font-weight:bold;

margin-bottom:8px;

font-size:14px;

color:var(--text);

}

select{

width:100%;

padding:13px 14px;

border:1px solid #CBD5E1;

border-radius:12px;

font-size:15px;

outline:none;

background:#FFFFFF;

color:var(--text);

}

.buttons-grid{

display:grid;

grid-template-columns:repeat(2,1fr);

gap:12px;

margin-top:8px;

}

button{

border:none;

border-radius:14px;

padding:15px 14px;

font-size:14px;

font-weight:bold;

cursor:pointer;

min-height:58px;

}

button:disabled{

opacity:0.55;

cursor:not-allowed;

}

.btn-primary{background:var(--primary);color:white;}

.btn-secondary{background:var(--primary-2);color:white;}

.btn-soft{

background:rgba(99,102,241,0.10);

color:var(--hover);

border:1px solid rgba(99,102,241,0.22);

}

.btn-dark{background:#1E293B;color:white;}

.btn-success{background:#0F766E;color:white;}

.btn-violet{background:#7C3AED;color:white;}

.btn-outline{

background:#FFFFFF;

color:var(--accent);

border:1px solid #CBD5E1;

}

.status-box{

margin-top:14px;

padding:12px 14px;

border-radius:14px;

background:rgba(99,102,241,0.10);

border:1px solid rgba(99,102,241,0.18);

font-size:13px;

color:var(--hover);

line-height:1.5;

}

.status-box.success{

background:var(--success-bg);

border-color:var(--success-border);

color:var(--success-text);

}

.footer{

margin-top:18px;

text-align:center;

font-size:12px;

color:var(--muted);

}

.footer strong{

color:var(--accent);

}

</style>

</head>

<body>

<div class="wrapper">

<div class="shell">

<div class="hero">

<div class="hero-badge">Plataforma de Seguimiento Académico</div>

<h1 class="hero-title">CLASE EducTech</h1>

<p class="hero-subtitle">

Sistema de generación automatizada de boletines académicos.

</p>

</div>

<div class="grid">

<div class="card">

<div class="card-header">

<div class="card-kicker">Modo individual</div>

<h2 class="card-title">Boletines por estudiante</h2>

<p class="card-subtitle">

Selecciona ciclo, curso y estudiante.

</p>

</div>

<div class="section">

<div class="form-group">

<label for="studentCycle">Ciclo</label>

<select id="studentCycle" onchange="loadStudentCourses()">

<option value="">Seleccione un ciclo</option>

<option value="Primer_Ciclo">Primer Ciclo</option>

<option value="Segundo_Ciclo">Segundo Ciclo</option>

</select>

</div>

<div class="form-group">

<label for="studentCourse">Curso</label>

<select id="studentCourse" onchange="loadStudents()">

<option value="">Seleccione ciclo primero</option>

</select>

</div>

<div class="form-group">

<label for="studentSelect">Estudiante</label>

<select id="studentSelect" onchange="updateStudentButtons()">

<option value="">Seleccione curso primero</option>

</select>

</div>

<div class="buttons-grid">

<button id="btnBulletinPdf" class="btn-primary" onclick="openStudentRoute('bulletin-pdf')" disabled>

Descargar boletín completo

</button>

<button id="btnBlocksPdf" class="btn-dark" onclick="openCycleSpecificPdf()" disabled>

Boletín por bloques

</button>

<button id="btnModulesPdf" class="btn-success" onclick="openStudentRoute('modules-only-pdf')" disabled>

Boletín módulos

</button>

<button id="btnBlocksModulesPdf" class="btn-violet" onclick="openStudentRoute('second-cycle-blocks-pdf')" disabled>

Bloques + módulos

</button>

</div>

</div>

</div>

<div class="card">

<div class="card-header">

<div class="card-kicker">Modo masivo</div>

<h2 class="card-title">Boletines por curso</h2>

<p class="card-subtitle">

Genera todos los boletines del curso en un solo ZIP.

</p>

</div>

<div class="section">

<div class="form-group">

<label for="massiveCycle">Ciclo</label>

<select id="massiveCycle" onchange="loadMassiveCourses()">

<option value="">Seleccione un ciclo</option>

<option value="Primer_Ciclo">Primer Ciclo</option>

<option value="Segundo_Ciclo">Segundo Ciclo</option>

</select>

</div>

<div class="form-group">

<label for="massiveCourse">Curso</label>

<select id="massiveCourse" onchange="updateMassiveButtons()">

<option value="">Seleccione ciclo primero</option>

</select>

</div>

<div class="buttons-grid">

<button id="btnZipComplete" class="btn-primary" onclick="openCompleteZip()" disabled>

ZIP completo

</button>

<button id="btnZipBlocks" class="btn-outline" onclick="openBlocksZip()" disabled>

ZIP por bloques

</button>

<button id="btnZipModules" class="btn-dark" onclick="openSecondCycleModulesZip()" disabled>

ZIP módulos

</button>

<button id="btnZipBlocksModules" class="btn-violet" onclick="openSecondCycleBlocksAndModulesZip()" disabled>

ZIP bloques + módulos

</button>

</div>

<div class="status-box" id="massiveStatus">

Selecciona ciclo para continuar.

</div>

</div>

</div>

</div>

<div class="footer">

Panel inicial del sistema · futura capa de acceso por <strong>roles</strong>

</div>

</div>

</div>

</body>
</html>
"""

    return HTMLResponse(content=html)