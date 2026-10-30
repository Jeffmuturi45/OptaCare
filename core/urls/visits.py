from django.urls import path
from core.views import visits as v

urlpatterns = [
    path('',                        v.visit_list,       name='visit_list'),
    path('new/',                    v.visit_create,     name='visit_create'),
    path('<int:pk>/transition/',    v.visit_transition, name='visit_transition'),
    path('<int:pk>/triage/',        v.triage_submit,    name='triage_submit'),
]
