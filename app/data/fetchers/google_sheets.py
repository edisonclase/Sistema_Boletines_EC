import pandas as pd
from urllib.error import HTTPError, URLError

from app.core.settings import settings


def _load_csv_from_url(url: str, label: str) -> pd.DataFrame:
    if not url:
        raise RuntimeError(f"No se configuró la URL para {label}.")

    try:
        return pd.read_csv(url)
    except HTTPError as e:
        raise RuntimeError(f"Error al leer {label}: HTTP {e.code}")
    except URLError as e:
        raise RuntimeError(f"Error de conexión en {label}: {e.reason}")


def load_primer_ciclo() -> pd.DataFrame:
    return _load_csv_from_url(
        settings.url_primer_ciclo,
        "Primer Ciclo",
    )


def load_segundo_ciclo() -> pd.DataFrame:
    return _load_csv_from_url(
        settings.url_segundo_ciclo,
        "Segundo Ciclo",
    )


def load_control_asistencia_completivo_primer_ciclo() -> pd.DataFrame:
    return _load_csv_from_url(
        settings.url_control_asistencia_completivo_primer_ciclo,
        "Control Asistencia Completivo Primer Ciclo",
    )


def load_control_asistencia_completivo_segundo_ciclo() -> pd.DataFrame:
    return _load_csv_from_url(
        settings.url_control_asistencia_completivo_segundo_ciclo,
        "Control Asistencia Completivo Segundo Ciclo",
    )