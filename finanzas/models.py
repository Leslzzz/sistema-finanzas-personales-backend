from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=50)
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.user.email})"

class Transaction(models.Model):
    DOCUMENT_TYPES = [('FACTURA', 'Factura'), ('TICKET', 'Ticket'), ('OTRO', 'Otro')]
    
    description = models.CharField(max_length=255)
    date = models.DateField(auto_now_add=True)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, blank=True, null=True)
    url_document = models.URLField(max_length=500, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)

    class Meta:
        ordering = ['-date']

class Income(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, primary_key=True, related_name='income_details')
    amount = models.DecimalField(max_digits=12, decimal_places=2)

class Outcome(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, primary_key=True, related_name='outcome_details')
    expense = models.DecimalField(max_digits=12, decimal_places=2)