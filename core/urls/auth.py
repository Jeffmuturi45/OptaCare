from django.urls import path
from core.views import auth as v
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


@login_required
def ping(request):
    return JsonResponse({'ok': True})


urlpatterns = [
    path('login/',          v.login_view,         name='login'),
    path('logout/',         v.logout_view,         name='logout'),
    path('pin/',            v.pin_view,            name='pin_verify'),
    path('branch-select/',  v.branch_select_view,  name='branch_select'),
    path('ping/',           ping,                  name='auth_ping'),
]
