from django.urls import path

from .views import CategoryListView, ExpenseListCreateView, SummaryView

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('expenses/', ExpenseListCreateView.as_view(), name='expense-list-create'),
    path('summary/', SummaryView.as_view(), name='summary'),
]