import io
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from core import auth_utils, read_file

# ------------------------------
# 🔐 Sécurité : accès par mot de passe
# ------------------------------

auth_utils.require_auth()

# ------------------------------
# TITRE & UPLOAD
# ------------------------------
st.title("🧭 Outil de passerelles métiers")

st.markdown(
    """
---
👋 Bienvenue dans l'outil de passerelles métiers !

Cet outil vous permet d'identifier les **passerelles métiers possibles** entre les métiers d'un client (ex : secteur pharmaceutique) et ceux du référentiel ROME, sur la base des **macro-compétences partagées**.

---

### 🧩 Étapes à suivre :
1. **Charger les deux fichiers Excel**.
2. **Choisir le type de passerelle** (entrante ou sortante).
3. **Sélectionner les dimensions de compétences** à prendre en compte ainsi que leur **pondération**.
4. **Filtrer par secteur** si besoin, puis **choisir un métier de départ**.
5. 📊 Obtenez les passerelles les plus proches et **téléchargez les résultats**.
6. (Facultatif) 📦 Générez **l'intégralité des passerelles** sans aucun filtre.

---
"""
)

st.markdown(
    "###\n**📚 1. Charger le fichier des compétences ROME (MACRO-COMPETENCES ROME.xlsx)**"
)
skills_file = st.file_uploader(
    "Fichier de compétences", type="xlsx", key="competences", label_visibility="hidden"
)
st.markdown("###\n**🏢 2. Charger le fichier des métiers client**")
st.markdown(
    """
<small>ℹ️ Le fichier métiers client doit contenir **une colonne intitulée `Code ROME`**, avec un code ROME par ligne (ex : M1805).<br>
Autres colonnes (intitulé, descriptions…) facultatives.</small>
""",
    unsafe_allow_html=True,
)
client_file = st.file_uploader(
    "Fichier client", type="xlsx", key="client", label_visibility="hidden"
)

if skills_file and client_file:
    # ------------------------------
    # CHOIX DU MODE ET DES OPTIONS
    # ------------------------------
    st.markdown("###\n**🔍 3. Type de passerelle**")
    mode = st.radio(
        "Mode",
        ["Passerelle entrante", "Passerelle sortante"],
        label_visibility="hidden",
    )

    st.markdown("###\n**🎯 4. Catégories de compétences**")
    col1, col2, col3 = st.columns(3)
    with col1:
        with_know_how = st.checkbox("Savoir-faire", value=True)
    with col2:
        with_professional_skills = st.checkbox("Savoir-être professionnels", value=True)
    with col3:
        with_knowledge = st.checkbox("Savoirs", value=True)

    st.markdown(
        "###\n**⚖️ 5. Pondération des catégories de compétences (total = 100%)**"
    )
    col_w1, col_w2, col_w3 = st.columns(3)

    with col_w1:
        know_how_weight = st.number_input(
            "🛠️ Savoir-faire (%)",
            min_value=0,
            max_value=100,
            value=20,
            step=5,
            disabled=not with_know_how,
        )

    with col_w2:
        professional_skills_weight = st.number_input(
            "🤝 Savoir-être (%)",
            min_value=0,
            max_value=100,
            value=20,
            step=5,
            disabled=not with_professional_skills,
        )

    with col_w3:
        knowledge_weight = st.number_input(
            "📚 Savoirs (%)",
            min_value=0,
            max_value=100,
            value=60,
            step=5,
            disabled=not with_knowledge,
        )

    # Calcul dynamique selon cases cochées
    total_weight = 0
    if with_know_how:
        total_weight += know_how_weight
    if with_professional_skills:
        total_weight += professional_skills_weight
    if with_knowledge:
        total_weight += knowledge_weight

    if total_weight != 100:
        st.error(
            "❌ La somme des pondérations doit être égale à 100% pour les catégories sélectionnées."
        )
        st.stop()

    # Liste des catégories sélectionnées
    selected_categories = []
    if with_know_how:
        selected_categories.append("Savoir-faire")
    if with_professional_skills:
        selected_categories.append("Savoir-être professionnels")
    if with_knowledge:
        selected_categories.append("Savoirs")

    if not selected_categories:
        st.warning(
            "⚠️ Veuillez sélectionner au moins une catégorie de compétence (savoir-faire, savoir-être professionnels ou savoirs)."
        )
        st.stop()

    # Chargement unique depuis l'onglet centralisé
    raw_skills_df = read_file.safe_read_excel(
        skills_file,
        sheet_name="Macro-Compétences",
        required_cols=["Code Métier", "Intitulé", "Macro Compétence", "Catégorie"],
        file_label="compétences ROME",
    )

    skills_df = raw_skills_df[
        raw_skills_df["Catégorie"].isin(selected_categories)
    ].copy()
    skills_df = skills_df.dropna(
        subset=["Code Métier", "Intitulé", "Macro Compétence"]
    )  # Nettoyage

    # Chargement des métiers client
    client_df = read_file.safe_read_excel(
        client_file,
        sheet_name=0,  # first sheet
        required_cols=["Code ROME"],
        file_label="métiers client",
    )
    client_codes = client_df["Code ROME"].dropna().unique()

    # Définir métiers de départ et d'arrivée selon le mode
    if mode == "Passerelle entrante":
        start_df = skills_df.copy()  # Tous les métiers (ROME + client)
        target_df = skills_df[skills_df["Code Métier"].isin(client_codes)]
    else:
        start_df = skills_df[skills_df["Code Métier"].isin(client_codes)]
        target_df = skills_df[~skills_df["Code Métier"].isin(client_codes)]

    # Liste des métiers de départ disponibles
    start_jobs = (
        start_df[["Code Métier", "Intitulé"]].drop_duplicates().sort_values("Intitulé")
    )

    # Dictionnaire de correspondance lettre → secteur
    sectors = {
        "A": "Agriculture et Pêche, Espaces naturels et Espaces verts, Soins aux animaux",
        "B": "Arts et Façonnage d'ouvrages d'art",
        "C": "Banque, Assurance, Immobilier",
        "D": "Commerce, Vente et Grande distribution",
        "E": "Communication, Média et Multimédia",
        "F": "Construction, Bâtiment et Travaux publics",
        "G": "Hôtellerie-Restauration, Tourisme, Loisirs et Animation",
        "H": "Industrie",
        "I": "Installation et Maintenance",
        "J": "Santé",
        "K": "Services à la personne et à la collectivité",
        "L": "Spectacle",
        "M": "Support à l'entreprise",
        "N": "Transport et Logistique",
    }

    # Lettres présentes dans les métiers de départ
    available_letters = start_df["Code Métier"].str[0].unique()
    available_sectors = {
        letter: sectors[letter] for letter in available_letters if letter in sectors
    }

    # Construction des options de filtre secteur
    sector_options = ["Tous les secteurs"] + [
        f"{letter} - {sectors[letter]}" for letter in sorted(available_sectors)
    ]

    # Initialisation du filtre secteur en session_state
    if "selected_sector" not in st.session_state:
        st.session_state["selected_sector"] = "Tous les secteurs"

    # Menu déroulant secteur
    st.markdown("###\n**🗂️ 6. Secteur d'activité**")
    selected_sector = st.selectbox(
        "Secteur d'activité",
        options=sector_options,
        index=sector_options.index(st.session_state["selected_sector"]),
        key="selected_sector",
        label_visibility="hidden",
    )

    # Filtrage des métiers de départ si un secteur est sélectionné
    if selected_sector == "Tous les secteurs":
        filtered_jobs = start_jobs.copy()
    else:
        selected_letter = selected_sector.split(" - ")[0]
        filtered_jobs = start_jobs[
            start_jobs["Code Métier"].str.startswith(selected_letter)
        ]

    # Liste des métiers de départ disponibles
    st.markdown("###\n**👤 7. Métier de départ**")
    filtered_jobs["Display"] = (
        filtered_jobs["Code Métier"] + " - " + filtered_jobs["Intitulé"]
    )
    display_choice = st.selectbox(
        " Métier de départ",
        options=filtered_jobs["Display"].tolist(),
        label_visibility="hidden",
    )
    selected_code = filtered_jobs[filtered_jobs["Display"] == display_choice][
        "Code Métier"
    ].values[0]
    selected_job = filtered_jobs[filtered_jobs["Code Métier"] == selected_code][
        "Intitulé"
    ].values[0]

    # Code métier sélectionné
    selected_code = start_jobs[start_jobs["Intitulé"] == selected_job][
        "Code Métier"
    ].values[0]

    # Macro-compétences du métier sélectionné
    selected_skills = set(
        start_df[start_df["Code Métier"] == selected_code]["Macro Compétence"].dropna()
    )

    # Calcul des similarités avec les métiers d'arrivée
    result_rows = []
    start_letter = selected_code[0]

    for job_code, group in target_df.groupby("Code Métier"):
        if job_code == selected_code:
            continue  # On saute si c'est le même métier
        title = group["Intitulé"].iloc[0]
        job_skills = set(group["Macro Compétence"].dropna())
        intersection = selected_skills & job_skills
        score = len(intersection)
        if score > 0:
            for skill in intersection:
                # On récupère la catégorie depuis le target_df
                category = group[group["Macro Compétence"] == skill]["Catégorie"].iloc[
                    0
                ]
                # Appliquer le poids en fonction de la catégorie
                if category == "Savoir-faire":
                    weight = know_how_weight
                elif category == "Savoir-être professionnels":
                    weight = professional_skills_weight
                elif category == "Savoirs":
                    weight = knowledge_weight
                else:
                    weight = 0  # sécurité

                bonus = 1.25 if job_code.startswith(start_letter) else 1
                weighted_score_final = (score * weight / 100) * bonus

                result_rows.append(
                    {
                        "Code Métier": job_code,
                        "Intitulé": title,
                        "Nb de passerelles communes": score,
                        "Score pondéré": score * weight / 100,
                        "Catégorie": category,
                        "Compétence commune": skill,
                    }
                )

    if result_rows:
        full_results_df = pd.DataFrame(result_rows)

        # Affichage top 20 pour l'écran
        top_jobs = (
            full_results_df.groupby(["Code Métier", "Intitulé"])
            .agg({"Score pondéré": "sum", "Compétence commune": "count"})
            .reset_index()
            .rename(
                columns={
                    "Score pondéré": "Score pondéré total",
                    "Compétence commune": "Nombre de compétences partagées",
                }
            )
            .sort_values("Score pondéré total", ascending=False)
            .head(20)
        )
        st.markdown("###\n### 🌟 Top 20 des passerelles proposées :")
        st.dataframe(top_jobs, hide_index=True)

        def export_top20_filtered_passerelles(top_df, full_df):
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                workbook = writer.book
                title_format = workbook.add_format({"bold": True, "font_size": 14})
                subtitle_format = workbook.add_format({"italic": True})

                # Sheet 1: Top 20 métiers
                sheet1 = "Top 20 métiers"
                writer.sheets[sheet1] = workbook.add_worksheet(sheet1)
                worksheet1 = writer.sheets[sheet1]

                worksheet1.write(
                    "A1", f"Métier de départ : {selected_job}", title_format
                )
                worksheet1.write(
                    "A2",
                    f"Dimensions sélectionnées : {categories_str}",
                    subtitle_format,
                )

                weight_list = []
                if with_know_how:
                    weight_list.append(f"Savoir-faire = {know_how_weight}%")
                if with_professional_skills:
                    weight_list.append(
                        f"Savoir-être professionnels = {professional_skills_weight}%"
                    )
                if with_knowledge:
                    weight_list.append(f"Savoirs = {knowledge_weight}%")

                worksheet1.write(
                    "A3",
                    "Pondérations appliquées : " + " / ".join(weight_list),
                    subtitle_format,
                )
                worksheet1.write(
                    "A4",
                    "Date d'export : " + datetime.now().strftime("%d/%m/%Y à %Hh%M"),
                    subtitle_format,
                )

                top_df.to_excel(writer, sheet_name=sheet1, startrow=5, index=False)
                for i, col in enumerate(top_df.columns):
                    max_len = max(top_df[col].astype(str).map(len).max(), len(col)) + 2
                    worksheet1.set_column(i, i, max_len)

                # Sheet 2: Passerelles pour Top 20
                sheet2 = "Passerelles Top 20"
                writer.sheets[sheet2] = workbook.add_worksheet(sheet2)
                worksheet2 = writer.sheets[sheet2]

                worksheet2.write(
                    "A1", f"Métier de départ : {selected_job}", title_format
                )
                worksheet2.write(
                    "A2",
                    f"Dimensions sélectionnées : {categories_str}",
                    subtitle_format,
                )
                worksheet2.write(
                    "A3",
                    "Pondérations appliquées : " + " / ".join(weight_list),
                    subtitle_format,
                )
                worksheet2.write(
                    "A4",
                    "Date d'export : " + datetime.now().strftime("%d/%m/%Y à %Hh%M"),
                    subtitle_format,
                )

                top_codes = top_df["Code Métier"].unique()
                top_filtered_df = filtered_df[
                    filtered_df["Code Métier"].isin(top_codes)
                ]

                top_filtered_df.to_excel(
                    writer, sheet_name=sheet2, startrow=5, index=False
                )
                for i, col in enumerate(top_filtered_df.columns):
                    max_len = (
                        max(top_filtered_df[col].astype(str).map(len).max(), len(col))
                        + 2
                    )
                    worksheet2.set_column(i, i, max_len)

            return buffer.getvalue()

        # Filtres et formats Excel
        filtered_df = full_results_df.copy()
        categories_str = ", ".join(selected_categories)

        # Ajouter le score pondéré total dans filtered_df
        scores_df = (
            filtered_df.groupby(["Code Métier", "Intitulé"])["Score pondéré"]
            .sum()
            .reset_index()
            .rename(columns={"Score pondéré": "Score pondéré total"})
        )

        # Merge avec le fichier filtré ligne par ligne
        filtered_df = filtered_df.merge(
            scores_df, on=["Code Métier", "Intitulé"], how="left"
        )

        # Réorganiser les colonnes et supprimer "Score pondéré"
        column_order = [
            "Code Métier",
            "Intitulé",
            "Score pondéré total",
            "Nb de passerelles communes",
            "Catégorie",
            "Compétence commune",
        ]
        filtered_df = filtered_df[column_order]

        # Trier par Score pondéré total décroissant
        filtered_df = filtered_df.sort_values(
            by=["Score pondéré total", "Code Métier", "Intitulé"],
            ascending=[False, True, True],
        )

        # 📥 Bouton de téléchargement
        st.download_button(
            label="📁 Télécharger Top 20 & passerelles associées",
            data=export_top20_filtered_passerelles(top_jobs, filtered_df),
            file_name="top20_et_passerelles.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_top20",
        )
        # Créer un tableau croisé avec Score pondéré par catégorie
        pivot_df = full_results_df.pivot_table(
            index=["Code Métier", "Intitulé"],
            columns="Catégorie",
            values="Score pondéré",
            aggfunc="sum",
            fill_value=0,
        ).reset_index()

        # Recalcul du score total pour tri
        pivot_df["Score total"] = pivot_df[selected_categories].sum(axis=1)
        pivot_df = pivot_df.sort_values("Score total", ascending=False).head(20)

        # Graphique empilé
        st.markdown("### 📊 Répartition des scores pondérés par type de compétence")
        fig, ax = plt.subplots(figsize=(8, 6))

        bottom = None
        labels = pivot_df["Intitulé"]

        # Colorer chaque barre selon la catégorie
        for cat in selected_categories:
            ax.barh(labels, pivot_df[cat], left=bottom, label=cat)
            if bottom is None:
                bottom = pivot_df[cat].copy()
            else:
                bottom += pivot_df[cat]

        ax.invert_yaxis()
        ax.set_xlabel("Score pondéré")
        ax.set_title("Top 20 métiers – scores par type de compétence")
        ax.legend(title="Catégorie")

        st.pyplot(fig)

        def export_excel(df, sheet_title, filename):
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                workbook = writer.book
                worksheet = workbook.add_worksheet(sheet_title)
                writer.sheets[sheet_title] = worksheet

                title_format = workbook.add_format({"bold": True, "font_size": 14})
                subtitle_format = workbook.add_format({"italic": True})

                # Écriture du titre et des dimensions choisies
                worksheet.write(
                    "A1", f"Métier de départ : {selected_job}", title_format
                )
                worksheet.write(
                    "A2",
                    f"Dimensions sélectionnées : {categories_str}",
                    subtitle_format,
                )
                # Définir les pondérations appliquées (selon sélection)
                weight_list = []
                if with_know_how:
                    weight_list.append(f"Savoir-faire = {know_how_weight}%")
                if with_professional_skills:
                    weight_list.append(
                        f"Savoir-être professionnels = {professional_skills_weight}%"
                    )
                if with_knowledge:
                    weight_list.append(f"Savoirs = {knowledge_weight}%")

                weight_str = " / ".join(weight_list)
                worksheet.write(
                    "A3", f"Pondérations appliquées : {weight_str}", subtitle_format
                )

                export_date = datetime.now().strftime("%d/%m/%Y à %Hh%M")
                worksheet.write("A4", f"Date d'export : {export_date}", subtitle_format)

                # Export des données à partir de la ligne 6 (index 5)
                df.to_excel(writer, index=False, startrow=5, sheet_name=sheet_title)

                # Ajustement automatique de la largeur des colonnes
                for i, col in enumerate(df.columns):
                    column_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                    worksheet.set_column(i, i, column_len)

            return buffer.getvalue()

        # ⬇️ Bouton 1 : Télécharger uniquement les passerelles filtrées (score > 3)
        st.download_button(
            label="📥 Télécharger les passerelles",
            data=export_excel(
                filtered_df, "Passerelles filtrées", "passerelles_filtrees.xlsx"
            ),
            file_name="passerelles_filtrees.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_filtered",
        )

        with st.expander("📦 Télécharger toutes les passerelles (brutes)"):
            if st.button("➡️ Générer toutes les passerelles sans aucun filtre"):
                st.markdown("###\n### ⏳ Génération des passerelles brutes...")

                # Rechargement brut
                raw_df = pd.read_excel(skills_file, sheet_name="Macro-Compétences")
                raw_df = raw_df.dropna(
                    subset=["Code Métier", "Intitulé", "Macro Compétence"]
                )

                client_jobs_df = pd.read_excel(client_file)
                raw_client_codes = client_jobs_df["Code ROME"].dropna().unique()

                client_jobs_df = raw_df[raw_df["Code Métier"].isin(raw_client_codes)]
                non_client_jobs_df = raw_df[
                    ~raw_df["Code Métier"].isin(raw_client_codes)
                ]

                # Fonction de calcul avec barre de progression
                def calculate_transitions(start_jobs, target_jobs, progress_bar=None):
                    rows = []
                    total = len(start_jobs["Code Métier"].unique())
                    for i, (start_code, start_group) in enumerate(
                        start_jobs.groupby("Code Métier")
                    ):
                        start_title = start_group["Intitulé"].iloc[0]
                        start_skills = set(start_group["Macro Compétence"].dropna())
                        for target_code, target_group in target_jobs.groupby(
                            "Code Métier"
                        ):
                            target_title = target_group["Intitulé"].iloc[0]
                            target_skills = set(
                                target_group["Macro Compétence"].dropna()
                            )
                            intersection = start_skills & target_skills
                            if intersection:
                                for skill in intersection:
                                    # Cherche catégorie dans le groupe d'arrivée (prioritaire) ou de départ
                                    if skill in target_group["Macro Compétence"].values:
                                        cat = target_group[
                                            target_group["Macro Compétence"] == skill
                                        ]["Catégorie"].iloc[0]
                                    else:
                                        cat = start_group[
                                            start_group["Macro Compétence"] == skill
                                        ]["Catégorie"].iloc[0]

                                    rows.append(
                                        {
                                            "Code Métier Départ": start_code,
                                            "Intitulé Départ": start_title,
                                            "Code Métier Arrivée": target_code,
                                            "Intitulé Arrivée": target_title,
                                            "Nombre de compétences partagées": len(
                                                intersection
                                            ),
                                            "Catégorie": cat,
                                            "Compétence commune": skill,
                                        }
                                    )

                        if progress_bar:
                            progress_bar.progress((i + 1) / total)
                    return pd.DataFrame(rows)

                # Calcul des passerelles avec barres de progression
                st.markdown("🔄 Calcul des passerelles entrantes...")
                bar1 = st.progress(0)
                incoming_df = calculate_transitions(
                    non_client_jobs_df, client_jobs_df, progress_bar=bar1
                )

                st.markdown("🔄 Calcul des passerelles sortantes...")
                bar2 = st.progress(0)
                outgoing_df = calculate_transitions(
                    client_jobs_df, non_client_jobs_df, progress_bar=bar2
                )

                st.success("✅ Calcul terminé ! Prêt à télécharger")

                # Export Excel
                raw_buffer = io.BytesIO()
                with pd.ExcelWriter(raw_buffer, engine="xlsxwriter") as writer:
                    incoming_df.to_excel(
                        writer, index=False, sheet_name="Passerelles entrantes"
                    )
                    outgoing_df.to_excel(
                        writer, index=False, sheet_name="Passerelles sortantes"
                    )

                raw_buffer.seek(0)
                st.download_button(
                    label="📥 Télécharger le fichier complet des passerelles",
                    data=raw_buffer.getvalue(),
                    file_name="passerelles_brutes.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_raw",
                )
            else:
                st.info(
                    "Cliquez sur le bouton ci-dessus pour lancer le calcul complet."
                )

    else:
        st.warning("Aucune compétence partagée trouvée avec les métiers cibles.")
