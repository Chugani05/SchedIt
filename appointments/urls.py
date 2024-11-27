from django.urls import path

from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.appointment_list, name='appointment-list'),
    path('<int:appointment_pk>/', views.appointment_detail, name='appointment-detail'),
    path('add/', views.add_appointment, name='add-appointment'),
]
