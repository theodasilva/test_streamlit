import os

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

from core import auth_utils

USER_CONFIG_PATH = "user_config.yaml"


def is_superuser(username):
    """Checks if the specified user has the 'Superuser' role.

    Args:
        username (str): The username to check.

    Returns:
        bool: True if the user has the 'Superuser' role, False otherwise.
    """
    user = config["credentials"]["usernames"].get(username)
    return user and "Superuser" in user.get("roles", [])


def save_config(config):
    """Saves the given configuration dictionary to a YAML file.

    Args:
        config (dict): The configuration data to save.
    """
    with open(USER_CONFIG_PATH, "w") as file:
        yaml.dump(config, file, default_flow_style=False, allow_unicode=True)


st.set_page_config(page_title="Gestion des utilisateurs", page_icon="👤")

# Restrict access to Admins and Superusers
auth_utils.require_roles(["Admin", "Superuser"])

# Load YAML config
config = auth_utils.load_config()
st.title("👤 Gestion des utilisateurs")
st.markdown("---")

# --- Create User ---
st.subheader("➕ Créer un nouvel utilisateur")

with st.form("create_user_form"):
    new_username = st.text_input("Nom d'utilisateur")
    new_password = st.text_input("Mot de passe", type="password")
    new_role = st.selectbox("Rôle", ["Utilisateur", "Client", "Admin"])

    submitted = st.form_submit_button("Créer l'utilisateur")
    if submitted:
        if new_username in config["credentials"]["usernames"]:
            st.error("Ce nom d'utilisateur existe déjà.")
        elif not new_username or not new_password:
            st.error("Le nom d'utilisateur et le mot de passe sont obligatoires.")
        else:
            hashed_pwd = stauth.Hasher.hash(new_password)
            config["credentials"]["usernames"][new_username] = {
                "password": hashed_pwd,
                "roles": [new_role],
                "failed_login_attempts": 0,
                "logged_in": False,
            }
            save_config(config)
            st.success(
                f"✅ Utilisateur '{new_username}' créé avec le rôle '{new_role}'."
            )

# --- Update Password ---
st.markdown("---")
st.subheader("🔑 Modifier le mot de passe")

user_to_update = st.selectbox(
    "Sélectionner un utilisateur", list(config["credentials"]["usernames"].keys())
)
new_pw = st.text_input("Nouveau mot de passe", type="password", key="pw_change")
if st.button("Modifier le mot de passe"):
    if is_superuser(user_to_update):
        st.warning(
            "⚠️ Vous ne pouvez pas modifier le mot de passe d’un superutilisateur."
        )
    elif not new_pw:
        st.error("Veuillez saisir un nouveau mot de passe.")
    else:
        hashed_pwd = stauth.Hasher.hash(new_pw)
        config["credentials"]["usernames"][user_to_update]["password"] = hashed_pwd
        save_config(config)
        st.success(f"🔐 Mot de passe mis à jour pour '{user_to_update}'.")

# --- Delete User ---

st.markdown("---")
st.subheader("🗑️ Supprimer un utilisateur")

user_to_delete = st.selectbox(
    "Sélectionner un utilisateur à supprimer",
    list(config["credentials"]["usernames"].keys()),
    key="delete_user",
)
if st.button("Supprimer l'utilisateur"):
    if is_superuser(user_to_delete):
        st.warning("❌ Vous ne pouvez pas supprimer un superutilisateur.")
    else:
        del config["credentials"]["usernames"][user_to_delete]
        save_config(config)
        st.success(f"🗑️ Utilisateur '{user_to_delete}' supprimé avec succès.")
