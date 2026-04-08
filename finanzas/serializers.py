from rest_framework import serializers
from django.db import transaction as db_transaction
from .models import Transaction, Category, Income, Outcome


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'budget']

    def create(self, validated_data):
        user = self.context['request'].user
        return Category.objects.create(user=user, **validated_data)


class TransactionSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, write_only=True)
    type = serializers.ChoiceField(choices=['INCOME', 'OUTCOME'], write_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'description', 'date', 'document_type', 'url_document', 'category', 'amount', 'type']

    def create(self, validated_data):
        amount = validated_data.pop('amount')
        trans_type = validated_data.pop('type')
        user = serializers.HiddenField(default=serializers.CurrentUserDefault())


        with db_transaction.atomic():
            transaction = Transaction.objects.create(user=user, **validated_data)
            if trans_type == 'INCOME':
                Income.objects.create(transaction=transaction, amount=amount)
            else:
                Outcome.objects.create(transaction=transaction, expense=amount)
        return transaction