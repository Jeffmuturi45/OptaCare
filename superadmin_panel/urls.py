from django.urls import path
from superadmin_panel import views as v

urlpatterns = [
    path('',        v.dashboard, name='superadmin_dashboard'),
    path('users/',  v.users,     name='superadmin_users'),
    path('branches/', v.branches, name='superadmin_branches'),
]
