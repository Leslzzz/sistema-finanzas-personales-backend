from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed

class CustomCookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # Intentamos obtener el token de la cookie 'access_token'
        raw_token = request.COOKIES.get('access_token') or None
        
        # Si no hay cookie, probamos con el header
        if raw_token is None:
            header = self.get_header(request)
            if header:
                raw_token = self.get_raw_token(header)

        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except (InvalidToken, AuthenticationFailed):
            return None