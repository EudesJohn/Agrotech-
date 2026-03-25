from django.urls import path
from . import views

urlpatterns = [
    path('diagnose_plant/', views.diagnose_plant, name='diagnose_plant'),
    path('register/', views.register_user, name='register_user'),
    path('profile/', views.profile_detail, name='profile_detail'),
    path('profiles/<str:firebase_uid>/', views.public_profile, name='public_profile'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('ai_search/', views.ai_search, name='ai_search'),
]
