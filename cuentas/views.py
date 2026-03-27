from django.shortcuts import render
from django.conf import settings
from django.db.models import Sum
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from finanzas.models import Income, Outcome
from .serializers import RegisterSerializer, MyTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')

            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=True, # Obligatorio para HTTPS
                samesite='None', # Obligatorio para Vercel -> Railway
                max_age=3600
            )
            
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure=True,
                samesite='None',
                max_age=86400
            )
            
            # Limpiamos el JSON por seguridad
            if 'access' in response.data: del response.data['access']
            if 'refresh' in response.data: del response.data['refresh']

        return response

class LogoutView(APIView):
    def post(self, request):
        response = Response({"message": "Sesión cerrada correctamente"}, status=status.HTTP_200_OK)
        # Borramos las cookies con los mismos parámetros de creación
        response.delete_cookie('access_token', samesite='None')
        response.delete_cookie('refresh_token', samesite='None')
        return response

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