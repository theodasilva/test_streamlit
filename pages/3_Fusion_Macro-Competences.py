import io

import pandas as pd
import streamlit as st

from core import auth_utils, data_processing, read_file

# ──────────────────────────────────────────────────────────────────────────────
# 🔐 Sécurité
# ──────────────────────────────────────────────────────────────────────────────
auth_utils.require_roles(["Utilisateur", "Admin", "Superuser"])

# ──────────────────────────────────────────────────────────────────────────────
# 🏷️ Titre & explications
# ──────────────────────────────────────────────────────────────────────────────
st.title("🔗 Fusion compétences ↔ macro-compétences")

st.markdown(
    """
---
Cette page vous permet de **joindre** un fichier Excel de compétences et un
fichier Excel de macro-compétences pour obtenir, en sortie, le fichier
« Compétences » enrichi d’une colonne **Macro-compétence**.

### Étapes
1. Charger le fichier **Compétences** (Avec une colonne `Compétences`)
2. Charger le fichier **Macro-compétences** (Avec un colonne `5 - Compétence` et `4 - Macro-compétence`)
3. Cliquer sur **🚀 Lancer la fusion**
---
"""
)

# ──────────────────────────────────────────────────────────────────────────────
# 📥 Uploads
# ──────────────────────────────────────────────────────────────────────────────
skills_file = st.file_uploader("📄 Fichier Excel compétences", type=["xlsx", "xls"])
macro_file = st.file_uploader("📊 Fichier Excel macro-compétences", type=["xlsx", "xls"])


if st.button("🚀 Lancer la fusion"):
    if skills_file is None or macro_file is None:
        st.error("Veuillez charger **les deux** fichiers Excel.")
        st.stop()

    try:
        with st.spinner("Fusion en cours…"):
            # Lecture sécurisée des deux fichiers
            df_skills = read_file.safe_read_excel(
                uploaded_file=skills_file,
                sheet_name=0,
                required_cols=["Compétences"],
                file_label="Excel compétences",
            )
            df_macro = read_file.safe_read_excel(
                uploaded_file=macro_file,
                sheet_name="Macro-Compétences",
                required_cols=["4 - Macro-compétence", "5 - Compétence"],
                file_label="Excel macro-compétences",
            )
            df_skill_macro = data_processing.add_macro_competence(
                df_skills,
                df_macro
            )

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                df_skill_macro.to_excel(writer, index=False, sheet_name="Résultat")
            buffer.seek(0)

        st.success("✅ Fusion terminée !")

        # Bouton de téléchargement
        st.download_button(
            label="📥 Télécharger le fichier fusionné",
            data=buffer.getvalue(),
            file_name="Skills_with_macro_competence.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except Exception as e:
        st.error(f"Erreur lors de la fusion : {e}")
