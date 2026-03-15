import json
import streamlit as st

def write_client_secrets(client_id, client_secret, project_id="sunleo-music"):
    """
    Creates the google_secret.json file required by the auth library.
    """
    secret_dict = {
        "web": {
            "client_id": client_id,
            "project_id": project_id,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": client_secret,
            "redirect_uris": [
                "http://localhost:8501/"
            ]
        }
    }
    
    with open("google_secret.json", "w") as f:
        json.dump(secret_dict, f, indent=4)
    
    return True
