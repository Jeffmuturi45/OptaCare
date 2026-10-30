from django.urls import path
from core.views import patients as v

urlpatterns = [
    path('',             v.patient_list,         name='patient_list'),
    path('register/',    v.patient_register,     name='patient_register'),
    path('<int:pk>/',    v.patient_detail,        name='patient_detail'),
    path('search/',      v.patient_search_ajax,  name='patient_search'),
]
