import streamlit as st
import streamlit_authenticator as stauth
import yaml

from core import auth_utils

# Load config
config = auth_utils.load_config()

# Setup authenticator
authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)

authenticator.login(location="main", fields=["username", "password"])

if st.session_state.get("authentication_status") is False:
    st.error("Username/password is incorrect")
elif st.session_state.get("authentication_status") is None:
    st.warning("Please enter your credentials")
    st.stop()
elif st.session_state.get("authentication_status"):
    authenticator.logout()

    st.set_page_config(
        page_title="Hello",
        page_icon="👋",
    )
    # ------------------------------
    # PAGE CONFIGURATION
    # ------------------------------
    st.set_page_config(
        page_title="Arthur Hunt - Outils Métiers", page_icon="🏢", layout="wide"
    )

    # ------------------------------
    # MAIN PAGE CONTENT
    # ------------------------------
    st.title("🏢 Arthur Hunt - Outils Métiers")
    st.markdown("---")

    st.markdown(
        """
    Bienvenue dans la plateforme d'outils métiers d'Arthur Hunt. Cette application propose trois modules spécialisés :

    1. **🧭 Outil de passerelles métiers** - Analyse des transitions professionnelles
    2. **📄 Extraction de fiches métiers** - Conversion PDF vers données structurées
    3. **🔗 Fusion compétences ↔ macro-compétences** - Fusion the fiche de compétence et Macro-Compétences
    4. **👤 Gestion des utilisateurs** - Administration des accès (réservé aux administrateurs)

    Sélectionnez un outil dans la sidebar pour commencer.
    """
    )

    st.markdown("---")

    # ------------------------------
    # TOOL DOCUMENTATION
    # ------------------------------
    st.header("📚 Documentation des outils")

    # Passerelles Métiers Documentation
    with st.expander("🧭 Documentation de l'outil Passerelles Métiers"):
        st.markdown(
            """
        ### Objectif
        Cet outil permet d'identifier les passerelles professionnelles possibles entre les métiers d'un client et ceux du référentiel ROME, basé sur les compétences partagées.

        ### Fonctionnalités clés
        - Analyse des compétences communes entre métiers
        - Calcul de scores de proximité professionnelle
        - Filtrage par secteur d'activité
        - Génération de rapports Excel détaillés

        ### Mode d'emploi
        1. **Charger les fichiers requis** :
        - Le référentiel des macro-compétences ROME
        - La liste des métiers clients (avec codes ROME)
        2. **Configurer l'analyse** :
        - Choisir le type de passerelle (entrante/sortante)
        - Sélectionner les catégories de compétences à inclure
        - Définir les pondérations
        3. **Lancer l'analyse** :
        - Filtrer par secteur si nécessaire
        - Sélectionner un métier de départ
        4. **Exporter les résultats** :
        - Télécharger le top 20 des passerelles
        - Ou générer un rapport complet

        ### Formats supportés
        - Fichiers d'entrée : Excel (.xlsx)
        - Fichiers de sortie : Excel (.xlsx)
        """
        )

    # PDF Extraction Documentation
    with st.expander("📄 Documentation de l'outil d'extraction PDF"):
        st.markdown(
            """
        ### Objectif
        Convertir les fiches métiers PDF standardisées en données structurées exploitables.

        ### Fonctionnalités clés
        - Extraction automatique des sections clés
        - Reconnaissance des compétences catégorisées
        - Export au format Excel multi-feuilles

        ### Mode d'emploi
        1. **Charger un fichier PDF** :
        - Doit suivre le format standard des fiches métiers
        - Exemple : A1101.pdf
        2. **Vérifier les données extraites** :
        - Aperçu des informations détectées
        - Validation visuelle
        3. **Télécharger les résultats** :
        - Fichier Excel organisé par catégories
        - Structure prête pour analyse

        ### Sections extraites
        - Titre et définition du métier
        - Titres alternatifs
        - Exigences (formation, certifications)
        - Compétences (savoir-faire, savoir-être)
        - Connaissances techniques
        - Contexte de travail

        ### Formats supportés
        - Fichiers d'entrée : PDF (.pdf)
        - Fichiers de sortie : Excel (.xlsx)
        """
        )

    with st.expander("🔗 Documentation de la fusion Compétences ↔ Macro-compétences"):
        st.markdown(
            """
            ### Objectif
            Associer automatiquement les compétences d’un fichier Excel (*Compétences*)
            aux macro-compétences d’un second fichier (*Macro-compétences*) afin
            d’obtenir un tableau enrichi prêt pour l’analyse.

            ### Fonctionnalités clés
            - Lecture sécurisée des deux fichiers avec contrôle des colonnes requises
            (`Compétences`, `5 - Compétence`, `4 - Macro-compétence`)
            - Jointure intelligente via `join_on_columns`
            (clé : **Compétences** ↔ **5 - Compétence**)
            - Ajout de la colonne **Macro-compétence** au fichier de sortie
            - Export en une seule feuille Excel nommée **Résultat**

            ### Mode d’emploi
            1. **Charger les fichiers**
            - *Compétences* (première feuille, colonne **Compétences**)
            - *Macro-compétences* (feuille **Macro-Compétences**,
                colonnes **5 - Compétence** et **4 - Macro-compétence**)
            2. **Lancer la fusion** en cliquant sur **🚀 Lancer la fusion**
            3. **Télécharger** le fichier Excel généré (**Skills_with_macro_competence.xlsx**)

            ### Formats supportés
            - Fichiers d’entrée : Excel (.xlsx ou .xls)
            - Fichier de sortie : Excel (.xlsx)

            """
        )

    # User Management Documentation
    with st.expander("👤 Documentation de la gestion des utilisateurs"):
        st.markdown(
            """
        ### Objectif (Réservé aux administrateurs)
        Gérer les comptes utilisateurs et les permissions d'accès aux outils.

        ### Fonctionnalités clés
        - Création de nouveaux comptes
        - Modification des mots de passe
        - Suppression de comptes
        - Gestion des rôles utilisateurs

        ### Rôles disponibles
        1. **Superuser** :
        - Accès complet à toutes les fonctionnalités
        - Impossible à supprimer/modifier via l'interface
        2. **Admin** :
        - Peut gérer les autres utilisateurs
        - Accès à tous les outils
        3. **Client** :
        - Accès limité aux outils métiers
        - Pas d'accès à l'administration
        4. **Utilisateur** :
        - Accès de base aux fonctionnalités principales

        ### Mode d'emploi
        1. **Créer un utilisateur** :
        - Définir un nom d'utilisateur unique
        - Attribuer un rôle approprié
        - Définir un mot de passe sécurisé
        2. **Modifier un mot de passe** :
        - Sélectionner l'utilisateur concerné
        - Saisir le nouveau mot de passe
        3. **Supprimer un utilisateur** :
        - Sélectionner l'utilisateur à supprimer
        - Confirmer la suppression

        ### Bonnes pratiques
        - Utiliser des mots de passe complexes
        - Limiter le nombre d'administrateurs
        - Révoquer rapidement les accès des anciens collaborateurs
        """
        )
