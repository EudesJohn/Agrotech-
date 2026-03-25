from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'phone_number', 'location')
    search_fields = ('user__username', 'phone_number')
    list_filter = ('user_type',)
