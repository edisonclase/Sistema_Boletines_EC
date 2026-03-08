import pandas as pd
from urllib.error import HTTPError, URLError
from app.core.settings import settings


def load_primer_ciclo() -> pd.DataFrame:
    try:
        return pd.read_csv(settings.url_primer_ciclo)
    except HTTPError as e:
        raise RuntimeError(f"Error al leer Primer Ciclo: HTTP {e.code}")
    except URLError as e:
        raise RuntimeError(f"Error de conexión en Primer Ciclo: {e.reason}")


def load_segundo_ciclo() -> pd.DataFrame:
    try:
        return pd.read_csv(settings.url_segundo_ciclo)
    except HTTPError as e:
        raise RuntimeError(f"Error al leer Segundo Ciclo: HTTP {e.code}")
    except URLError as e:
        raise RuntimeError(f"Error de conexión en Segundo Ciclo: {e.reason}")