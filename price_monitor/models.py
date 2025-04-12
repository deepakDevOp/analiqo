from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

class MonitoredURL(models.Model):
    # Marketplace choices
    MARKETPLACE_CHOICES = [
        ('amazon', 'Amazon'),
        ('ebay', 'eBay'),
        ('walmart', 'Walmart'),
        ('etsy', 'Etsy'),
        ('shopify', 'Shopify'),
        ('target', 'Target'),
        ('best_buy', 'Best Buy'),
        ('newegg', 'Newegg'),
        ('other', 'Other'),
    ]
    
    # Monitoring frequency choices
    FREQUENCY_CHOICES = [
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='monitored_urls')
    name = models.CharField(max_length=255, help_text="Product name or identifier")
    url = models.URLField(max_length=2000, help_text="URL to monitor for price changes")
    marketplace = models.CharField(max_length=50, choices=MARKETPLACE_CHOICES, default='amazon')
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    previous_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    last_checked = models.DateTimeField(null=True, blank=True)
    monitoring_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    alert_threshold_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=5.00,
        help_text="Percentage change that triggers an alert"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def price_change_percentage(self):
        """Calculate percentage change between current and previous price"""
        if not self.current_price or not self.previous_price or self.previous_price == 0:
            return None
        
        change = ((self.current_price - self.previous_price) / self.previous_price) * 100
        return round(change, 2)
    
    @property
    def price_increased(self):
        """Check if price increased since last check"""
        if not self.current_price or not self.previous_price:
            return None
        return self.current_price > self.previous_price
    
    @property
    def price_decreased(self):
        """Check if price decreased since last check"""
        if not self.current_price or not self.previous_price:
            return None
        return self.current_price < self.previous_price
    
    @property
    def alert_needed(self):
        """Determine if price change exceeds alert threshold"""
        if self.price_change_percentage is None:
            return False
            
        return abs(self.price_change_percentage) >= self.alert_threshold_percentage


class PriceHistory(models.Model):
    url = models.ForeignKey(MonitoredURL, on_delete=models.CASCADE, related_name='price_history')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Price histories"
    
    def __str__(self):
        return f"{self.url.name} - ${self.price} on {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class PriceAlert(models.Model):
    url = models.ForeignKey(MonitoredURL, on_delete=models.CASCADE, related_name='price_alerts')
    old_price = models.DecimalField(max_digits=10, decimal_places=2)
    new_price = models.DecimalField(max_digits=10, decimal_places=2)
    percentage_change = models.DecimalField(max_digits=7, decimal_places=2)
    is_increase = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        change_type = "increased" if self.is_increase else "decreased"
        return f"{self.url.name} price {change_type} by {abs(self.percentage_change)}%"
    
    def save(self, *args, **kwargs):
        # Calculate percentage change and is_increase if not already set
        if not self.percentage_change or self.is_increase is None:
            if self.old_price > 0:
                self.percentage_change = ((self.new_price - self.old_price) / self.old_price) * 100
                self.is_increase = self.new_price > self.old_price
            
        super().save(*args, **kwargs)
