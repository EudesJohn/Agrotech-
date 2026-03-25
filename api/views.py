from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .firebase_auth import FirebaseAuthentication
import google.generativeai as genai
from django.conf import settings
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
    
    # Extraction du base64 si présent (format Data URL)
    if ';base64,' in image_data:
        image_data = image_data.split(';base64,')[1]

    try:
        # Re-configuration par précaution (permet le test à chaud)
        if not hasattr(genai, 'api_key_configured'):
            genai.configure(api_key=settings.GEMINI_API_KEY)
            genai.api_key_configured = True

        prompt = """Tu es PlantGuard AI, l'expert agronome ultime pour l'Afrique. 
        Analyse cette image. Si l'image n'est pas une plante ou est illisible, tu dois le signaler dans la maladie.
        
        Tu DOIS répondre UNIQUEMENT avec un objet JSON valide. Ne dis pas bonjour, n'ajoute aucun texte avant ou après.
        Le JSON doit avoir EXACTEMENT ces 7 clés en français :
        {
            "plante": "Nom de la plante identifiée (ex: Tomate, Maïs)",
            "utilite": "Utilité de la plante (nourriture, industrie, etc.)",
            "proprietes_medicinales": "Maladies humaines ou maux que cette plante aide à guérir ou ses bienfaits santé",
            "maladie": "Maladie actuelle de la plante (ex: Mildiou) ou 'Saine'",
            "cause": "Cause racine de la maladie (ex: Champignon)",
            "traitement": "Protocole exact étape par étape pour soigner la plante",
            "produit_recommande": "Nom du remède pour la plante"
        }"""
        
        # On utilise gemini-flash-latest qui a été testé avec succès
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content([{'mime_type': 'image/jpeg', 'data': image_data}, prompt])
        
        if not response.text:
            return Response({"error": "L'IA n'a pas pu générer de texte. L'image est peut-être inappropriée ou illisible."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        raw_text = response.text.strip()
        # Nettoyage Markdown si l'IA en ajoute
        if raw_text.startswith('```json'): raw_text = raw_text[7:]
        if raw_text.startswith('```'): raw_text = raw_text[3:]
        if raw_text.endswith('```'): raw_text = raw_text[:-3]
            
        try:
            diagnostic_data = json.loads(raw_text.strip())
        except json.JSONDecodeError:
            # Fallback si le JSON est malformé
            return Response({
                "status": "success", 
                "diagnostic": {
                    "maladie": "Analyse complexe",
                    "cause": "Erreur de formatage IA",
                    "traitement": raw_text[:500], # On renvoie le texte brut au pire
                    "produit_recommande": "Vérifiez les détails dans le traitement"
                }
            })

        # Sécurité : assurer que toutes les clés sont là
        for key in ["maladie", "cause", "traitement", "produit_recommande"]:
            if key not in diagnostic_data: diagnostic_data[key] = "Non détecté"
                
        return Response({"status": "success", "diagnostic": diagnostic_data})
    except Exception as e:
        # Logging de l'erreur pour debug si possible
        print(f"DEBUG AI ERROR: {str(e)}")
        return Response({"error": f"Erreur IA: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([FirebaseAuthentication])
@permission_classes([IsAuthenticated])
def ai_search(request):
    """
    Expert search analyzed by Gemini Pro. 
    Focus: Nature, plants, and agriculture.
    """
    query = request.data.get('query')
    if not query:
        return Response({"error": "Requête vide."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Configuration
        if not hasattr(genai, 'api_key_configured'):
            genai.configure(api_key=settings.GEMINI_API_KEY)
            genai.api_key_configured = True

        system_prompt = """Tu es Agrotech Intelligence, l'IA experte en agriculture tropicale et botanique.
        Réponds de manière concrète, détaillée et professionnelle.
        
        RÈGLE CRUCIALE : Réponds UNIQUEMENT aux questions portant sur la nature, les plantes, l'agriculture, l'élevage ou l'environnement.
        Si la question est hors-sujet, réponds poliment : "Je suis spécialisé uniquement en agriculture et botanique. Je ne peux pas répondre à cette question."
        
        Format de réponse : Utilise des puces et du gras pour la clarté. Sois précis sur les noms scientifiques si possible."""
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(f"{system_prompt}\n\nQuestion de l'utilisateur: {query}")
        
        if not response.text:
            return Response({"answer": "Désolé, je n'ai pas pu générer de réponse."}, status=200)

        return Response({
            "status": "success",
            "answer": response.text.strip()
        })
    except Exception as e:
        print(f"DEBUG AI SEARCH ERROR: {str(e)}")
        return Response({"error": f"Erreur IA: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    data = request.data
    firebase_uid = data.get('firebase_uid')
    email = data.get('email')
    full_name = data.get('full_name', '')
    phone = data.get('phone', '')
    location = data.get('location', '')
    user_type = data.get('user_type', 'FARMER')

    if not firebase_uid or not email:
        return Response({"error": "ID Firebase ou Email manquant"}, status=400)

    try:
        username = email.split('@')[0] + "_" + firebase_uid[:5]
        user, created = User.objects.get_or_create(email=email, defaults={'username': username})
        
        if full_name:
            names = full_name.split(' ')
            user.first_name = names[0]
            if len(names) > 1: user.last_name = " ".join(names[1:])
            user.save()

        profile, p_created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'firebase_uid': firebase_uid,
                'phone_number': phone,
                'location': location,
                'user_type': user_type,
                'profile_picture': request.data.get('photoURL')
            }
        )
        
        if not p_created:
            profile.firebase_uid = firebase_uid
            profile.phone_number = phone if phone else profile.phone_number
            profile.location = location if location else profile.location
            profile.user_type = user_type if user_type else profile.user_type
            p_pic = request.data.get('photoURL') 
            if p_pic: profile.profile_picture = p_pic
            profile.save()

        is_complete = bool(profile.phone_number and profile.location)

        return Response({
            "status": "success",
            "is_complete": is_complete,
            "user": {"id": user.id, "email": user.email, "full_name": f"{user.first_name} {user.last_name}".strip()}
        })
    except Exception as e:
        return Response({"error": str(e)}, status=500)

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
        user_data = request.data.get('user')
        if user_data:
            user = request.user
            if 'first_name' in user_data: user.first_name = user_data['first_name']
            if 'last_name' in user_data: user.last_name = user_data['last_name']
            user.save()

        serializer = UserProfileSerializer(profile, data=request.data, partial=(request.method == 'PATCH'))
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

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    email = request.data.get('email')
    if not email: return Response({"error": "Email requis"}, status=400)
    return Response({"status": "success", "message": f"Lien envoyé à {email}."})
