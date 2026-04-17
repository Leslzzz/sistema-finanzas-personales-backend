from django.urls import path
from .views import (
    OnboardingView,
    TransactionListCreateView,
    TransactionSummaryView,
    TransactionCategoriesView,
    TransactionImportView,
    TransactionExportView,
    TransactionTemplateView,
    BudgetListView,
    BudgetDetailView,
    PeriodCurrentView,
    PeriodListView,
    PeriodDetailView,
    PeriodStartView,
    PeriodCloseView,
)

urlpatterns = [
    path('onboarding', OnboardingView.as_view(), name='onboarding'),

    path('periods/current', PeriodCurrentView.as_view(), name='period_current'),
    path('periods/start', PeriodStartView.as_view(), name='period_start'),
    path('periods', PeriodListView.as_view(), name='period_list'),
    path('periods/<int:pk>', PeriodDetailView.as_view(), name='period_detail'),
    path('periods/<int:pk>/close', PeriodCloseView.as_view(), name='period_close'),

    path('transactions', TransactionListCreateView.as_view(), name='transactions'),
    path('transactions/summary', TransactionSummaryView.as_view(), name='transactions_summary'),
    path('transactions/categories', TransactionCategoriesView.as_view(), name='transactions_categories'),
    path('transactions/import', TransactionImportView.as_view(), name='transactions_import'),
    path('transactions/export', TransactionExportView.as_view(), name='transactions_export'),
    path('transactions/template', TransactionTemplateView.as_view(), name='transactions_template'),

    path('budgets', BudgetListView.as_view(), name='budgets'),
    path('budgets/<str:pk>', BudgetDetailView.as_view(), name='budget_detail'),
]
