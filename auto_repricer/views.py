from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Avg, Count, Sum, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
import random

from .models import UserProduct, Competitor, RepricingRule, RepricingHistory


class AutoRepricerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'auto_repricer/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user products
        user_products = UserProduct.objects.filter(user=user)
        context['total_products'] = user_products.count()
        context['active_products'] = user_products.filter(is_active=True).count()
        
        # Buy Box statistics
        buy_box_winners = user_products.filter(buy_box_status=True).count()
        if context['total_products'] > 0:
            buy_box_percentage = (buy_box_winners / context['total_products']) * 100
        else:
            buy_box_percentage = 0
            
        context['buy_box_winners'] = buy_box_winners
        context['buy_box_percentage'] = round(buy_box_percentage, 1)
        
        # Get recent products
        context['recent_products'] = user_products.order_by('-created_at')[:5]
        
        # Get active repricing rules
        rules = RepricingRule.objects.filter(user=user, is_active=True)
        context['active_rules'] = rules.count()
        context['recent_rules'] = rules.order_by('-created_at')[:5]
        
        # Get recent repricing actions
        repricing_history = RepricingHistory.objects.filter(
            product__user=user
        ).order_by('-timestamp')[:10]
        
        context['recent_repricing'] = repricing_history
        
        # If no real repricing history, generate mock data for demonstration
        if not repricing_history:
            context['recent_repricing'] = []
            for product in user_products[:5]:
                previous_price = float(product.current_price)
                new_price = previous_price * (1 + random.uniform(-0.05, 0.05))
                context['recent_repricing'].append({
                    'product': product,
                    'timestamp': timezone.now() - timedelta(hours=random.randint(1, 48)),
                    'old_price': previous_price,
                    'new_price': round(new_price, 2),
                    'rule_name': 'Beat Lowest Price' if random.choice([True, False]) else 'Fixed Margin',
                    'buy_box_won': random.choice([True, False, False, True])  # 50% chance of winning
                })
        
        # Generate chart data for Buy Box win rate trend
        days = 14
        labels = [(timezone.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days-1, -1, -1)]
        
        # In a real implementation, this would be calculated from actual data
        win_rate_data = []
        base_win_rate = context['buy_box_percentage']
        
        for i in range(days):
            # Fluctuate win rate between +/- 15% of current rate
            variation = random.uniform(-15, 15)
            win_rate = base_win_rate + variation
            # Keep within 0-100 range
            win_rate = max(0, min(100, win_rate))
            win_rate_data.append(round(win_rate, 1))
        
        context['buy_box_trend_chart'] = {
            'labels': labels,
            'data': win_rate_data
        }
        
        # Calculate profit margin data
        total_profit = 0
        average_margin = 0
        
        if user_products:
            for product in user_products:
                total_profit += product.profit_amount
            
            average_margin = sum(product.profit_margin for product in user_products) / len(user_products)
        
        context['total_profit'] = total_profit
        context['average_margin'] = round(average_margin, 1)
        
        # Marketplace distribution
        amazon_count = user_products.filter(marketplace='amazon').count()
        ebay_count = user_products.filter(marketplace='ebay').count()
        walmart_count = user_products.filter(marketplace='walmart').count()
        other_count = user_products.exclude(marketplace__in=['amazon', 'ebay', 'walmart']).count()
        
        context['marketplace_distribution'] = {
            'labels': ['Amazon', 'eBay', 'Walmart', 'Other'],
            'data': [amazon_count, ebay_count, walmart_count, other_count]
        }
        
        # Buy Box win rate by marketplace
        if user_products:
            amazon_win_rate = 0
            ebay_win_rate = 0
            walmart_win_rate = 0
            
            amazon_products = user_products.filter(marketplace='amazon')
            if amazon_products:
                amazon_winners = amazon_products.filter(buy_box_status=True).count()
                amazon_win_rate = (amazon_winners / amazon_products.count()) * 100
                
            ebay_products = user_products.filter(marketplace='ebay')
            if ebay_products:
                ebay_winners = ebay_products.filter(buy_box_status=True).count()
                ebay_win_rate = (ebay_winners / ebay_products.count()) * 100
                
            walmart_products = user_products.filter(marketplace='walmart')
            if walmart_products:
                walmart_winners = walmart_products.filter(buy_box_status=True).count()
                walmart_win_rate = (walmart_winners / walmart_products.count()) * 100
                
            context['marketplace_win_rates'] = {
                'labels': ['Amazon', 'eBay', 'Walmart'],
                'data': [
                    round(amazon_win_rate, 1),
                    round(ebay_win_rate, 1),
                    round(walmart_win_rate, 1)
                ]
            }
        
        return context


class ProductListView(LoginRequiredMixin, ListView):
    model = UserProduct
    template_name = 'auto_repricer/product_list.html'
    context_object_name = 'products'
    
    def get_queryset(self):
        return UserProduct.objects.filter(user=self.request.user).order_by('-created_at')


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = UserProduct
    template_name = 'auto_repricer/product_detail.html'
    context_object_name = 'product'
    
    def get_queryset(self):
        return UserProduct.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        
        # Get competitors
        context['competitors'] = Competitor.objects.filter(product=product)
        
        # Get repricing history
        context['repricing_history'] = RepricingHistory.objects.filter(
            product=product
        ).order_by('-timestamp')[:10]
        
        # Get applied rules
        context['applied_rules'] = product.rules.filter(is_active=True)
        
        # Generate price history chart data
        days = 30
        labels = [(timezone.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days-1, -1, -1)]
        
        # In a real implementation, this would be actual price history
        price_history_data = []
        current_price = float(product.current_price)
        
        for i in range(days):
            # Random historical prices with some trend
            day_price = current_price * (1 + random.uniform(-0.15, 0.15))
            price_history_data.append(round(day_price, 2))
        
        # Order from oldest to newest
        price_history_data.reverse()
        
        context['price_history_chart'] = {
            'labels': labels,
            'data': price_history_data
        }
        
        return context


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = UserProduct
    template_name = 'auto_repricer/product_form.html'
    fields = [
        'name', 'sku', 'asin', 'marketplace', 'product_url', 
        'current_price', 'min_price', 'max_price', 'cost_price', 'is_active'
    ]
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Product added successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('auto_repricer:product_detail', kwargs={'pk': self.object.pk})


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = UserProduct
    template_name = 'auto_repricer/product_form.html'
    fields = [
        'name', 'sku', 'asin', 'marketplace', 'product_url', 
        'current_price', 'min_price', 'max_price', 'cost_price', 'is_active'
    ]
    
    def get_queryset(self):
        return UserProduct.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Product updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('auto_repricer:product_detail', kwargs={'pk': self.object.pk})


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = UserProduct
    template_name = 'auto_repricer/product_confirm_delete.html'
    success_url = reverse_lazy('auto_repricer:product_list')
    
    def get_queryset(self):
        return UserProduct.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Product deleted successfully.')
        return super().delete(request, *args, **kwargs)


class CompetitorCreateView(LoginRequiredMixin, CreateView):
    model = Competitor
    template_name = 'auto_repricer/competitor_form.html'
    fields = ['name', 'url', 'current_price', 'shipping_price', 'has_buy_box', 'is_active']
    
    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(UserProduct, pk=self.kwargs['product_id'], user=request.user)
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.product = self.product
        messages.success(self.request, 'Competitor added successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        return context
    
    def get_success_url(self):
        return reverse_lazy('auto_repricer:product_detail', kwargs={'pk': self.product.pk})


class CompetitorUpdateView(LoginRequiredMixin, UpdateView):
    model = Competitor
    template_name = 'auto_repricer/competitor_form.html'
    fields = ['name', 'url', 'current_price', 'shipping_price', 'has_buy_box', 'is_active']
    
    def dispatch(self, request, *args, **kwargs):
        self.competitor = get_object_or_404(Competitor, pk=self.kwargs['pk'])
        self.product = self.competitor.product
        
        # Ensure user owns the related product
        if self.product.user != request.user:
            messages.error(request, "You don't have permission to edit this competitor.")
            return redirect('auto_repricer:dashboard')
            
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Competitor updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('auto_repricer:product_detail', kwargs={'pk': self.product.pk})


class CompetitorDeleteView(LoginRequiredMixin, DeleteView):
    model = Competitor
    template_name = 'auto_repricer/competitor_confirm_delete.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.competitor = get_object_or_404(Competitor, pk=self.kwargs['pk'])
        self.product = self.competitor.product
        
        # Ensure user owns the related product
        if self.product.user != request.user:
            messages.error(request, "You don't have permission to delete this competitor.")
            return redirect('auto_repricer:dashboard')
            
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        return context
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Competitor deleted successfully.')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('auto_repricer:product_detail', kwargs={'pk': self.product.pk})


class RuleListView(LoginRequiredMixin, ListView):
    model = RepricingRule
    template_name = 'auto_repricer/rule_list.html'
    context_object_name = 'rules'
    
    def get_queryset(self):
        return RepricingRule.objects.filter(user=self.request.user).order_by('-created_at')


class RuleDetailView(LoginRequiredMixin, DetailView):
    model = RepricingRule
    template_name = 'auto_repricer/rule_detail.html'
    context_object_name = 'rule'
    
    def get_queryset(self):
        return RepricingRule.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rule = self.get_object()
        
        # Get products using this rule
        context['applied_products'] = rule.products.all()
        
        # Get repricing history for this rule
        context['repricing_history'] = RepricingHistory.objects.filter(
            rule=rule
        ).order_by('-timestamp')[:10]
        
        return context


class RuleCreateView(LoginRequiredMixin, CreateView):
    model = RepricingRule
    template_name = 'auto_repricer/rule_form.html'
    fields = [
        'name', 'rule_type', 'adjustment_value', 'is_percentage', 
        'min_profit_margin', 'custom_formula', 'apply_to_all_products', 'is_active'
    ]
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        
        response = super().form_valid(form)
        
        # If apply_to_all_products is checked, add all user's products to this rule
        if form.instance.apply_to_all_products:
            user_products = UserProduct.objects.filter(user=self.request.user)
            form.instance.products.add(*user_products)
        
        messages.success(self.request, 'Repricing rule created successfully.')
        return response
    
    def get_success_url(self):
        return reverse_lazy('auto_repricer:rule_detail', kwargs={'pk': self.object.pk})


class RuleUpdateView(LoginRequiredMixin, UpdateView):
    model = RepricingRule
    template_name = 'auto_repricer/rule_form.html'
    fields = [
        'name', 'rule_type', 'adjustment_value', 'is_percentage', 
        'min_profit_margin', 'custom_formula', 'apply_to_all_products', 'is_active'
    ]
    
    def get_queryset(self):
        return RepricingRule.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # If apply_to_all_products is checked, update products
        if form.instance.apply_to_all_products:
            user_products = UserProduct.objects.filter(user=self.request.user)
            form.instance.products.clear()
            form.instance.products.add(*user_products)
        
        messages.success(self.request, 'Repricing rule updated successfully.')
        return response
    
    def get_success_url(self):
        return reverse_lazy('auto_repricer:rule_detail', kwargs={'pk': self.object.pk})


class RuleDeleteView(LoginRequiredMixin, DeleteView):
    model = RepricingRule
    template_name = 'auto_repricer/rule_confirm_delete.html'
    success_url = reverse_lazy('auto_repricer:rule_list')
    
    def get_queryset(self):
        return RepricingRule.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Repricing rule deleted successfully.')
        return super().delete(request, *args, **kwargs)


class ManageProductRulesView(LoginRequiredMixin, TemplateView):
    template_name = 'auto_repricer/manage_product_rules.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(UserProduct, pk=self.kwargs['pk'], user=request.user)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        
        # Get all rules for this user
        context['available_rules'] = RepricingRule.objects.filter(
            user=self.request.user, is_active=True
        )
        
        # Get rules currently applied to this product
        context['applied_rules'] = self.product.rules.all()
        
        return context
    
    def post(self, request, *args, **kwargs):
        rule_ids = request.POST.getlist('rules')
        
        # Clear existing rules and add selected ones
        self.product.rules.clear()
        
        if rule_ids:
            rules = RepricingRule.objects.filter(id__in=rule_ids, user=request.user)
            self.product.rules.add(*rules)
            messages.success(request, f'Rules updated for {self.product.name}.')
        else:
            messages.warning(request, f'No rules are now applied to {self.product.name}.')
            
        return redirect('auto_repricer:product_detail', pk=self.product.pk)


class BulkImportProductsView(LoginRequiredMixin, TemplateView):
    template_name = 'auto_repricer/bulk_import_products.html'
    
    def post(self, request, *args, **kwargs):
        products_text = request.POST.get('products_text', '').strip()
        marketplace = request.POST.get('marketplace', 'amazon')
        
        if not products_text:
            messages.error(request, 'Please provide product data to import.')
            return self.get(request, *args, **kwargs)
        
        # Split the text by lines and process each product
        product_lines = products_text.split('\n')
        imported_count = 0
        
        for line in product_lines:
            line = line.strip()
            if not line:
                continue
                
            # Try to parse product data in the format: Name, SKU, ASIN, Price, Min Price, Max Price, Cost
            parts = [part.strip() for part in line.split(',')]
            
            if len(parts) < 5:  # Need at least Name, SKU, Price, Min, Max
                continue
                
            try:
                name = parts[0]
                sku = parts[1]
                current_price = float(parts[2].replace('$', ''))
                min_price = float(parts[3].replace('$', ''))
                max_price = float(parts[4].replace('$', ''))
                
                # Cost price is optional, default to 70% of current price if not provided
                cost_price = current_price * 0.7
                if len(parts) >= 6:
                    cost_price = float(parts[5].replace('$', ''))
                
                # ASIN is optional
                asin = None
                if len(parts) >= 7:
                    asin = parts[6]
                
                # Create the product
                product_url = f"https://example.com/product/{sku}"  # Placeholder URL
                
                UserProduct.objects.create(
                    user=request.user,
                    name=name,
                    sku=sku,
                    asin=asin,
                    marketplace=marketplace,
                    product_url=product_url,
                    current_price=current_price,
                    min_price=min_price,
                    max_price=max_price,
                    cost_price=cost_price,
                    is_active=True
                )
                
                imported_count += 1
                
            except (ValueError, IndexError) as e:
                continue  # Skip invalid lines
        
        if imported_count > 0:
            messages.success(request, f'Successfully imported {imported_count} products.')
        else:
            messages.warning(request, 'No valid product data was found to import.')
            
        return redirect('auto_repricer:product_list')


class AnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'auto_repricer/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user products
        user_products = UserProduct.objects.filter(user=user)
        
        # Overall statistics
        context.update({
            'total_products': user_products.count(),
            'active_products': user_products.filter(is_active=True).count(),
            'buy_box_winners': user_products.filter(buy_box_status=True).count(),
            'total_competitors': Competitor.objects.filter(product__user=user).count(),
            'total_rules': RepricingRule.objects.filter(user=user).count()
        })
        
        # Calculate average profit margin
        total_margin = 0
        for product in user_products:
            total_margin += product.profit_margin
            
        avg_margin = total_margin / max(len(user_products), 1)
        context['average_margin'] = round(avg_margin, 2)
        
        # Recent repricing actions
        context['recent_repricing'] = RepricingHistory.objects.filter(
            product__user=user
        ).order_by('-timestamp')[:10]
        
        # Generate profit margin by marketplace chart
        amazon_margin = 0
        ebay_margin = 0
        walmart_margin = 0
        
        amazon_products = user_products.filter(marketplace='amazon')
        if amazon_products:
            amazon_margin = sum(p.profit_margin for p in amazon_products) / len(amazon_products)
            
        ebay_products = user_products.filter(marketplace='ebay')
        if ebay_products:
            ebay_margin = sum(p.profit_margin for p in ebay_products) / len(ebay_products)
            
        walmart_products = user_products.filter(marketplace='walmart')
        if walmart_products:
            walmart_margin = sum(p.profit_margin for p in walmart_products) / len(walmart_products)
            
        context['marketplace_margins'] = {
            'labels': ['Amazon', 'eBay', 'Walmart'],
            'data': [
                round(amazon_margin, 2),
                round(ebay_margin, 2),
                round(walmart_margin, 2)
            ]
        }
        
        # Generate Buy Box win rate trend over time (mock data)
        days = 90  # Last 90 days
        labels = [(timezone.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days-1, -1, -1)]
        
        # Create mock data for Buy Box win rate over time
        win_rate_data = []
        base_rate = 60  # Starting point
        for i in range(days):
            # Random daily fluctuation
            rate_change = random.uniform(-5, 5)
            
            # Add an upward trend over time to simulate improvement
            trend_factor = i / days * 10  # Up to 10% improvement over the period
            
            rate = base_rate + rate_change + trend_factor
            # Keep within 0-100 range
            rate = max(0, min(100, rate))
            win_rate_data.append(round(rate, 1))
        
        context['win_rate_trend'] = {
            'labels': labels,
            'data': win_rate_data
        }
        
        # Most profitable products
        top_products = sorted(user_products, key=lambda p: p.profit_amount, reverse=True)[:5]
        context['top_products'] = top_products
        
        return context


class RunRepricingView(LoginRequiredMixin, TemplateView):
    template_name = 'auto_repricer/run_repricing.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get active products
        context['active_products'] = UserProduct.objects.filter(
            user=user, is_active=True
        ).count()
        
        # Get active rules
        context['active_rules'] = RepricingRule.objects.filter(
            user=user, is_active=True
        ).count()
        
        return context
    
    def post(self, request, *args, **kwargs):
        scope = request.POST.get('scope', 'all')
        
        # Get products to reprice
        if scope == 'all':
            products = UserProduct.objects.filter(user=request.user, is_active=True)
        elif scope == 'amazon':
            products = UserProduct.objects.filter(
                user=request.user, is_active=True, marketplace='amazon'
            )
        elif scope == 'ebay':
            products = UserProduct.objects.filter(
                user=request.user, is_active=True, marketplace='ebay'
            )
        elif scope == 'walmart':
            products = UserProduct.objects.filter(
                user=request.user, is_active=True, marketplace='walmart'
            )
        else:
            products = []
        
        # Simulate repricing process (in a real app, this would call the actual repricing logic)
        repriced_count = 0
        buy_box_wins = 0
        
        for product in products:
            # Get active rule for this product
            rule = product.active_rule
            if not rule:
                continue
                
            # Get competitors for this product
            competitors = Competitor.objects.filter(product=product, is_active=True)
            
            # Calculate new price based on rule
            old_price = product.current_price
            new_price = rule.calculate_new_price(product, competitors)
            
            # Only create history if price actually changed
            if new_price != old_price:
                # Update product price
                product.previous_price = old_price
                product.current_price = new_price
                product.last_repriced = timezone.now()
                
                # Random Buy Box status for demonstration (in reality, this would be determined by marketplace data)
                won_buy_box = random.choice([True, False])
                product.buy_box_status = won_buy_box
                
                if won_buy_box:
                    buy_box_wins += 1
                    
                product.save()
                
                # Create repricing history entry
                RepricingHistory.objects.create(
                    product=product,
                    rule=rule,
                    old_price=old_price,
                    new_price=new_price,
                    buy_box_won=won_buy_box,
                    rule_name=rule.name,
                    timestamp=timezone.now()
                )
                
                repriced_count += 1
        
        if repriced_count > 0:
            messages.success(
                request, 
                f'Successfully repriced {repriced_count} products. Won {buy_box_wins} Buy Boxes.'
            )
        else:
            messages.info(request, 'No products needed repricing at this time.')
            
        return redirect('auto_repricer:dashboard')


class RepricingHistoryView(LoginRequiredMixin, ListView):
    model = RepricingHistory
    template_name = 'auto_repricer/repricing_history.html'
    context_object_name = 'history_entries'
    
    def get_queryset(self):
        return RepricingHistory.objects.filter(
            product__user=self.request.user
        ).order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add some overall statistics
        entries = self.get_queryset()
        context['total_entries'] = entries.count()
        context['buy_box_wins'] = entries.filter(buy_box_won=True).count()
        
        if context['total_entries'] > 0:
            win_rate = (context['buy_box_wins'] / context['total_entries']) * 100
            context['win_rate'] = round(win_rate, 1)
        else:
            context['win_rate'] = 0
            
        return context


class StartRepricingView(LoginRequiredMixin, TemplateView):
    template_name = 'auto_repricer/start_repricing.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get active products
        context['active_products'] = UserProduct.objects.filter(
            user=user, is_active=True
        ).count()
        
        # Get active rules
        context['active_rules'] = RepricingRule.objects.filter(
            user=user, is_active=True
        ).count()
        
        # Get last repricing timestamp
        last_repricing = RepricingHistory.objects.filter(
            product__user=user
        ).order_by('-timestamp').first()
        
        if last_repricing:
            context['last_repricing'] = last_repricing.timestamp.strftime('%Y-%m-%d %H:%M')
        
        return context
    
    def post(self, request, *args, **kwargs):
        # Get active products
        products = UserProduct.objects.filter(user=request.user, is_active=True)
        
        # Apply filters based on scope
        scope = request.POST.get('scope', 'all')
        if scope == 'amazon':
            products = products.filter(marketplace='amazon')
        elif scope == 'ebay':
            products = products.filter(marketplace='ebay')
        elif scope == 'walmart':
            products = products.filter(marketplace='walmart')
        
        # Get force reprice parameter
        force_reprice = request.POST.get('force_reprice') == 'on'
        
        # Simulate repricing process
        repriced_count = 0
        buy_box_wins = 0
        
        for product in products:
            # Get active rules for this product
            rules = product.rules.filter(is_active=True)
            if not rules.exists():
                continue
                
            # Use the first active rule for simplicity
            rule = rules.first()
                
            # Get competitors for this product
            competitors = Competitor.objects.filter(product=product, is_active=True)
            
            # Calculate new price based on rule (simplified logic)
            old_price = float(product.current_price)
            
            # Simplified price adjustment - in reality would use complex logic
            if rule.rule_type == 'beat_competition':
                new_price = old_price * 0.95  # 5% lower
            elif rule.rule_type == 'match_competition':
                new_price = old_price  # match exactly
            elif rule.rule_type == 'fixed_margin':
                new_price = float(product.cost_price) * 1.25  # 25% margin
            else:
                new_price = old_price * (1 + random.uniform(-0.05, 0.05))  # random change
            
            # Ensure price is within min/max
            new_price = max(float(product.min_price), min(float(product.max_price), new_price))
            new_price = round(new_price, 2)
            
            # Only create history if price actually changed or force_reprice is checked
            if force_reprice or abs(new_price - old_price) > 0.01:
                # Update product price
                product.previous_price = old_price
                product.current_price = new_price
                product.last_repriced = timezone.now()
                
                # Randomly determine if we won the Buy Box (would be determined by marketplace data)
                won_buy_box = random.random() > 0.5
                product.buy_box_status = won_buy_box
                
                if won_buy_box:
                    buy_box_wins += 1
                    
                product.save()
                
                # Create repricing history entry
                RepricingHistory.objects.create(
                    product=product,
                    rule=rule,
                    old_price=old_price,
                    new_price=new_price,
                    buy_box_won=won_buy_box,
                    rule_name=rule.name,
                    timestamp=timezone.now()
                )
                
                repriced_count += 1
        
        if repriced_count > 0:
            messages.success(
                request, 
                f'Successfully repriced {repriced_count} products. Won {buy_box_wins} Buy Boxes.'
            )
        else:
            messages.info(request, 'No products needed repricing at this time.')
            
        return redirect('auto_repricer:dashboard')
