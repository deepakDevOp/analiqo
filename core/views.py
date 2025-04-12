from django.shortcuts import render, redirect
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from price_monitor.models import MonitoredURL, PriceHistory
from auto_repricer.models import UserProduct, RepricingRule, RepricingHistory
from datetime import datetime, timedelta
import random


class LandingPageView(View):
    """
    Landing page view that shows the landing page for unauthenticated users
    and redirects authenticated users to the dashboard.
    """
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('core:dashboard')
        return render(request, 'landing_page.html')


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'
    login_url = '/accounts/login/'
    redirect_field_name = 'next'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get price monitoring stats
        monitored_urls = MonitoredURL.objects.filter(user=user)
        context['monitored_urls_count'] = monitored_urls.count()
        context['active_monitored_urls'] = monitored_urls.filter(is_active=True).count()
        
        # Get auto repricer stats
        user_products = UserProduct.objects.filter(user=user)
        context['user_products_count'] = user_products.count()
        context['active_user_products'] = user_products.filter(is_active=True).count()
        
        # Buy Box stats
        buy_box_winners = user_products.filter(buy_box_status=True).count()
        if context['user_products_count'] > 0:
            win_rate = (buy_box_winners / context['user_products_count']) * 100
        else:
            win_rate = 0
        
        context['buy_box_wins'] = buy_box_winners
        context['buy_box_win_rate'] = round(win_rate, 1)
        
        # Recent notifications (placeholder until actual notifications are implemented)
        # In a real app, you would fetch actual notifications here
        context['recent_notifications'] = []
        
        # Mock data for price changes chart (in a real app, this would be from actual data)
        # Create chart data for price changes over the last 15 days
        days = 15
        labels = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days-1, -1, -1)]
        
        # Generate random price change percentages between -5% and +5%
        price_changes = []
        for _ in range(days):
            price_changes.append(round(random.uniform(-5, 5), 2))
        
        context['price_change_chart'] = {
            'labels': labels,
            'data': price_changes
        }
        
        # Recent price changes and repricing actions
        # In a real app, these would be actual database records
        
        # Mock recent price changes data
        context['recent_price_changes'] = []
        for url in monitored_urls[:5]:
            previous_price = round(random.uniform(50, 200), 2)
            price = previous_price * (1 + random.uniform(-0.1, 0.1))
            context['recent_price_changes'].append({
                'monitored_url': url,
                'timestamp': datetime.now() - timedelta(hours=random.randint(1, 72)),
                'price': round(price, 2),
                'previous_price': previous_price
            })
        
        # Mock recent repricing data
        context['recent_repricing'] = []
        for product in user_products[:5]:
            previous_price = float(product.current_price)
            new_price = previous_price * (1 + random.uniform(-0.05, 0.05))
            context['recent_repricing'].append({
                'product': product,
                'timestamp': datetime.now() - timedelta(hours=random.randint(1, 48)),
                'previous_price': previous_price,
                'new_price': round(new_price, 2),
                'buy_box_won': random.choice([True, False, True])  # 2/3 chance of winning
            })
        
        return context


class AboutView(TemplateView):
    template_name = 'core/about.html'


class ContactView(TemplateView):
    template_name = 'core/contact.html'


class PrivacyPolicyView(TemplateView):
    template_name = 'core/privacy_policy.html'


class TermsOfServiceView(TemplateView):
    template_name = 'core/terms_of_service.html'


class HelpCenterView(TemplateView):
    template_name = 'core/help_center.html'
