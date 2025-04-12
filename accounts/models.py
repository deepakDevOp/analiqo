from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company_name = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    subscription_plan = models.CharField(max_length=20, 
                                        choices=[
                                            ('basic', 'Basic'),
                                            ('pro', 'Professional'),
                                            ('enterprise', 'Enterprise')
                                        ],
                                        default='basic') # create separate model for subscription/pricing
    subscription_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email}'s Profile"
