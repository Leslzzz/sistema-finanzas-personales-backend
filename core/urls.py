from django.contrib import admin
from django.urls import path, include
from cuentas.views import CustomTokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('cuentas.urls')),
    path('api/', include('finanzas.urls')),
    path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
]
