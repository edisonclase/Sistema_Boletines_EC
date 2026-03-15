from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CLASE Edutech"
    app_env: str = "development"
    app_debug: bool = True

    secret_key: str = "CHANGE_THIS_SECRET_KEY"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    url_primer_ciclo: str = ""
    url_segundo_ciclo: str = ""

    pdf_engine: str = "weasyprint"
    wkhtmltopdf_path: str = ""

    institution_name: str = "Politécnico Prof. José Mercedes Alvino - CEJOMA"
    institution_code: str = "14601"

    institution_logo: str = "app/pdf/assets/logo.png"
    institution_minerd_logo: str = "app/pdf/assets/minerd.png"

    # NUEVO
    institution_letterhead: str = "app/pdf/assets/membrete.png"

    institution_motto: str = ""
    institution_address: str = "Avenida Hispanoamericana, Santiago, República Dominicana"
    institution_email: str = "cejomal.2014@gmail.com"
    institution_phone: str = "809-570-6598"
    institution_academic_department: str = "Departamento de Registro y Control Académico"
    institution_director: str = "Zoilo A. Marrero Sirí"

    # FILOSOFIA DEL CENTRO
    institution_philosophy_title: str = "Filosofía Institucional"

    institution_philosophy_text: str = """
    El Politécnico Profesor José Mercedes Alvino tiene como propósito formar
    ciudadanos íntegros, críticos y comprometidos con el desarrollo social,
    científico y tecnológico del país.

    Promovemos una educación basada en valores, el respeto a la dignidad
    humana, el pensamiento lógico, creativo y crítico, así como la formación
    técnico profesional orientada al trabajo productivo y al servicio de la
    sociedad.

    Nuestra institución impulsa el desarrollo de competencias comunicativas,
    científicas, éticas y ciudadanas que permitan a nuestros estudiantes
    integrarse de manera responsable al mundo laboral y continuar su formación
    académica con éxito.
    """

    passing_grade: int = 70
    low_grade_highlight_color: str = "#FFF59D"

    bulletin_generated_by: str = "CLASE Edutech"
    bulletin_generated_role: str = "Coordinación de Registro y Control Académico"
    bulletin_author: str = "CLASE Edutech"

    philosophy_pdf_path: str = "app/pdf/assets/filosofia.pdf"

    school_year: str = "2025-2026"

    database_url: str = ""
    db_echo: bool = False

    security_password_min_length: int = 15
    security_max_login_attempts: int = 3
    security_account_lockout_minutes: int = 15
    security_password_reset_token_expire_minutes: int = 15

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()