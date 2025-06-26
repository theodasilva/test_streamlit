import io

import pandas as pd
import streamlit as st

from core import auth_utils, data_processing, job_pdf_to_excel, read_file

# ──────────────────────────────────────────────────────────────────────────────
# 🔐 Sécurité
# ──────────────────────────────────────────────────────────────────────────────
auth_utils.require_roles(["Utilisateur", "Admin", "Superuser"])

# ──────────────────────────────────────────────────────────────────────────────
# 📄 Interface
# ──────────────────────────────────────────────────────────────────────────────
st.title("📄 Extraction de fiches métiers PDF ↔ Macro-compétences")

use_macro = st.checkbox("Avec macro compétences")

uploaded_file = st.file_uploader(
    "📄 Charger le PDF de la fiche métier",
    type="pdf",
)

macro_file = None
if use_macro:
    macro_file = st.file_uploader(
        "📊 Charger l’Excel de correspondance macro-compétences",
        type=["xlsx", "xls"],
    )

# ──────────────────────────────────────────────────────────────────────────────
# ▶️ Action
# ──────────────────────────────────────────────────────────────────────────────
if st.button("🚀 Lancer l'extraction"):
    if uploaded_file is None:
        st.error("Veuillez charger un fichier PDF.")
        st.stop()
    if use_macro and macro_file is None:
        st.error("Veuillez charger le fichier Excel de macro-compétences.")
        st.stop()

    try:
        with st.spinner("Extraction en cours…"):
            # 1) PDF ➜ DataFrame
            df_job = job_pdf_to_excel.job_pdf_to_excel(uploaded_file)

            # 2) Option macro ➜ même algo que l’exemple fourni
            if use_macro:
                df_macro = read_file.safe_read_excel(
                    uploaded_file=macro_file,
                    sheet_name="Macro-Compétences",
                    required_cols=["4 - Macro-compétence", "5 - Compétence"],
                    file_label="Excel macro-compétences",
                )

                df_joined = data_processing.add_macro_competence(
                    df_job,
                    df_macro
                )
                df_output = df_joined
                sheet_name = "Résultat"
            else:
                df_output = df_job
                sheet_name = "Fiche de poste"

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                df_output.to_excel(writer, index=False, sheet_name=sheet_name)
            buffer.seek(0)

        st.success("✅ Extraction terminée")

        st.download_button(
            label="📥 Télécharger le fichier Excel",
            data=buffer.getvalue(),
            file_name="Fiche_metier.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except Exception as e:
        st.error(f"Erreur : {e}")
