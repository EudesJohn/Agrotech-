from django.apps import AppConfig
import firebase_admin
import os

class ApiConfig(AppConfig):
    name = 'api'

    def ready(self):
        # Initialisation de Firebase Admin
        if not firebase_admin._apps:
            try:
                # Configuration explicite de l'ID projet Agrotech pour Render
                firebase_admin.initialize_app(options={
                    'projectId': 'agrotech-ai-ff555'
                })
                print(">>> Firebase Admin Initialized for agrotech-ai-ff555")
            except Exception as e:
                print(f">>> Firebase Admin Init Error: {e}")
