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
)

urlpatterns = [
    path('onboarding', OnboardingView.as_view(), name='onboarding'),

    path('transactions', TransactionListCreateView.as_view(), name='transactions'),
    path('transactions/summary', TransactionSummaryView.as_view(), name='transactions_summary'),
    path('transactions/categories', TransactionCategoriesView.as_view(), name='transactions_categories'),
    path('transactions/import', TransactionImportView.as_view(), name='transactions_import'),
    path('transactions/export', TransactionExportView.as_view(), name='transactions_export'),
    path('transactions/template', TransactionTemplateView.as_view(), name='transactions_template'),

    path('budgets', BudgetListView.as_view(), name='budgets'),
    path('budgets/<str:pk>', BudgetDetailView.as_view(), name='budget_detail'),
]
