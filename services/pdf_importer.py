import json
from pathlib import Path

import pandas as pd

from core.paths import DATA_DIR, EXTRACTED_TXT, GUESTS_JSON, PDF_LIST, ensure_dirs
from repositories.database import create_import, log_event, replace_guests
from scripts.extrair_dados import extrair_convidados, gerar_resumo, ler_pdf, salvar_txt_conferencia


def process_pdf(uploaded_file=None, pdf_path: str | Path | None = None, event_id: int | None = None) -> dict:
    ensure_dirs()
    source_name = "lista.pdf"
    if uploaded_file is not None:
        source_name = getattr(uploaded_file, "name", "lista.pdf")
        with open(PDF_LIST, "wb") as f:
            f.write(uploaded_file.getbuffer())
        caminho = PDF_LIST
    elif pdf_path:
        caminho = Path(pdf_path)
    else:
        caminho = PDF_LIST

    texto = ler_pdf(caminho)
    convidados = extrair_convidados(texto)
    resumo = gerar_resumo(convidados)
    payload = {"resumo": resumo, "convidados": convidados}

    with open(GUESTS_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, allow_nan=False)

    salvar_txt_conferencia(convidados, EXTRACTED_TXT)
    replace_guests(pd.DataFrame(convidados), event_id=event_id)
    create_import(event_id, source_name, len(convidados), "success", "PDF importado e persistido no SQLite")
    log_event("importacao_pdf", f"PDF importado: {len(convidados)} convidados", detail=source_name, event_id=event_id)
    return payload
