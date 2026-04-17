from tokenize import TokenError

from jwt import InvalidTokenError

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import User
from .serializers import RegisterSerializer, MyTokenObtainPairSerializer, get_tokens_for_user

try:
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False


def _profile_data(user):
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'avatarUrl': user.avatar_url,
        'timezone': user.timezone,
        'monthStartDay': user.month_start_day,
        'notifications': {
            'budgetAlert': user.budget_alert,
            'dailyReminder': user.daily_reminder,
        },
    }


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            if 'email' in serializer.errors:
                return Response({'message': 'Este email ya está registrado'}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        tokens = get_tokens_for_user(user)

        response = Response({
            'token': tokens['access'],
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
        }, status=status.HTTP_201_CREATED)

        response.set_cookie('access_token', tokens['access'], httponly=True, secure=True, samesite='None', max_age=3600)
        response.set_cookie('refresh_token', tokens['refresh'], httponly=True, secure=True, samesite='None', max_age=86400 * 7)
        return response


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code != 200:
            return Response({'message': 'Credenciales incorrectas'}, status=status.HTTP_401_UNAUTHORIZED)

        access_token = response.data.get('access')
        refresh_token = response.data.get('refresh')

        try:
            user = User.objects.get(email=request.data.get('email'))
        except User.DoesNotExist:
            return Response({'message': 'Credenciales incorrectas'}, status=status.HTTP_401_UNAUTHORIZED)

        response.set_cookie('access_token', access_token, httponly=True, secure=True, samesite='None', max_age=3600)
        response.set_cookie('refresh_token', refresh_token, httponly=True, secure=True, samesite='None', max_age=86400 * 7)

        response.data = {
            'token': access_token,
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
        }
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
                response.set_cookie('access_token', access_token, httponly=True, secure=True, samesite='None', max_age=3600)
                if 'access' in response.data:
                    del response.data['access']
                new_refresh = response.data.get('refresh')
                if new_refresh:
                    response.set_cookie('refresh_token', new_refresh, httponly=True, secure=True, samesite='None', max_age=86400 * 7)
                    del response.data['refresh']
            return response
        except (InvalidTokenError, TokenError):
            return Response({'detail': 'Sesión expirada'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    def post(self, request):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie('access_token', samesite='None')
        response.delete_cookie('refresh_token', samesite='None')
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from datetime import date
        from finanzas.models import MonthlyPeriod

        user = request.user
        today = date.today()
        has_period = MonthlyPeriod.objects.filter(
            user=user, year=today.year, month=today.month,
        ).exists()

        return Response({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'onboardingCompleted': user.onboarding_completed,
            'hasPeriodForCurrentMonth': has_period,
        })


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(_profile_data(request.user))

    def put(self, request):
        user = request.user
        name = request.data.get('name', user.name)
        email = request.data.get('email', user.email)

        if email != user.email and User.objects.filter(email=email).exclude(id=user.id).exists():
            return Response({'message': 'Email ya en uso'}, status=status.HTTP_400_BAD_REQUEST)

        user.name = name
        user.email = email
        user.save()
        return Response(_profile_data(user))

    def delete(self, request):
        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfilePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        if not user.check_password(request.data.get('currentPassword', '')):
            return Response({'message': 'Contraseña incorrecta'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(request.data.get('newPassword'))
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileAvatarView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def put(self, request):
        if not CLOUDINARY_AVAILABLE:
            return Response({'message': 'Almacenamiento de imágenes no configurado'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        avatar = request.FILES.get('avatar')
        if not avatar:
            return Response({'message': 'No se proporcionó imagen'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = cloudinary.uploader.upload(
                avatar,
                folder='finanzly/avatars',
                public_id=f'user_{request.user.id}',
                overwrite=True,
            )
            url = result.get('secure_url')
            request.user.avatar_url = url
            request.user.save()
            return Response({'avatarUrl': url})
        except Exception as e:
            return Response({'message': f'Error al subir imagen: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfilePreferencesView(APIView):
    permission_classes = [IsAuthenticated]

    VALID_TIMEZONES = ['America/Mexico_City', 'America/Monterrey', 'America/Tijuana', 'America/Cancun']
    VALID_START_DAYS = [1, 5, 10, 15, 16]

    def put(self, request):
        user = request.user
        timezone = request.data.get('timezone', user.timezone)
        month_start_day = request.data.get('monthStartDay', user.month_start_day)

        if timezone not in self.VALID_TIMEZONES:
            return Response({'message': 'Timezone inválido'}, status=status.HTTP_400_BAD_REQUEST)
        if int(month_start_day) not in self.VALID_START_DAYS:
            return Response({'message': 'monthStartDay inválido'}, status=status.HTTP_400_BAD_REQUEST)

        user.timezone = timezone
        user.month_start_day = int(month_start_day)
        user.save()
        return Response(_profile_data(user))


class ProfileNotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        user.budget_alert = request.data.get('budgetAlert', user.budget_alert)
        user.daily_reminder = request.data.get('dailyReminder', user.daily_reminder)
        user.save()
        return Response(_profile_data(user))


class DashboardHomeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from finanzas.models import Transaction
            from django.db.models import Sum
            user = request.user
            total_in = Transaction.objects.filter(user=user, type='ingreso').aggregate(Sum('amount'))['amount__sum'] or 0
            total_out = Transaction.objects.filter(user=user, type='gasto').aggregate(Sum('amount'))['amount__sum'] or 0
            balance = float(total_in) - float(total_out)
            return Response({
                'user_info': {
                    'name': user.name,
                    'email': user.email,
                    'created_at': user.created_at.strftime('%B %Y') if user.created_at else 'Reciente',
                },
                'summary': {
                    'balance_total': balance,
                    'total_income': float(total_in),
                    'total_outcome': float(total_out),
                },
            })
        except Exception:
            return Response({'error': 'Error interno al calcular balance'}, status=500)
