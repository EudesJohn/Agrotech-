"""
Firebase JWT Verification WITHOUT a Service Account.
Uses Firebase's public certificates to validate tokens.
No credentials file needed - works on any hosting (Render, Heroku, etc.)
"""
import requests
import json
import base64
import hashlib
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from rest_framework import authentication, exceptions
from django.contrib.auth.models import User
from .models import UserProfile

FIREBASE_PROJECT_ID = 'agrotech-ai-ff555'
FIREBASE_CERTS_URL = 'https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com'

_cert_cache = {}

def get_firebase_public_keys():
    """Récupère les clés publiques Firebase (avec cache simple)."""
    global _cert_cache
    if _cert_cache:
        return _cert_cache
    response = requests.get(FIREBASE_CERTS_URL, timeout=5)
    _cert_cache = response.json()
    return _cert_cache

def verify_firebase_token_manual(id_token):
    """
    Vérifie un token Firebase JWT en utilisant les clés publiques de Google.
    Ne nécessite aucun fichier de credentials.
    """
    try:
        # Séparer le JWT en 3 parties
        parts = id_token.split('.')
        if len(parts) != 3:
            raise ValueError("Token JWT invalide (format incorrect)")

        header_b64, payload_b64, signature_b64 = parts

        # Décoder le header pour trouver le kid (key ID)
        header_padded = header_b64 + '=' * (4 - len(header_b64) % 4)
        header = json.loads(base64.urlsafe_b64decode(header_padded))
        kid = header.get('kid')

        # Décoder le payload
        payload_padded = payload_b64 + '=' * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_padded))

        # Vérifications de base du payload
        import time
        now = time.time()
        if payload.get('exp', 0) < now:
            raise ValueError("Token expiré")
        if payload.get('aud') != FIREBASE_PROJECT_ID:
            raise ValueError(f"Audience incorrecte: {payload.get('aud')}")
        if payload.get('iss') != f'https://securetoken.google.com/{FIREBASE_PROJECT_ID}':
            raise ValueError("Émetteur invalide")

        # Vérifier la signature avec la clé publique Firebase
        certs = get_firebase_public_keys()
        if kid not in certs:
            _cert_cache.clear()  # Invalider le cache si kid inconnu
            certs = get_firebase_public_keys()

        if kid not in certs:
            raise ValueError(f"Clé publique introuvable pour kid={kid}")

        # Charger le certificat et vérifier
        cert_pem = certs[kid].encode()
        cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
        public_key = cert.public_key()

        # Données signées = header.payload
        signed_data = f"{parts[0]}.{parts[1]}".encode()
        signature_padded = signature_b64 + '=' * (4 - len(signature_b64) % 4)
        signature = base64.urlsafe_b64decode(signature_padded)

        public_key.verify(signature, signed_data, padding.PKCS1v15(), hashes.SHA256())

        return payload  # Token valide !

    except Exception as e:
        raise ValueError(f"Vérification du token échouée : {str(e)}")


class FirebaseAuthentication(authentication.BaseAuthentication):
    """
    Authentification Firebase sans Service Account.
    Vérifie les JWT via les clés publiques de Google.
    Crée automatiquement un profil Django si inexistant.
    """
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None

        id_token = auth_header.split(' ').pop()

        try:
            payload = verify_firebase_token_manual(id_token)

            uid = payload.get('uid') or payload.get('user_id')
            email = payload.get('email', '')
            name = payload.get('name', 'Utilisateur Agrotech')
            picture = payload.get('picture', '')

            # Sync Auto : Créer le profil Django si inexistant
            try:
                profile = UserProfile.objects.get(firebase_uid=uid)
                user = profile.user
            except UserProfile.DoesNotExist:
                username = email.split('@')[0] if email else f"user_{uid[:8]}"
                if User.objects.filter(username=username).exists():
                    username = f"{username}_{uid[:4]}"

                user = User.objects.create(
                    username=username,
                    email=email or f"{uid}@firebase-user.com",
                    first_name=name.split(' ')[0] if ' ' in name else name,
                    last_name=" ".join(name.split(' ')[1:]) if ' ' in name else ""
                )
                profile = UserProfile.objects.create(
                    user=user,
                    firebase_uid=uid,
                    profile_picture=picture
                )
                print(f">>> [AUTO-SYNC] Nouveau profil créé : {user.email}")

            return (user, None)

        except Exception as e:
            raise exceptions.AuthenticationFailed(f"Authentification échouée : {str(e)}")
