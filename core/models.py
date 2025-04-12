from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    """System notifications for users"""
    TYPE_CHOICES = [
        ('price_change', 'Price Change'),
        ('buybox_lost', 'Buy Box Lost'),
        ('buybox_won', 'Buy Box Won'),
        ('competitor_oos', 'Competitor Out of Stock'),
        ('system', 'System Notification'),
    ]
    
    LEVEL_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('error', 'Error'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='info')
    related_url = models.URLField(max_length=1000, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.notification_type}) for {self.user.email}"


class SystemSetting(models.Model):
    """System-wide settings"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_editable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.key


class UserSetting(models.Model):
    """User-specific settings"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='settings')
    key = models.CharField(max_length=100)
    value = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'key')
    
    def __str__(self):
        return f"{self.key} for {self.user.email}"


class ApiKey(models.Model):
    """API keys for third-party integrations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=255)
    secret = models.CharField(max_length=255, blank=True, null=True)
    service = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.service} - {self.name}"
