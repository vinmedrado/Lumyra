from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.paths import MAP_PDF
from repositories.database import log_event


def gerar_pdf_mesas(df: pd.DataFrame, output_path: str | Path = MAP_PDF, event_id: int | None = None) -> Path:
    output_path = Path(output_path)
    doc = SimpleDocTemplate(str(output_path), pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("TitleERP", parent=styles["Title"], alignment=TA_CENTER, fontSize=22, textColor=colors.HexColor("#111827"), spaceAfter=8)
    subtitle = ParagraphStyle("SubtitleERP", parent=styles["Normal"], alignment=TA_CENTER, fontSize=10, textColor=colors.HexColor("#6b7280"), spaceAfter=18)
    mesa_style = ParagraphStyle("Mesa", parent=styles["Heading2"], alignment=TA_CENTER, fontSize=13, textColor=colors.white)
    name_style = ParagraphStyle("Name", parent=styles["Normal"], fontSize=9, leading=12, textColor=colors.HexColor("#111827"))
    elements = [Paragraph("Mapa de Mesas", title), Paragraph("Lista de convidados organizada por mesa", subtitle), Spacer(1, 8)]
    if df.empty or "mesa_final" not in df.columns:
        elements.append(Paragraph("Nenhum convidado disponível.", styles["Normal"]))
        doc.build(elements)
        return output_path
    base = df[df["mesa_final"].notna()].copy()
    if base.empty:
        elements.append(Paragraph("Nenhuma mesa atribuída.", styles["Normal"]))
        doc.build(elements)
        return output_path
    def mesa_order(value):
        try:
            return int(str(value).split()[-1])
        except Exception:
            return 999
    for mesa in sorted(base["mesa_final"].unique(), key=mesa_order):
        mesa_df = base[base["mesa_final"] == mesa].sort_values(["grupo", "nome_original"], na_position="last")
        header = Table([[Paragraph(f"{mesa} • {len(mesa_df)} convidado(s)", mesa_style)]], colWidths=[520])
        header.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#8f5f34")), ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#8f5f34")), ("PADDING", (0, 0), (-1, -1), 8)]))
        elements.append(header)
        rows = [["Convidado", "Grupo", "Categoria"]]
        for _, row in mesa_df.iterrows():
            rows.append([Paragraph(str(row.get("nome_original") or row.get("nome") or "-"), name_style), Paragraph(str(row.get("grupo") or "-"), name_style), Paragraph(str(row.get("categoria") or "-"), name_style)])
        table = Table(rows, colWidths=[240, 160, 120], repeatRows=1)
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d1d5db")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("PADDING", (0, 0), (-1, -1), 6)]))
        elements.extend([table, Spacer(1, 14)])
    doc.build(elements)
    log_event("exportacao", "PDF de mesas gerado", detail=str(output_path), event_id=event_id)
    return output_path
