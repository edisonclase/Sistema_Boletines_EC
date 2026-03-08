from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Sistema_Boletines_EC"
    app_env: str = "development"
    app_debug: bool = True

    secret_key: str = "CHANGE_THIS_SECRET_KEY"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    url_primer_ciclo: str = ""
    url_segundo_ciclo: str = ""

    pdf_engine: str = "wkhtmltopdf"
    wkhtmltopdf_path: str = ""

    institution_name: str = "Politécnico Profesor José Mercedes Alvino"
    institution_code: str = "14601"
    institution_logo: str = "app/pdf/assets/logo.jpg"
    institution_minerd_logo: str = "app/pdf/assets/minerd.png"
    institution_motto: str = ""
    institution_address: str = "Avenida Hispanoamericana, Santiago, República Dominicana"
    institution_email: str = "cejomal.2014@gmail.com"
    institution_phone: str = "809-570-6598"
    institution_academic_department: str = "Departamento de Registro y Control Académico"
    institution_director: str = "Zoilo A. Marrero Sirí"

    passing_grade: int = 70
    low_grade_highlight_color: str = "#FFF59D"

    bulletin_generated_by: str = "Sistema de Boletines ECS"
    bulletin_generated_role: str = "Coordinación de Registro y Control Académico"
    bulletin_author: str = "ECS"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()