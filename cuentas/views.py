from tokenize import TokenError

from django.shortcuts import render
from django.conf import settings
from django.db.models import Sum
from jwt import InvalidTokenError
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

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
                secure=True,
                samesite='None',
                max_age=3600
            )
            
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure=True,
                samesite='None',
                max_age=86400 * 7
            )
            
            if 'access' in response.data: del response.data['access']
            if 'refresh' in response.data: del response.data['refresh']

        return response

class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        
        if refresh_token:
            request.data['refresh'] = refresh_token

        try:
            response = super().post(request, *args, **kwargs)
            
            if response.status_code == 200:
                access_token = response.data.get('access')
                
                response.set_cookie(
                    key='access_token',
                    value=access_token,
                    httponly=True,
                    secure=True,
                    samesite='None',
                    max_age=3600
                )
                
                if 'access' in response.data: del response.data['access']
                new_refresh = response.data.get('refresh')
                if new_refresh:
                    response.set_cookie(
                        key='refresh_token',
                        value=new_refresh,
                        httponly=True,
                        secure=True,
                        samesite='None',
                        max_age=86400 * 7
                    )
                    del response.data['refresh']
                
            return response
        except (InvalidTokenError, TokenError):
            return Response({"detail": "Sesión expirada"}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    def post(self, request):
        response = Response({"message": "Sesión cerrada correctamente"}, status=status.HTTP_200_OK)
        response.delete_cookie('access_token', samesite='None')
        response.delete_cookie('refresh_token', samesite='None')
        return response

class DashboardHomeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            total_in = Income.objects.filter(transaction__user=user).aggregate(Sum('amount'))['amount__sum'] or 0
            total_out = Outcome.objects.filter(transaction__user=user).aggregate(Sum('expense'))['expense__sum'] or 0
            balance = float(total_in) - float(total_out)

            return Response({
                "user_info": {
                    "name": getattr(user, 'name', 'Usuario'),
                    "email": user.email,
                    "created_at": user.created_at.strftime('%B %Y') if user.created_at else "Reciente"
                },
                "summary": {
                    "balance_total": balance,
                    "total_income": float(total_in),
                    "total_outcome": float(total_out)
                }
            })
        except Exception as e:
            print(f"Error crítico en Dashboard: {str(e)}")
            return Response({"error": "Error interno al calcular balance"}, status=500)