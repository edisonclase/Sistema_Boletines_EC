from fastapi import APIRouter
from app.data.fetchers.google_sheets import load_primer_ciclo, load_segundo_ciclo

router = APIRouter(prefix="/data-sources", tags=["data-sources"])


@router.get("/health")
def data_sources_health():
    result = {
        "primer_ciclo": None,
        "segundo_ciclo": None,
    }

    try:
        primer = load_primer_ciclo()
        result["primer_ciclo"] = {
            "status": "ok",
            "rows": len(primer),
            "columns_count": len(primer.columns),
            "first_10_columns": primer.columns[:10].tolist(),
        }
    except Exception as e:
        result["primer_ciclo"] = {
            "status": "error",
            "detail": str(e),
        }

    try:
        segundo = load_segundo_ciclo()
        result["segundo_ciclo"] = {
            "status": "ok",
            "rows": len(segundo),
            "columns_count": len(segundo.columns),
            "first_10_columns": segundo.columns[:10].tolist(),
        }
    except Exception as e:
        result["segundo_ciclo"] = {
            "status": "error",
            "detail": str(e),
        }

    return result