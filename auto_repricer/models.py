from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

class UserProduct(models.Model):
    """Model representing a user's product that will be automatically repriced"""
    
    MARKETPLACE_CHOICES = [
        ('amazon', 'Amazon'),
        ('ebay', 'eBay'),
        ('walmart', 'Walmart'),
        ('etsy', 'Etsy'),
        ('shopify', 'Shopify'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, help_text="Stock Keeping Unit")
    asin = models.CharField(max_length=20, blank=True, null=True, help_text="Amazon Standard Identification Number")
    marketplace = models.CharField(max_length=50, choices=MARKETPLACE_CHOICES, default='amazon')
    product_url = models.URLField(max_length=2000)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    min_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Minimum price floor")
    max_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Maximum price ceiling")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Product cost price")
    buy_box_status = models.BooleanField(default=False, help_text="Whether this product is winning the Buy Box")
    is_active = models.BooleanField(default=True)
    last_repriced = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    @property
    def profit_margin(self):
        """Calculate current profit margin percentage"""
        if self.current_price <= 0 or self.cost_price <= 0:
            return 0
        
        profit = self.current_price - self.cost_price
        margin = (profit / self.current_price) * 100
        return round(margin, 2)
    
    @property
    def profit_amount(self):
        """Calculate current profit amount"""
        return self.current_price - self.cost_price
    
    @property
    def active_rule(self):
        """Return the active repricing rule for this product, if any"""
        return self.rules.filter(is_active=True).first()


class Competitor(models.Model):
    """Model representing a competitor's product that is tracked for repricing"""
    
    product = models.ForeignKey(UserProduct, on_delete=models.CASCADE, related_name='competitors')
    name = models.CharField(max_length=255, help_text="Competitor's product name or seller name")
    url = models.URLField(max_length=2000, help_text="URL to the competitor's product")
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    shipping_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    has_buy_box = models.BooleanField(default=False)
    last_checked = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} for {self.product.name}"
    
    @property
    def total_price(self):
        """Calculate total price including shipping"""
        if self.current_price is None:
            return None
        return self.current_price + self.shipping_price


class RepricingRule(models.Model):
    """Model representing a repricing rule applied to products"""
    
    RULE_TYPE_CHOICES = [
        ('match_lowest', 'Match Lowest Price'),
        ('beat_lowest', 'Beat Lowest Price'),
        ('match_buy_box', 'Match Buy Box'),
        ('beat_buy_box', 'Beat Buy Box'),
        ('fixed_margin', 'Fixed Margin'),
        ('dynamic_margin', 'Dynamic Margin'),
        ('custom', 'Custom Formula'),
    ]
    
    name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='repricing_rules')
    products = models.ManyToManyField(UserProduct, related_name='rules', blank=True)
    rule_type = models.CharField(max_length=50, choices=RULE_TYPE_CHOICES)
    adjustment_value = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, 
                                          help_text="Adjustment value (percentage or fixed amount)")
    is_percentage = models.BooleanField(default=True, help_text="If True, adjustment is a percentage")
    min_profit_margin = models.DecimalField(max_digits=6, decimal_places=2, default=10.00,
                                           help_text="Minimum profit margin percentage")
    custom_formula = models.TextField(blank=True, null=True, 
                                     help_text="Custom pricing formula (for custom rule type)")
    apply_to_all_products = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def product_count(self):
        """Return the number of products this rule applies to"""
        return self.products.count()
    
    def calculate_new_price(self, product, competitors):
        """
        Calculate the new price for a product based on this rule.
        This is a simplified placeholder for the actual pricing logic.
        In a real application, this would implement complex repricing algorithms.
        """
        if not competitors or not product:
            return product.current_price
            
        # Get the lowest competitor price
        lowest_price = min([c.total_price for c in competitors if c.total_price is not None], 
                          default=product.current_price)
        
        # Get the buy box price if available
        buy_box_competitor = next((c for c in competitors if c.has_buy_box), None)
        buy_box_price = buy_box_competitor.total_price if buy_box_competitor else lowest_price
        
        # Calculate new price based on rule type
        new_price = product.current_price  # Default no change
        
        if self.rule_type == 'match_lowest':
            new_price = lowest_price
        elif self.rule_type == 'beat_lowest':
            adjustment = self.adjustment_value
            if self.is_percentage:
                adjustment = (lowest_price * self.adjustment_value) / 100
            new_price = lowest_price - adjustment
        elif self.rule_type == 'match_buy_box':
            new_price = buy_box_price
        elif self.rule_type == 'beat_buy_box':
            adjustment = self.adjustment_value
            if self.is_percentage:
                adjustment = (buy_box_price * self.adjustment_value) / 100
            new_price = buy_box_price - adjustment
        elif self.rule_type == 'fixed_margin':
            # Calculate price to achieve the desired margin
            desired_margin = self.adjustment_value
            if desired_margin >= 100:  # Prevent division by zero or negative prices
                desired_margin = 99.9
            new_price = product.cost_price / (1 - (desired_margin / 100))
        elif self.rule_type == 'dynamic_margin':
            # Dynamic margin adjusts based on competition
            # This is a simplified version
            if lowest_price > (product.cost_price * 1.5):  # Good margin available
                margin_factor = 0.8  # Aim for 80% of the margin available
                new_price = product.cost_price + ((lowest_price - product.cost_price) * margin_factor)
            else:  # Tight margin
                new_price = product.cost_price * (1 + (self.min_profit_margin / 100))
        
        # Ensure price is within min/max bounds
        new_price = max(product.min_price, min(product.max_price, new_price))
        
        # Ensure minimum profit margin is maintained
        min_acceptable_price = product.cost_price * (1 + (self.min_profit_margin / 100))
        new_price = max(min_acceptable_price, new_price)
        
        return round(new_price, 2)


class RepricingHistory(models.Model):
    """Model tracking the history of price changes from repricing rules"""
    
    product = models.ForeignKey(UserProduct, on_delete=models.CASCADE, related_name='repricing_history')
    rule = models.ForeignKey(RepricingRule, on_delete=models.SET_NULL, null=True, related_name='repricing_history')
    old_price = models.DecimalField(max_digits=10, decimal_places=2)
    new_price = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)
    buy_box_won = models.BooleanField(null=True, help_text="Whether this repricing resulted in winning the Buy Box")
    rule_name = models.CharField(max_length=100, help_text="Name of the rule at time of repricing")
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Repricing histories"
    
    def __str__(self):
        return f"{self.product.name} price changed from ${self.old_price} to ${self.new_price}"
    
    @property
    def price_difference(self):
        """Calculate the price difference"""
        return self.new_price - self.old_price
    
    @property
    def price_change_percentage(self):
        """Calculate percentage price change"""
        if self.old_price <= 0:
            return 0
        change = ((self.new_price - self.old_price) / self.old_price) * 100
        return round(change, 2)
