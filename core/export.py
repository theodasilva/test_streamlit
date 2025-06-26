import io
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from core import auth_utils


def excel_export(
    df: pd.DataFrame,
    sheet_name: str,
    source_job: str,
    categories_str=None,
    poids_sf=None,
    poids_se=None,
    poids_savoirs=None,
):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet(sheet_name)
        writer.sheets[sheet_name] = worksheet

        format_titre = workbook.add_format({"bold": True, "font_size": 14})
        format_soustitre = workbook.add_format({"italic": True})

        # Écriture du titre et des dimensions choisies
        worksheet.write("A1", f"Métier de départ : {source_job}", format_titre)
        worksheet.write(
            "A2",
            f"Dimensions sélectionnées : {categories_str}",
            format_soustitre,
        )
        # Définir les pondérations appliquées (selon sélection)
        pond_list = []
        if poids_sf is None:
            pond_list.append(f"Savoir-faire = {poids_sf}%")
        if poids_se is None:
            pond_list.append(f"Savoir-être professionnels = {poids_se}%")
        if poids_savoirs is None:
            pond_list.append(f"Savoirs = {poids_savoirs}%")

        pond_str = " / ".join(pond_list)
        worksheet.write("A3", f"Pondérations appliquées : {pond_str}", format_soustitre)

        date_export = datetime.now().strftime("%d/%m/%Y à %Hh%M")
        worksheet.write("A4", f"Date d’export : {date_export}", format_soustitre)

        # Export des données à partir de la ligne 6 (index 5)
        df.to_excel(writer, index=False, startrow=5, sheet_name=sheet_name)

        # Ajustement automatique de la largeur des colonnes
        for i, col in enumerate(df.columns):
            column_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_len)

    return buffer.getvalue()
