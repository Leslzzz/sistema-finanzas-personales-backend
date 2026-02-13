from django.contrib import admin
from .models import User

@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'created_at')
    ordering = ('email',)