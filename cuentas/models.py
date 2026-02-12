from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # Definición de roles sugerida por la asesoría empresarial [cite: 10]
    ROLE_CHOICES = (
        ('admin', 'Administrador'),
        ('usuario', 'Usuario Estándar'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='usuario')
    email = models.EmailField(unique=True) # Para garantizar integridad en el acceso

    def __str__(self):
        return f"{self.username} - {self.role}"
