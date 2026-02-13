from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from cuentas.views import RegisterView, MyTokenObtainPairView, DashboardHomeView

urlpatterns = [
    path('admin/', admin.site.urls), 
    
    # Endpoints de Autenticación para la Landing Page
    path('api/register/', RegisterView.as_view(), name='auth_register'), # <--- ESTA ES LA QUE FALTA
    path('api/login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Endpoint para el Dashboard
    path('api/dashboard/home/', DashboardHomeView.as_view(), name='dashboard_home'),
]