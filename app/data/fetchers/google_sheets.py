import pandas as pd
from app.core.settings import settings


def load_primer_ciclo() -> pd.DataFrame:
    return pd.read_csv(settings.url_primer_ciclo)


def load_segundo_ciclo() -> pd.DataFrame:
    return pd.read_csv(settings.url_segundo_ciclo)