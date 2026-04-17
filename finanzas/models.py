import uuid

from django.db import models
from django.conf import settings


class MonthlyPeriod(models.Model):
    STATUS_CHOICES = [('active', 'Active'), ('closed', 'Closed')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='periods')
    year = models.IntegerField()
    month = models.IntegerField()
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [('user', 'year', 'month')]
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.user.email} | {self.year}-{self.month:02d} | {self.status}"


class Transaction(models.Model):
    TYPE_CHOICES = [('ingreso', 'Ingreso'), ('gasto', 'Gasto')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    period = models.ForeignKey(MonthlyPeriod, on_delete=models.CASCADE, null=True, blank=True, related_name='transactions')
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
    period = models.ForeignKey(MonthlyPeriod, on_delete=models.CASCADE, null=True, blank=True, related_name='budgets')
    label = models.CharField(max_length=100)
    icon = models.CharField(max_length=10)
    color = models.CharField(max_length=7)
    limit = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.label} ({self.user.email})"
