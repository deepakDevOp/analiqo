from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Avg, Count, F, Q, Max
from .models import MonitoredURL, PriceHistory, PriceAlert
import random
from datetime import datetime, timedelta

class PriceMonitorDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'price_monitor/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get monitored URLs
        monitored_urls = MonitoredURL.objects.filter(user=user)
        context['total_monitored'] = monitored_urls.count()
        context['active_monitored'] = monitored_urls.filter(is_active=True).count()
        
        # Get recent monitored URLs
        context['recent_monitored'] = monitored_urls.order_by('-created_at')[:5]
        
        # Mock price alerts (in a real implementation, these would be real alerts from the database)
        # In a production environment, we'd fetch real alerts based on price changes
        context['price_alerts'] = []
        
        # Add some mock alerts for demonstration
        for url in monitored_urls[:7]:  # Get up to 7 monitored URLs
            is_increase = random.choice([True, False])
            change_percent = random.uniform(5, 25) if is_increase else random.uniform(5, 20)
            
            context['price_alerts'].append({
                'url': url,
                'is_increase': is_increase,
                'change_percent': change_percent,
                'timestamp': datetime.now() - timedelta(hours=random.randint(1, 48))
            })
        
        # Generate chart data for price changes over the last 15 days
        days = 15
        labels = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days-1, -1, -1)]
        
        # Simulate some price fluctuations for the chart
        # In a real implementation, this would analyze actual price change data
        data = []
        price_change = 0
        
        for _ in range(days):
            # Random price change between -4% and +4%, with some smoothing
            new_change = random.uniform(-4, 4)
            price_change = (price_change * 0.3) + (new_change * 0.7)  # Smooth the changes
            data.append(round(price_change, 2))
        
        context['price_change_chart'] = {
            'labels': labels,
            'data': data
        }
        
        # Marketplace distribution data for pie chart
        amazon_count = monitored_urls.filter(marketplace='amazon').count()
        ebay_count = monitored_urls.filter(marketplace='ebay').count()
        walmart_count = monitored_urls.filter(marketplace='walmart').count()
        other_count = monitored_urls.exclude(
            marketplace__in=['amazon', 'ebay', 'walmart']
        ).count()
        
        context['marketplace_distribution'] = {
            'labels': ['Amazon', 'eBay', 'Walmart', 'Other'],
            'data': [amazon_count, ebay_count, walmart_count, other_count]
        }
        
        return context


class MonitoredURLListView(LoginRequiredMixin, ListView):
    model = MonitoredURL
    template_name = 'price_monitor/url_list.html'
    context_object_name = 'urls'
    
    def get_queryset(self):
        return MonitoredURL.objects.filter(user=self.request.user).order_by('-created_at')


class MonitoredURLDetailView(LoginRequiredMixin, DetailView):
    model = MonitoredURL
    template_name = 'price_monitor/url_detail.html'
    context_object_name = 'url'
    
    def get_queryset(self):
        return MonitoredURL.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        monitored_url = self.get_object()
        
        # Fetch price history or generate mock data if none exists
        price_history = PriceHistory.objects.filter(url=monitored_url).order_by('timestamp')
        
        if not price_history:
            # If no real price history exists, generate mock data for demonstration
            # In a real implementation, this would be actual price history
            days = 30
            mock_history = []
            current_price = float(monitored_url.current_price or 100)
            
            # Generate price entries for the last 30 days
            for i in range(days, -1, -1):
                date = datetime.now() - timedelta(days=i)
                # Add some random fluctuation, between -3% and +3% of the previous price
                fluctuation = random.uniform(-0.03, 0.03)
                current_price = current_price * (1 + fluctuation)
                
                mock_history.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'price': round(current_price, 2)
                })
            
            context['price_history'] = mock_history
            
            # Data for chart
            context['chart_data'] = {
                'labels': [item['date'] for item in mock_history],
                'prices': [item['price'] for item in mock_history]
            }
        else:
            # Use actual price history
            history_data = []
            for entry in price_history:
                history_data.append({
                    'date': entry.timestamp.strftime('%Y-%m-%d'),
                    'price': float(entry.price)
                })
            
            context['price_history'] = history_data
            
            # Data for chart
            context['chart_data'] = {
                'labels': [item['date'] for item in history_data],
                'prices': [item['price'] for item in history_data]
            }
        
        # Add price alerts
        context['price_alerts'] = PriceAlert.objects.filter(url=monitored_url).order_by('-created_at')[:10]
        
        return context


class MonitoredURLCreateView(LoginRequiredMixin, CreateView):
    model = MonitoredURL
    template_name = 'price_monitor/url_form.html'
    fields = [
        'name', 'url', 'marketplace', 'monitoring_frequency', 
        'alert_threshold_percentage', 'is_active'
    ]
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'URL added successfully for monitoring.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('price_monitor:url_detail', kwargs={'pk': self.object.pk})


class MonitoredURLUpdateView(LoginRequiredMixin, UpdateView):
    model = MonitoredURL
    template_name = 'price_monitor/url_form.html'
    fields = [
        'name', 'url', 'marketplace', 'monitoring_frequency', 
        'alert_threshold_percentage', 'is_active'
    ]
    
    def get_queryset(self):
        return MonitoredURL.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Monitored URL updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('price_monitor:url_detail', kwargs={'pk': self.object.pk})


class MonitoredURLDeleteView(LoginRequiredMixin, DeleteView):
    model = MonitoredURL
    template_name = 'price_monitor/url_confirm_delete.html'
    success_url = reverse_lazy('price_monitor:url_list')
    
    def get_queryset(self):
        return MonitoredURL.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Monitored URL deleted successfully.')
        return super().delete(request, *args, **kwargs)


class BulkImportView(LoginRequiredMixin, TemplateView):
    template_name = 'price_monitor/bulk_import.html'
    
    def post(self, request, *args, **kwargs):
        # Process bulk import
        urls_text = request.POST.get('urls_text', '').strip()
        marketplace = request.POST.get('marketplace', 'amazon')
        frequency = request.POST.get('frequency', 'daily')
        threshold = request.POST.get('threshold', 5.0)
        
        if not urls_text:
            messages.error(request, 'Please provide URLs to import.')
            return self.get(request, *args, **kwargs)
        
        # Split the text by lines and process each URL
        url_lines = urls_text.split('\n')
        imported_count = 0
        
        for line in url_lines:
            line = line.strip()
            if not line:
                continue
                
            # Parse name and URL if provided in format "Name - URL"
            if ' - ' in line:
                name, url = line.split(' - ', 1)
            else:
                name = f"Product {imported_count + 1}"
                url = line
            
            # Create the monitored URL
            MonitoredURL.objects.create(
                user=request.user,
                name=name,
                url=url,
                marketplace=marketplace,
                monitoring_frequency=frequency,
                alert_threshold_percentage=threshold,
                is_active=True
            )
            
            imported_count += 1
        
        if imported_count > 0:
            messages.success(request, f'Successfully imported {imported_count} URLs for monitoring.')
        else:
            messages.warning(request, 'No valid URLs were found to import.')
            
        return redirect('price_monitor:url_list')


class AnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'price_monitor/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get monitored URLs
        monitored_urls = MonitoredURL.objects.filter(user=user)
        
        # Overall statistics
        context.update({
            'total_urls': monitored_urls.count(),
            'active_urls': monitored_urls.filter(is_active=True).count(),
            'amazon_urls': monitored_urls.filter(marketplace='amazon').count(),
            'ebay_urls': monitored_urls.filter(marketplace='ebay').count(),
            'walmart_urls': monitored_urls.filter(marketplace='walmart').count()
        })
        
        # Price change statistics (in a real app, these would be calculated from actual data)
        context.update({
            'price_drops': random.randint(5, 25),
            'price_increases': random.randint(5, 20),
            'average_price_change': round(random.uniform(-5, 5), 2)
        })
        
        # Price history trend for all monitored products (mock data)
        days = 90  # Last 90 days
        labels = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days-1, -1, -1)]
        
        # Create mock data for price index (100 = baseline)
        base_value = 100
        price_trend = []
        for i in range(days):
            # Random daily fluctuation with slight upward bias
            change = random.uniform(-1.5, 2)
            base_value += change
            price_trend.append(round(base_value, 2))
        
        context['price_trend_chart'] = {
            'labels': labels,
            'data': price_trend
        }
        
        # Top price decreases in the last month
        top_decreases = []
        for i in range(5):  # Top 5
            if i < monitored_urls.count():
                url = monitored_urls[i]
                percent_decrease = random.uniform(5, 25)
                top_decreases.append({
                    'url': url,
                    'percent_decrease': round(percent_decrease, 1),
                    'date': datetime.now() - timedelta(days=random.randint(1, 30))
                })
        
        context['top_decreases'] = top_decreases
        
        # Distribution of price changes by marketplace
        context['marketplace_changes'] = {
            'labels': ['Amazon', 'eBay', 'Walmart', 'Other'],
            'decreases': [random.randint(5, 20) for _ in range(4)],
            'increases': [random.randint(5, 15) for _ in range(4)]
        }
        
        return context
