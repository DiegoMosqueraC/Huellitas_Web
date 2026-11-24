"""Mapa del sitio: cada página pública tiene su propia dirección."""
from django.urls import path

from . import views

app_name = 'sitio'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('animales/', views.animales, name='animales'),
    path('animales/<int:id>/', views.ficha, name='ficha'),
    path('adoptar/', views.adoptar, name='adoptar'),
    path('voluntarios/', views.voluntarios, name='voluntarios'),
    path('mi-solicitud/', views.consulta, name='consulta'),
    path('contacto/', views.contacto, name='contacto'),
    path('panel/', views.panel, name='panel'),
]
