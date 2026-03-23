from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Aula Nova - Sistema de Gestión Escolar"
    app_env: str = "development"
    app_debug: bool = True

    secret_key: str = "CHANGE_THIS_SECRET_KEY"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    url_primer_ciclo: str = ""
    url_segundo_ciclo: str = ""

    pdf_engine: str = "wkhtmltopdf"
    wkhtmltopdf_path: str = ""

    institution_name: str = "Politécnico Prof. José Mercedes Alvino - CEJOMA"
    institution_code: str = "14601"

    institution_logo: str = "app/pdf/assets/logo.png"
    institution_minerd_logo: str = "app/pdf/assets/minerd.png"
    institution_letterhead: str = "app/pdf/assets/membrete.png"

    institution_motto: str = ""
    institution_address: str = "Avenida Hispanoamericana, Santiago, República Dominicana"
    institution_email: str = "cejomal.2014@gmail.com"
    institution_phone: str = "809-570-6598"
    institution_academic_department: str = "Departamento de Registro y Control Académico"
    institution_director: str = "Zoilo A. Marrero Sirí"

    institution_philosophy_title: str = "Filosofía Institucional"

    institution_philosophy_text: str = """
    En el Politécnico Profesor José Mercedes Alvino (CEJOMAL) Ofrecemos una formación técnico-profesional 
    basada en una educación integral de calidad, orientada al desarrollo de competencias y el fortalecimiento 
    de los valores humanos.
    
	Somos una institución de servicio comprometida con una educación cualificada que promueve la formación de 
    personas justas, capaces, dispuestas a enfrentar las exigencias empresariales e insertarse con éxito en estudios 
    superiores. 
    
	Creemos que la verdadera felicidad se alcanza actuando con imparcialidad, respeto a las leyes y a la dignidad humana; servir con amor, entrega y pasión, ha de ser nuestra esencia.
    """

    institution_mission_text: str = """
    Formar profesionales técnicos competentes, aptos para responder con eficiencia 
    a los nuevos desafíos del mundo laboral y del nivel superior; dispuestos a transformar 
    con amor y justicia su entorno social, cultural, científico y tecnológico.

    """

    institution_vision_text: str = """
	Ser un centro educativo modelo que ofrezca un servicio de la más alta calidad y 
    logre la formación de recursos humanos capacitados, respetuosos e identificados con su patria.
    """

    institution_values_text: str = """
    Amor, Justicia, Responsabilidad, Respeto, Honestidad, Solidaridad
    """

    passing_grade: int = 70
    low_grade_highlight_color: str = "#FFF59D"

    bulletin_generated_by: str = "Aula Nova"
    bulletin_generated_role: str = "Coordinación de Registro y Control Académico"
    bulletin_author: str = "Aula Nova"

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