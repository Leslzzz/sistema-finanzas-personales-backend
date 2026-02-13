from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # Solo usa los campos que tú definiste en tu tabla de Postgres
    list_display = ('email', 'name', 'created_at')
    search_fields = ('email', 'name')
    ordering = ('email',)