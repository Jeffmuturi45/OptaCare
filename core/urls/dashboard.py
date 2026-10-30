from django.urls import path
from core.views import dashboard as v

urlpatterns = [
    path('', v.dashboard_view, name='dashboard'),
]
