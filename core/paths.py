from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
DB_PATH = DATA_DIR / "event_erp.sqlite3"
GUESTS_JSON = DATA_DIR / "base_convidados.json"
TABLES_CSV = DATA_DIR / "relatorio_mesas.csv"
PDF_LIST = DATA_DIR / "lista.pdf"
EXTRACTED_TXT = DATA_DIR / "nomes_extraidos.txt"
ASSESSORIA_CONTEXT = DATA_DIR / "assessoria_contexto.json"
MAP_PDF = DATA_DIR / "mapa_mesas.pdf"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
