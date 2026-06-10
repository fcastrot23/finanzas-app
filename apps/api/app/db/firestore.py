"""Firestore Admin SDK client — server-side writes and sensitive operations."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

import firebase_admin
from firebase_admin import credentials, firestore


@lru_cache(maxsize=1)
def _get_app() -> firebase_admin.App:
    """Initialize Firebase Admin SDK once per process."""
    emulator_host = os.environ.get("FIRESTORE_EMULATOR_HOST")
    if emulator_host:
        # Emulator: use a dummy credential
        app = firebase_admin.initialize_app(
            options={"projectId": os.environ.get("FIREBASE_PROJECT_ID", "finanzas-dev")}
        )
    else:
        cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        cred = credentials.Certificate(cred_path) if cred_path else credentials.ApplicationDefault()
        app = firebase_admin.initialize_app(cred)
    return app


def get_db() -> Any:
    """Return a Firestore client (Admin SDK)."""
    _get_app()
    return firestore.client()
