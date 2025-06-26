import pandas as pd
import streamlit as st


def safe_read_excel(uploaded_file, sheet_name, required_cols, file_label):
    """
    Open an Excel file securely and ensure that required columns exist.

    Args:
        uploaded_file (BytesIO): Streamlit‐uploaded file.
        sheet_name (str | int): Worksheet name or index to read.
        required_cols (list[str]): Column names that must be present.
        file_label (str): Human-friendly file name used in error messages.

    Returns:
        pd.DataFrame: The loaded dataframe if everything is OK.

    Raises:
        Streamlit stops with a user-friendly error message when:
        - The sheet is missing.
        - The file cannot be opened.
        - Required columns are absent.
    """
    try:
        df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
    except ValueError:
        st.error(
            f"❌ Impossible de trouver l’onglet « {sheet_name} » dans {file_label}."
        )
        st.stop()
    except Exception as e:
        st.error(f"❌ Impossible d’ouvrir {file_label} : {e}")
        st.stop()

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"❌ Colonnes manquantes dans {file_label} : {', '.join(missing)}.")
        st.stop()

    return df
