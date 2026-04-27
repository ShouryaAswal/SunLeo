"""
Firestore client singleton for SunLeo chatbot service.
Initializes Firebase Admin SDK once per process and exposes a shared Firestore client.
"""
from __future__ import annotations

import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore

_app: firebase_admin.App | None = None
_db: firestore.Client | None = None

# Project root: app/ → chatbot_service/ → backend/ → root (local dev only)
try:
    _PROJECT_ROOT = Path(__file__).parents[3]
except IndexError:
    _PROJECT_ROOT = Path("/app")  # Docker fallback


def get_db() -> firestore.Client:
    """Return the shared Firestore client, initializing Firebase once."""
    global _app, _db

    if _db is not None:
        return _db

    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_path:
        raise RuntimeError(
            "GOOGLE_APPLICATION_CREDENTIALS is not set. "
            "Point it to your Firebase service account JSON file."
        )

    # Resolve relative paths against project root (where .env lives)
    cred_resolved = Path(cred_path)
    if not cred_resolved.is_absolute():
        cred_resolved = _PROJECT_ROOT / cred_resolved
    cred_path = str(cred_resolved)

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        _app = firebase_admin.initialize_app(cred)

    _db = firestore.client()
    return _db
