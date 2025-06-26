import io
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, BinaryIO, Dict, List

import pandas as pd
import pdfplumber

from core import france_travail_api

SECTION_CONFIG = {
    "alternate_titles": r"Autres emplois décrits",
    "definition": r"Définition",
    "job_requirements": r"Accès à l'emploi",
    "certifications": r"Certifications et diplômes",
    "skills": r"Compétences",
    "know_how": r"Savoir-faire",
    "professional_skills": r"Savoir-être professionnels",
    "knowledge": r"Savoirs",
    "work_context": r"Contextes de travail",
    "activity_sectors": r"Secteurs d'activité",
}


def extract_job_metadata(pdf_content: str) -> dict:
    with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text()

        if not text:
            return {"job_ref": None, "job_title": None}

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        job_ref = None
        job_title = None

        for i, line in enumerate(lines):
            if re.fullmatch(r"[A-Z]\d{4}", line):
                job_ref = line
                if i + 1 < len(lines):
                    job_title = lines[i + 1]
                break

        return {"job_ref": job_ref, "job_title": job_title}


def extract_full_pdf(pdf_file: BinaryIO):
    pdf_content = pdf_file.read()
    metadata = extract_job_metadata(pdf_content)
    sections = extract_pdf_sections(pdf_content)
    return {"metadata": metadata, "sections": sections}


def line_cleaner(line_data):
    res = []
    lines = []

    if "•" in line_data:
        lines.extend(line_data.split("•"))
    else:
        lines = [line_data]
    for line in lines:
        res.append(line.strip())

    return res


def extract_pdf_sections(
    pdf_content: str,
    section_config: Dict[str, str] = SECTION_CONFIG,
) -> Dict[str, str]:
    extracted_data = defaultdict(list)
    current_section = None

    with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=3, y_tolerance=3)
            if text:
                for line_data in text.split("\n"):
                    lines = line_cleaner(line_data)
                    for line in lines:
                        for section_name, pattern in section_config.items():
                            if re.search(pattern, line, flags=re.IGNORECASE):
                                current_section = section_name
                                break

                        if current_section and line:
                            clean_line = clean_text(line)
                            if clean_line:
                                extracted_data[current_section].append(clean_line)

    return {
        section: "\n".join(content[1:]) for section, content in extracted_data.items()
    }


def clean_text(line: str) -> str:
    line = re.sub(r"^[•]\s*", "", line)
    line = re.sub(r"\s+", " ", line).strip()
    return line if line and not is_footer(line) else ""


def is_footer(line: str) -> bool:
    footer_keywords = ["Copyright", "France Travail", "Page", "Confidentiel"]
    return any(keyword in line for keyword in footer_keywords)


def _to_multiline(value):
    """Return a newline-separated string if *value* is an iterable.

    Args:
        value (Any): Either a scalar or an iterable of scalars.

    Returns:
        str: ``value`` converted to a string, or elements joined with
        line breaks when *value* is a list/tuple/set.
    """
    if isinstance(value, (list, tuple, set)):
        return "\n".join(str(v) for v in value)
    return value or ""


def build_job_excel_pd(
    pdf_data: dict,
    job_data: dict,
    output_path: str | Path = "fiche_rome.xlsx",
) -> None:
    """Generate an Excel sheet where each competence is a separate row.

    The function flattens ``job_data["skills"]`` (structured as
    *Catégorie → Enjeu compétences → Compétences*).
    All other job-level fields are duplicated so the resulting DataFrame
    matches the expected ROME template.

    Args:
        pdf_data (dict):
            Output of :pyfunc:`job_pdf_to_excel.extract_full_pdf`.
        job_data (dict):
            Output of :pyfunc:`FranceTravailAPI.get_full_job_data`.
        output_path (str | pathlib.Path, optional):
            Destination file. Defaults to ``"fiche_rome.xlsx"``.

    Returns:
        None
    """
    code = pdf_data["metadata"]["job_ref"]
    title = pdf_data["metadata"]["job_title"]

    alt_titles = _to_multiline(pdf_data["sections"]["alternate_titles"])
    definition = _to_multiline(pdf_data["sections"]["definition"])
    job_requirements = _to_multiline(pdf_data["sections"]["job_requirements"])
    certifications = _to_multiline(pdf_data["sections"]["certifications"])
    activity_sectors = _to_multiline(pdf_data["sections"]["activity_sectors"])

    work_condition = _to_multiline(job_data["contexts"].get("CONDITIONS_TRAVAIL", []))
    work_schedule = _to_multiline(
        job_data["contexts"].get("HORAIRE_ET_DUREE_TRAVAIL", [])
    )
    work_structure = _to_multiline(
        job_data["contexts"].get("TYPE_STRUCTURE_ACCUEIL", [])
    )

    header = [
        "Code Métier",
        "Intitulé",
        "Autres emplois décrits",
        "Définition",
        "Accès à l'emploi",
        "Certifications et diplômes",
        "Catégorie",
        "Enjeu compétences",
        "Compétences",
        "Conditions de travail et risques professionnels",
        "Horaires et durée du travail",
        "Types de structures",
        "Secteurs d'activités",
    ]

    rows = [
        [
            code,
            title,
            alt_titles,
            definition,
            job_requirements,
            certifications,
            categorie,
            enjeu,
            competence,
            work_condition,
            work_schedule,
            work_structure,
            activity_sectors,
        ]
        for categorie, subdict in job_data["skills"].items()
        for enjeu, competences in subdict.items()
        for competence in competences
    ]

    df = pd.DataFrame(rows, columns=header).replace({pd.NA: ""})
    return df


def job_pdf_to_excel(pdf_file: BinaryIO) -> io.BytesIO:
    pdf_file.seek(0)

    pdf_data = extract_full_pdf(pdf_file)
    job_code = pdf_data.get("metadata", {}).get("job_ref")
    if job_code:
        api = france_travail_api.FranceTravailAPI()
        job_data = api.get_full_job_data(job_code)
        filename = f"{job_code}_fiche_rome.xlsx"
        return build_job_excel_pd(pdf_data, job_data, filename)
