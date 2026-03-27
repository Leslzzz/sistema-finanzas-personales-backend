from django.urls import path
from .views import (
    RegisterView, 
    MyTokenObtainPairView, 
    LogoutView, 
    DashboardHomeView,
    CustomTokenRefreshView 
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/home/', DashboardHomeView.as_view(), name='dashboard_home'),
        path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
]