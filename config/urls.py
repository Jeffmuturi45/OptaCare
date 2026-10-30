from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('',          RedirectView.as_view(url='/auth/login/', permanent=False)),
    path('django-admin/', admin.site.urls),
    path('auth/',         include('core.urls.auth')),
    path('dashboard/',    include('core.urls.dashboard')),
    path('patients/',     include('core.urls.patients')),
    path('visits/',       include('core.urls.visits')),
    path('superadmin/',   include('superadmin_panel.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)