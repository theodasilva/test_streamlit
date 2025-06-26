import os

import streamlit as st
import yaml
from yaml.loader import SafeLoader

USER_CONFIG_PATH = "user_config.yaml"


def require_roles(allowed_roles):
    """Restricts access to the page based on user roles.

    Args:
        allowed_roles (list): List of roles that are allowed to access the page.

    Raises:
        Stops Streamlit execution with an error if the user is not authorized.
    """
    if not st.session_state.get("authentication_status") or not any(
        role in st.session_state.get("roles", []) for role in allowed_roles
    ):
        st.error(
            "⛔ Accès refusé. Vous n'avez pas les permissions nécessaires pour accéder à cette page."
        )
        st.stop()


def require_auth():
    """Restricts access to the page if the user is not authenticated.

    Raises:
        Stops Streamlit execution with an error if the user is not logged in.
    """
    if not st.session_state.get("authentication_status"):
        st.error("⛔ Accès refusé. Veuillez vous connecter pour accéder à cette page.")
        st.stop()


def load_config():
    """Loads the user configuration from a YAML file.

    Raises:
        FileNotFoundError: If the configuration file does not exist.

    Returns:
        dict: The parsed configuration dictionary.
    """
    if not os.path.exists(USER_CONFIG_PATH):
        raise FileNotFoundError(
            f"Fichier de configuration introuvable : '{USER_CONFIG_PATH}'."
        )
    with open(USER_CONFIG_PATH, "r") as file:
        return yaml.load(file, Loader=SafeLoader)
