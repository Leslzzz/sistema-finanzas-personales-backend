from django.urls import path
from .views import (
    RegisterView,
    MyTokenObtainPairView,
    LogoutView,
    DashboardHomeView,
    MeView,
    ProfileView,
    ProfilePasswordView,
    ProfileAvatarView,
    ProfilePreferencesView,
    ProfileNotificationsView,
)

urlpatterns = [
    # ── Auth ───────────────────────────────────────────────────────────────
    path('auth/register', RegisterView.as_view(), name='auth_register'),
    path('auth/login', MyTokenObtainPairView.as_view(), name='auth_login'),
    path('auth/me', MeView.as_view(), name='auth_me'),
    path('auth/logout', LogoutView.as_view(), name='auth_logout'),

    # ── Profile ────────────────────────────────────────────────────────────
    path('profile', ProfileView.as_view(), name='profile'),
    path('profile/password', ProfilePasswordView.as_view(), name='profile_password'),
    path('profile/avatar', ProfileAvatarView.as_view(), name='profile_avatar'),
    path('profile/preferences', ProfilePreferencesView.as_view(), name='profile_preferences'),
    path('profile/notifications', ProfileNotificationsView.as_view(), name='profile_notifications'),

    # ── Misc ───────────────────────────────────────────────────────────────
    path('dashboard/home', DashboardHomeView.as_view(), name='dashboard_home'),
]
