import uuid

from django.db import models
from django.conf import settings


class Transaction(models.Model):
    TYPE_CHOICES = [('ingreso', 'Ingreso'), ('gasto', 'Gasto')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    desc = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    category = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateField()

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.type} | {self.desc} | {self.amount}"


class Budget(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    label = models.CharField(max_length=100)
    icon = models.CharField(max_length=10)
    color = models.CharField(max_length=7)
    limit = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.label} ({self.user.email})"
