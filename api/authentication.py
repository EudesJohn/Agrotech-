import firebase_admin
import os
from firebase_admin import auth as firebase_auth
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.contrib.auth.models import User
from .models import UserProfile

# Initialisation globale de Firebase Admin
if not firebase_admin._apps:
    # Récupérer le project ID depuis l'env ou utiliser le fallback
    project_id = os.getenv('FIREBASE_PROJECT_ID', 'agrotech-ai-ff555')
    firebase_admin.initialize_app(options={'projectId': project_id})

class FirebaseAuthentication(BaseAuthentication):
    """
    Middleware de sécurité 1000/1000.
    Intercepte le Token JWT de Firebase envoyé par Vue.js, le valide, 
    et connecte l'utilisateur Django correspondant.
    """
    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        id_token = auth_header.split(" ").pop()

        try:
            # Vérification cryptographique du token auprès de Google
            decoded_token = firebase_auth.verify_id_token(id_token)
        except Exception as e:
            raise exceptions.AuthenticationFailed(f"Token Firebase corrompu ou expiré : {str(e)}")

        uid = decoded_token.get("uid")
        email = decoded_token.get("email", f"{uid}@agrotech.local")

        # Création ou récupération de l'utilisateur Django à la volée
        user, created = User.objects.get_or_create(username=uid, defaults={'email': email})
        UserProfile.objects.get_or_create(user=user, defaults={'firebase_uid': uid})

        return (user, decoded_token)