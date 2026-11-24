"""Endpoints de la API (rutas → controladores)."""
from django.urls import path, re_path

from . import views

urlpatterns = [
    path('animales/', views.AnimalesController.as_view(), name='animales'),
    path('animales/<int:id>/', views.AnimalDetalleController.as_view(), name='animal-detalle'),
    path('solicitudes/', views.SolicitudesController.as_view(), name='solicitudes'),
    path('solicitudes/consulta/', views.ConsultaSolicitudController.as_view(), name='solicitud-consulta'),
    path('solicitudes/<int:id>/', views.SolicitudDetalleController.as_view(), name='solicitud-detalle'),
    path('voluntarios/', views.VoluntariosController.as_view(), name='voluntarios'),
    path('voluntarios/<int:id>/', views.VoluntarioDetalleController.as_view(), name='voluntario-detalle'),
    path('jornadas/', views.JornadasController.as_view(), name='jornadas'),
    path('sesion/', views.SesionController.as_view(), name='sesion'),
    re_path(r'^(?P<ruta>.*)$', views.ruta_no_encontrada),
]
