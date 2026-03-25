import firebase_admin
from firebase_admin import auth
from django.conf import settings
from rest_framework import authentication
from rest_framework import exceptions
from django.contrib.auth.models import User
from .models import UserProfile

class FirebaseAuthentication(authentication.BaseAuthentication):
    """
    Validation réelle du token JWT via Firebase Admin SDK.
    Auto-crée l'utilisateur Django s'il n'existe pas encore.
    Cela permet une intégration fluide sans inscription manuelle sur le backend.
    """
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None
        
        id_token = auth_header.split(' ').pop()
        
        try:
            # 1. Vérification du token avec le SDK Admin Firebase
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token.get('uid')
            email = decoded_token.get('email')
            name = decoded_token.get('name', 'Utilisateur Agrotech')
            picture = decoded_token.get('picture', '')

            # 2. Récupération ou Création Automatique de l'utilisateur Django
            # Requis pour les relations de modèles Django (historique, etc.)
            try:
                profile = UserProfile.objects.get(firebase_uid=uid)
                user = profile.user
            except UserProfile.DoesNotExist:
                # Création automatique et silencieuse (Mirroring)
                username = email.split('@')[0] if email else f"user_{uid[:8]}"
                # Unicité du username
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
                print(f">>> SYNC : Nouvel utilisateur Django créé pour {user.email}")

            return (user, None)
            
        except Exception as e:
            # En mode DEBUG local, on peut logger plus de détails
            if settings.DEBUG:
                print(f"AUTH DEBUG ERROR: {str(e)}")
            
            raise exceptions.AuthenticationFailed(f"Authentification Firebase échouée : {str(e)}")
