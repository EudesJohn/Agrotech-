from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    firebase_uid = models.CharField(max_length=128, unique=True, null=True, blank=True)
    USER_TYPES = (
        ('FARMER', 'Producteur'),
        ('BUYER', 'Acheteur (Restaurant/Supermarché)'),
        ('EXPORTER', 'Exportateur'),
        ('PROCESSOR', 'Transformateur'),
        ('SUPPLIER', "Fournisseur d'intrants"),
        ('TRANSPORTER', 'Transporteur'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='FARMER')
    phone_number = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)
    
    # Social features (Cache local if needed, but primary is Firestore)
    bio = models.TextField(blank=True, help_text="Déscription courte de l'utilisateur")
    experience = models.TextField(blank=True, help_text="Expériences agricoles et parcours")
    profile_picture = models.URLField(max_length=500, blank=True, null=True, help_text="URL de l'image de profil")

    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"

class ScanHistory(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='scan_history')
    image_base64 = models.TextField()
    diagnostic = models.JSONField()
    scanned_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    feda_transaction_id = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Scan by {self.user.user.username} - {self.scanned_at}"

class MarketPrice(models.Model):
    product_name = models.CharField(max_length=100)
    market_location = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Prix du jour en FCFA")
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product_name} at {self.market_location} - {self.price} FCFA"
