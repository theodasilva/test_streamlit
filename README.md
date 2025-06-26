# Passerelles-Métiers 🧭

Centralise et enrichit les données métiers (Compétences ↔ Macro-compétences ROME 4.0) via une application **Streamlit** prête à l’emploi.

---

## 1. Description rapide

| Fonction | Détail |
|----------|--------|
| 🔗 **Fusion Compétences ↔ Macro-compétences** | Ajoute automatiquement la colonne *Macro-compétence* à un fichier client. |
| 🧭 **Passerelles métiers** | Détecte les passerelles entre métiers sur la base des compétences partagées. |
| 📄 **Extraction PDF** | Convertit les fiches PDF ROME en Excel structuré. |
| 👤 **Gestion des utilisateurs** | Création / suppression de comptes, rôles *Superuser*, *Admin*… |

L’appel à l’API France Travail garantit des données ROME toujours à jour.

---

## 2. Prérequis

* **Python 3.9+**
* Accès Internet pour l’API France Travail (client ID / secret)
* Optionnel : *make* (Linux/macOS) pour piloter les commandes courantes

---

## 3. Installation pas-à-pas

```bash
# 1) Cloner le dépôt
git clone https://github.com/rogel-23/passerelles-metiers.git
cd passerelles-metiers

# 2) Créer et activer un environnement virtuel
python3 -m venv venv
source venv/bin/activate   # Windows : venv\Scripts\activate

# 3) Installer les dépendances
make install               # équivalent : python -m pip install -r requirements.txt

--
Secrets Streamlit :
Créez un fichier .streamlit/secrets.toml ou utilisez Streamlit Cloud › Settings › Secrets :
```txt
    FRANCE_CLIENT_ID     = "…"
    FRANCE_CLIENT_SECRET = "…"
```

--
4. Démarrage de l’application
```sh
make run          # lance Streamlit sur http://localhost:8501
Le module principal est Index.py. La sidebar permet d’accéder aux quatre pages listées ci-dessus.
```

--

5. Makefile
| Cible          | Action                                    |
| -------------- | ----------------------------------------- |
| `make run`     | `streamlit run Index.py`                  |
| `make format`  | Formatage automatique (`black` + `isort`) |
| `make install` | Installation des dépendances              |


--
6. Architecture des fichiers
```
.
├── Index.py                          # point d’entrée Streamlit
├── Makefile
├── requirements.txt
├── core/                             # logique métier
│   ├── france_travail_api.py
│   ├── data_processing.py
│   ├── read_file.py
│   ├── job_pdf_to_excel.py
│   └── auth_utils.py
├── pages/                            # pages Streamlit (sidebar)
│   ├── 1_Passerelles_metiers.py
│   ├── 2_PDF_vers_competence.py
│   ├── 3_Fusion_Macro-Competences.py
│   └── 4_Gestion_des_utilisateurs.py
└── user_config.yaml                  # comptes + rôles pour l’authentification
```