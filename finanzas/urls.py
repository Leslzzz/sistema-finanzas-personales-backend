from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import CategoryViewSet, TransactionViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
]