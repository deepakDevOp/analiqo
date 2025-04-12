from django.shortcuts import render, redirect
from django.views.generic import DetailView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from .models import UserProfile
from django.contrib import messages


class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'user_profile'
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ensure the user has a profile
        UserProfile.objects.get_or_create(user=self.request.user)
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    template_name = 'accounts/profile_edit.html'
    fields = ['company_name', 'phone_number']
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        # Get or create the user profile
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)


class SubscriptionView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/subscription.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        context['profile'] = profile
        
        # Plan details for display
        context['plans'] = {
            'basic': {
                'name': 'Basic',
                'price': '$29/month',
                'features': [
                    'Monitor up to 50 competitor URLs',
                    'Daily price tracking',
                    'Basic price alerts',
                    'Manual repricing suggestions'
                ]
            },
            'pro': {
                'name': 'Professional',
                'price': '$99/month',
                'features': [
                    'Monitor up to 500 competitor URLs',
                    'Hourly price tracking',
                    'Advanced price alerts',
                    'Automated repricing',
                    'Buy Box optimization',
                    'Priority support'
                ]
            },
            'enterprise': {
                'name': 'Enterprise',
                'price': '$299/month',
                'features': [
                    'Unlimited competitor URLs',
                    'Real-time price tracking',
                    'Comprehensive price alerts',
                    'Advanced automated repricing',
                    'Custom Buy Box optimization strategies',
                    'Dedicated account manager',
                    'API access'
                ]
            }
        }
        
        return context
    
    def post(self, request, *args, **kwargs):
        # Simple subscription plan change (in a real app, this would involve payment processing)
        plan = request.POST.get('plan')
        if plan in ['basic', 'pro', 'enterprise']:
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.subscription_plan = plan
            profile.save()
            messages.success(request, f'Your subscription has been updated to {plan.capitalize()}')
        else:
            messages.error(request, 'Invalid subscription plan selected')
        
        return redirect('accounts:subscription')
