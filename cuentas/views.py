from django.shortcuts import render
from rest_framework import generics 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Sum
from finanzas.models import Income, Outcome

from .serializers import RegisterSerializer, MyTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class DashboardHomeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        total_in = Income.objects.filter(transaction__user=user).aggregate(Sum('amount'))['amount__sum'] or 0
        total_out = Outcome.objects.filter(transaction__user=user).aggregate(Sum('expense'))['expense__sum'] or 0
        balance = total_in - total_out

        return Response({
            "user_info": {
                "name": user.name,
                "email": user.email,
                "created_at": user.created_at.strftime('%B %Y')
            },
            "summary": {
                "balance_total": float(balance),
                "total_income": float(total_in),
                "total_outcome": float(total_out)
            }
        })