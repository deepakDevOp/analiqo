from django.urls import path
from . import views

app_name = 'auto_repricer'

urlpatterns = [
    path('', views.AutoRepricerDashboardView.as_view(), name='dashboard'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/add/', views.ProductCreateView.as_view(), name='product_add'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    path('rules/', views.RuleListView.as_view(), name='rule_list'),
    path('rules/add/', views.RuleCreateView.as_view(), name='rule_add'),
    path('rules/<int:pk>/', views.RuleDetailView.as_view(), name='rule_detail'),
    path('rules/<int:pk>/edit/', views.RuleUpdateView.as_view(), name='rule_edit'),
    path('rules/<int:pk>/delete/', views.RuleDeleteView.as_view(), name='rule_delete'),
    path('history/', views.RepricingHistoryView.as_view(), name='history'),
    path('start-repricing/', views.StartRepricingView.as_view(), name='start_repricing'),
]