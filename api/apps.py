from django.apps import AppConfig
import firebase_admin
import os

class ApiConfig(AppConfig):
    name = 'api'

    def ready(self):
        # Initialisation de Firebase Admin
        if not firebase_admin._apps:
            try:
                # Sur Render, si on n'a pas de fichier JSON, on initialise par défaut
                # (nécessite que les variables d'environnement Google soient configurées ou par défaut)
                firebase_admin.initialize_app()
                print(">>> Firebase Admin Initialized Successfully")
            except Exception as e:
                print(f">>> Firebase Admin Init Error: {e}")
