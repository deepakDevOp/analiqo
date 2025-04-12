from django.urls import path
from . import views

app_name = 'price_monitor'

urlpatterns = [
    # Dashboard
    path('', views.PriceMonitorDashboardView.as_view(), name='dashboard'),
    
    # URL Management
    path('urls/', views.MonitoredURLListView.as_view(), name='url_list'),
    path('urls/<int:pk>/', views.MonitoredURLDetailView.as_view(), name='url_detail'),
    path('urls/add/', views.MonitoredURLCreateView.as_view(), name='url_add'),
    path('urls/<int:pk>/edit/', views.MonitoredURLUpdateView.as_view(), name='url_edit'),
    path('urls/<int:pk>/delete/', views.MonitoredURLDeleteView.as_view(), name='url_delete'),
    
    # Bulk Import
    path('bulk-import/', views.BulkImportView.as_view(), name='bulk_import'),
    
    # Analytics
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
]