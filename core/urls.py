from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from cuentas.views import RegisterView, MyTokenObtainPairView, DashboardHomeView

urlpatterns = [
    path('admin/', admin.site.urls), 
    
    path('api/register/', RegisterView.as_view(), name='auth_register'),
    
    path('api/login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/dashboard/home/', DashboardHomeView.as_view(), name='dashboard_home'),
]