import pandas as pd
import unicodedata
import re
from typing import Dict


def clean_text(s: pd.Series) -> pd.Series:
    """Normalize text by removing accents, special characters, and extra spaces.

    Args:
        s (pd.Series): Input text series to clean

    Returns:
        pd.Series: Cleaned text series in lowercase
    """
    s = (s.astype(str)
           .str.normalize("NFKD")
           .str.encode("ascii", "ignore")
           .str.decode("utf-8"))
    s = s.str.replace(r"[\u00A0\r\n\t]+", " ", regex=True)
    s = s.str.replace(r"[•;/\-–—]", " ", regex=True)
    s = s.str.replace(r"[(){}\[\],.’‘’“”«»\\]", " ", regex=True)
    return s.str.replace(r"\s+", " ", regex=True).str.strip().str.lower()


def add_macro_competence(df_skills: pd.DataFrame, df_macro: pd.DataFrame) -> pd.DataFrame:
    """Adds macro-competence mapping to skills DataFrame.

    Args:
        df_skills (pd.DataFrame): DataFrame containing skills with 'Compétences' column
        df_macro (pd.DataFrame): DataFrame containing macro-competence mappings

    Returns:
        pd.DataFrame: Original skills DataFrame with added 'Macro-Compétence' column
    """
    df_result = df_skills.copy()
    df_macro = df_macro.copy()

    df_result['clean_competence'] = clean_text(df_result['Compétences'])

    for col_to_explode in ["5 - Compétence", "5 - Compétence (bis)"]:
        df_macro[col_to_explode] = df_macro[col_to_explode].astype(str).str.split(r"[•;\n]")
        df_macro = df_macro.explode(col_to_explode).reset_index(drop=True)

    df_macro["key_1"] = clean_text(df_macro["5 - Compétence"])
    df_macro["key_2"] = clean_text(df_macro["5 - Compétence (bis)"])
    df_macro["key_3"] = clean_text(df_macro["4 - Macro-compétence"])

    mapping_dict = {}
    for col in ["key_1", "key_2", "key_3"]:
        temp_dict = (df_macro.dropna(subset=[col, "4 - Macro-compétence"])
                      .sort_values("4 - Macro-compétence", na_position="last")
                      .drop_duplicates(subset=col, keep="first")
                      .set_index(col)["4 - Macro-compétence"]
                      .to_dict())
        mapping_dict.update({k: v for k, v in temp_dict.items() if k not in mapping_dict})

    df_result["Macro-Compétence"] = df_result['clean_competence'].map(mapping_dict)

    return df_result.drop(columns='clean_competence')


def load_and_validate_skills(file_buffer) -> pd.DataFrame:
    """Load and validate skills Excel file.

    Args:
        file_buffer: Uploaded Excel file object

    Returns:
        pd.DataFrame: Cleaned and validated DataFrame with skills data

    Raises:
        ValueError: If file is invalid or missing required columns
    """
    try:
        df = pd.read_excel(file_buffer, sheet_name="Macro-Compétences")

        required_cols = {"Code Métier", "Intitulé", "Macro Compétence", "Catégorie"}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

        df = df.dropna(subset=["Code Métier", "Intitulé", "Macro Compétence"])
        df["Code Métier"] = clean_text(df["Code Métier"]).str.upper()
        df["Macro Compétence"] = clean_text(df["Macro Compétence"])
        df["Catégorie"] = clean_text(df["Catégorie"])

        return df

    except Exception as e:
        raise ValueError(f"Error processing skills file: {str(e)}")


def load_and_validate_client(file_buffer) -> pd.DataFrame:
    """Load and validate client Excel file.

    Args:
        file_buffer: Uploaded Excel file object

    Returns:
        pd.DataFrame: Cleaned DataFrame with client job codes

    Raises:
        ValueError: If required columns are missing
    """
    try:
        df = pd.read_excel(file_buffer)

        if "Code ROME" not in df.columns:
            raise ValueError("Client file must contain 'Code ROME' column")

        df["Code ROME"] = clean_text(df["Code ROME"]).str.upper()
        df = df.dropna(subset=["Code ROME"])

        return df

    except Exception as e:
        raise ValueError(f"Error processing client file: {str(e)}")


def calculate_job_similarities(
    start_df: pd.DataFrame,
    target_df: pd.DataFrame,
    selected_job_code: str,
    weights: Dict[str, int],
) -> pd.DataFrame:
    """Calculate weighted similarity scores between jobs.

    Args:
        start_df: DataFrame containing starting job data
        target_df: DataFrame containing target job data
        selected_job_code: Job code to compare against
        weights: Weights for each skill category

    Returns:
        pd.DataFrame: Similarity results with scores

    Raises:
        ValueError: If computation fails
    """
    try:
        selected_job_code = selected_job_code.strip().upper()
        selected_skills = set(
            start_df[start_df["Code Métier"] == selected_job_code]["Macro Compétence"]
        )
        start_letter = selected_job_code[0]
        results = []

        for job_code, group in target_df.groupby("Code Métier"):
            if job_code == selected_job_code:
                continue

            title = group["Intitulé"].iloc[0]
            job_skills = set(group["Macro Compétence"])
            common_skills = selected_skills & job_skills

            if common_skills:
                for skill in common_skills:
                    category = group[group["Macro Compétence"] == skill][
                        "Catégorie"
                    ].iloc[0]
                    weight = weights.get(category.lower(), 0)
                    bonus = 1.25 if job_code.startswith(start_letter) else 1
                    weighted_score = (len(common_skills) * weight / 100) * bonus

                    results.append(
                        {
                            "Code Métier": job_code,
                            "Intitulé": title.title(),
                            "Nb de passerelles communes": len(common_skills),
                            "Score pondéré": weighted_score,
                            "Catégorie": category,
                            "Compétence commune": skill,
                        }
                    )

        if results:
            result_df = pd.DataFrame(results)
            result_df["Score pondéré total"] = result_df.groupby(
                ["Code Métier", "Intitulé"]
            )["Score pondéré"].transform("sum")
            return result_df.sort_values("Score pondéré total", ascending=False)

        return pd.DataFrame()

    except Exception as e:
        raise ValueError(f"Error calculating similarities: {str(e)}")


def join_on_columns(
    df_left: pd.DataFrame,
    df_right: pd.DataFrame,
    left_col: str,
    right_col: str,
) -> pd.DataFrame:
    """Perform left join between two DataFrames on specified columns.

    Args:
        df_left: Left DataFrame to enrich
        df_right: Right DataFrame to join with
        left_col: Column name in df_left to join on
        right_col: Column name in df_right to join on

    Returns:
        pd.DataFrame: Enriched DataFrame with joined columns
    """
    joined = df_left.merge(
        df_right,
        how="left",
        left_on=left_col,
        right_on=right_col,
    )
    return joined