from django.urls import path
from .views import (
    RegisterView,
    MyTokenObtainPairView,
    LogoutView,
    DashboardHomeView,
    CustomTokenRefreshView,
    MeView,
    ProfileView,
    ProfilePasswordView,
    ProfileAvatarView,
    ProfilePreferencesView,
    ProfileNotificationsView,
)

urlpatterns = [
    # ── Auth (spec paths) ──────────────────────────────────────────────────
    path('auth/register', RegisterView.as_view(), name='auth_register'),
    path('auth/login', MyTokenObtainPairView.as_view(), name='auth_login'),
    path('auth/me', MeView.as_view(), name='auth_me'),
    path('auth/logout', LogoutView.as_view(), name='auth_logout'),

    # ── Profile (spec paths) ───────────────────────────────────────────────
    path('profile', ProfileView.as_view(), name='profile'),
    path('profile/password', ProfilePasswordView.as_view(), name='profile_password'),
    path('profile/avatar', ProfileAvatarView.as_view(), name='profile_avatar'),
    path('profile/preferences', ProfilePreferencesView.as_view(), name='profile_preferences'),
    path('profile/notifications', ProfileNotificationsView.as_view(), name='profile_notifications'),

    # ── Legacy /api/ aliases (backward compat with existing frontend) ──────
    path('api/register/', RegisterView.as_view(), name='api_register'),
    path('api/login/', MyTokenObtainPairView.as_view(), name='api_login'),
    path('api/logout/', LogoutView.as_view(), name='api_logout'),
    path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('api/dashboard/home/', DashboardHomeView.as_view(), name='dashboard_home'),
]
