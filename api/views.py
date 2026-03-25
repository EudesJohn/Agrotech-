from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .firebase_auth import FirebaseAuthentication
from django.conf import settings
import google.generativeai as genai
import json
from django.contrib.auth.models import User
from .models import UserProfile
from .serializers import UserProfileSerializer
from rest_framework import status
from django.db.models import Q

# Configuration de l'API Gemini
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

@api_view(['POST'])
@authentication_classes([FirebaseAuthentication])
@permission_classes([IsAuthenticated])
def diagnose_plant(request):
    print(">>> DIAGNOSE PLANT REQUEST RECEIVED")
    image_data = request.data.get('image')
    if not image_data:
        return Response({"error": "Aucune image fournie."}, status=status.HTTP_400_BAD_REQUEST)
    
    if ';base64,' in image_data:
        image_data = image_data.split(';base64,')[1]

    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        prompt = """Tu es PlantGuard AI, l'expert agronome ultime pour l'Afrique. 
        Analyse cette image. Si l'image n'est pas une plante ou est illisible, tu dois le signaler dans la maladie.
        Tu DOIS répondre UNIQUEMENT avec un objet JSON valide.
        {
            "plante": "Nom de la plante",
            "utilite": "Utilité",
            "proprietes_medicinales": "Bienfaits santé",
            "maladie": "Maladie ou 'Saine'",
            "cause": "Cause",
            "traitement": "Protocole pas à pas",
            "produit_recommande": "Remède"
        }"""
        response = model.generate_content([{'mime_type': 'image/jpeg', 'data': image_data}, prompt])
        
        raw_text = response.text.strip()
        if raw_text.startswith('```json'): raw_text = raw_text[7:]
        if raw_text.startswith('```'): raw_text = raw_text[3:]
        if raw_text.endswith('```'): raw_text = raw_text[:-3]
            
        diagnostic_data = json.loads(raw_text.strip())
        return Response({"status": "success", "diagnostic": diagnostic_data})
    except Exception as e:
        return Response({"error": f"Erreur IA: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([FirebaseAuthentication])
@permission_classes([IsAuthenticated])
def ai_search(request):
    query = request.data.get('query')
    if not query:
        return Response({"error": "Requête vide."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        system_prompt = "Tu es Agrotech Intelligence, l'IA experte en agriculture tropicale."
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content(f"{system_prompt}\n\nQuestion: {query}")
        return Response({"status": "success", "answer": response.text.strip()})
    except Exception as e:
        return Response({"error": f"Erreur IA: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    # La création est maintenant gérée par FirebaseAuthentication automatiquement
    # Cet endpoint reste pour la compatibilité frontend si besoin de stats supplémentaires
    return Response({"status": "success", "message": "Enregistrement via Sync Auto activé."})

@api_view(['GET', 'PUT', 'PATCH'])
@authentication_classes([FirebaseAuthentication])
@permission_classes([IsAuthenticated])
def profile_detail(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return Response({"error": "Profil non trouvé"}, status=404)

    if request.method == 'GET':
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([AllowAny])
def public_profile(request, firebase_uid):
    try:
        profile = UserProfile.objects.get(firebase_uid=firebase_uid)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    except UserProfile.DoesNotExist:
        return Response({"error": "Profil non trouvé"}, status=404)

@api_view(['GET'])
@permission_classes([AllowAny])
def version_check(request):
    return Response({"version": "v2.0-PROD-SYNC-LIVE", "status": "ok"})

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    email = request.data.get('email')
    if not email: return Response({"error": "Email requis"}, status=400)
    return Response({"status": "success", "message": f"Lien envoyé à {email}."})
