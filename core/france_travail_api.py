import time
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional
from core import utils

import requests

BASE_URL_JOB_DESCRIPTION = "https://api.francetravail.io/partenaire/rome-fiches-metiers/v1/fiches-rome/fiche-metier"
BASE_URL_JOB_CONTEXT = (
    "https://api.francetravail.io/partenaire/rome-metiers/v1/metiers/metier"
)
AUTH_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire"
TIMEOUT = 10


class FranceTravailAPI:
    """
    API client for interacting with France Travail job description and context APIs.
    Handles authentication, retry logic, and structured extraction of job competences and knowledge.
    """

    def __init__(self):
        self.CLIENT_ID = utils.require_env("FRANCETRAVAIL_CLIENT_ID")
        self.CLIENT_SECRET = utils.require_env("FRANCETRAVAIL_CLIENT_SECRET")
        self.SCOPE = "api_rome-fiches-metiersv1 api_rome-metiersv1 nomenclatureRome"

        self.BASE_URL_JOB_DESCRIPTION = BASE_URL_JOB_DESCRIPTION
        self.BASE_URL_JOB_CONTEXT = BASE_URL_JOB_CONTEXT
        self.AUTH_URL = AUTH_URL
        self.TIMEOUT = TIMEOUT

        self.MAX_RETRIES = 3
        self.BASE_DELAY = 1
        self.MAX_DELAY = 10

        self._token: Optional[str] = None
        self._exp: float = 0.0

        self.skills: Dict[str, Dict[str, List[str]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self.contexts: Dict[str, List[str]] = defaultdict(list)
        self.current_job_code: Optional[str] = None

    def _retry_with_backoff(self, fn: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with exponential backoff in case of failure.

        Args:
            fn (Callable): The function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            Any: Result of the function if successful.

        Raises:
            FranceTravailAPIError: If all retries fail.
        """
        last_exception = None

        for attempt in range(self.MAX_RETRIES):
            try:
                return fn(*args, **kwargs)
            except (requests.exceptions.RequestException, FranceTravailAPIError) as e:
                last_exception = e
                if attempt == self.MAX_RETRIES - 1:
                    break
                delay = min(self.BASE_DELAY * (2**attempt), self.MAX_DELAY)
                time.sleep(delay + delay * 0.1 * (attempt + 1))

        raise FranceTravailAPIError(
            f"Failed after {self.MAX_RETRIES} attempts: {str(last_exception)}"
        )

    def _get_token(self) -> str:
        """
        Retrieve or renew the OAuth2 access token using client credentials.

        Returns:
            str: The access token.

        Raises:
            FranceTravailAPIError: If the token cannot be obtained.
        """
        now = time.time()
        if self._token and now < self._exp - 60:
            return self._token

        def _request_token():
            try:
                response = requests.post(
                    self.AUTH_URL,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.CLIENT_ID,
                        "client_secret": self.CLIENT_SECRET,
                        "scope": self.SCOPE,
                    },
                    timeout=self.TIMEOUT,
                )
                response.raise_for_status()
                token_data = response.json()
                self._token = token_data["access_token"]
                self._exp = now + token_data["expires_in"]
                return self._token
            except requests.exceptions.RequestException as e:
                raise FranceTravailAPIError(f"Failed to obtain access token: {str(e)}")

        return self._retry_with_backoff(_request_token)

    def _make_request(self, url: str) -> Dict[str, Any]:
        """
        Make an authenticated GET request to a specified URL.

        Args:
            url (str): The URL to request.

        Returns:
            Dict[str, Any]: Parsed JSON response.

        Raises:
            FranceTravailAPIError: If the request fails.
        """

        def _request():
            try:
                headers = {
                    "Authorization": f"Bearer {self._get_token()}",
                    "Accept": "application/json",
                }
                response = requests.get(url, headers=headers, timeout=self.TIMEOUT)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                raise FranceTravailAPIError(f"API request failed: {str(e)}")

        return self._retry_with_backoff(_request)

    def get_job_description(self, code: str) -> Dict[str, Any]:
        """
        Retrieve the job description data for a given job code.

        Args:
            code (str): ROME job code.

        Returns:
            Dict[str, Any]: Job description data.
        """
        url = f"{self.BASE_URL_JOB_DESCRIPTION}/{code}"
        return self._make_request(url)

    def get_job_context(self, code: str) -> Dict[str, Any]:
        """
        Retrieve the job context data for a given job code.

        Args:
            code (str): ROME job code.

        Returns:
            Dict[str, Any]: Job context data.
        """
        url = f"{self.BASE_URL_JOB_CONTEXT}/{code}"
        return self._make_request(url)

    def process_competences(self, fiche_data: Dict[str, Any]) -> None:
        """
        Process and store competences from the job description data.

        Args:
            fiche_data (Dict[str, Any]): Raw job description data.
        """
        if "groupesCompetencesMobilisees" not in fiche_data:
            return

        for line in fiche_data["groupesCompetencesMobilisees"]:
            skill_title = line.get("enjeu", {}).get("libelle", "Unknown")
            for skill in line.get("competences", []):
                skill_type_res = skill.get("type", "Unknown")
                if skill_type_res in {"MACRO-SAVOIR-ETRE-PROFESSIONNEL"}:
                    skill_type = "Savoir-être professionnels"
                    skill_title = skill_type
                else:
                    skill_type = "Savoir-faire"
                skill_description = skill.get("libelle", "")
                self.skills[skill_type][skill_title].append(skill_description)

    def process_knowledge(self, fiche_data: Dict[str, Any]) -> None:
        """
        Process and store knowledge from the job description data.

        Args:
            fiche_data (Dict[str, Any]): Raw job description data.
        """
        if "groupesSavoirs" not in fiche_data:
            return

        for knowledge_group in fiche_data["groupesSavoirs"]:
            skill_title = knowledge_group.get("categorieSavoirs", {}).get(
                "libelle", "Unknown"
            )
            for knowledge in knowledge_group.get("savoirs", []):
                skill_type = "Savoir"
                skill_description = knowledge.get("libelle", "")
                self.skills[skill_type][skill_title].append(skill_description)

    def print_skills(self) -> None:
        """
        Print all collected skills organized by type.
        """
        for skill_type, skill_groups in self.skills.items():
            print(f"{skill_type}:\n{skill_groups}")

    def get_full_job_data(self, code: str) -> Dict[str, Any]:
        """
        Retrieve and process all available data for a given job code.

        Args:
            code (str): ROME job code.

        Returns:
            Dict[str, Any]: Dictionary containing description, contexts, and skills.
        """
        self.current_job_code = code
        description = self.get_job_description(code)
        self.process_competences(description)
        self.process_knowledge(description)
        self.process_job_context(code)

        return {
            "description": description,
            "contexts": dict(self.contexts),
            "skills": dict(self.skills),
        }

    def process_job_context(self, code: str) -> Dict[str, List[str]]:
        """
        Process and store job context information by category.

        Args:
            code (str): ROME job code.

        Returns:
            Dict[str, List[str]]: Categorized job contexts.
        """
        context_res = self.get_job_context(code)
        self.contexts.clear()

        for context in context_res.get("contextesTravail", []):
            category = context["categorie"]
            text = context["libelle"]
            self.contexts[category].append(text)

        return dict(self.contexts)

    def get_competences(self) -> Dict[str, List[str]]:
        """
        Retrieve all processed competences grouped by skill title.

        Returns:
            Dict[str, List[str]]: Competences grouped by title.
        """
        return dict(self.skills.get("COMPETENCE", {}))

    def get_knowledge(self) -> Dict[str, List[str]]:
        """
        Retrieve all processed knowledge items grouped by category.

        Returns:
            Dict[str, List[str]]: Knowledge grouped by category.
        """
        return dict(self.skills.get("SAVOIR", {}))

    def reset_data(self) -> None:
        """
        Clear all stored job data including skills and contexts.
        """
        self.skills.clear()
        self.contexts.clear()
        self.current_job_code = None


class FranceTravailAPIError(Exception):
    """
    Custom exception class for handling API-related errors.
    """

    pass
