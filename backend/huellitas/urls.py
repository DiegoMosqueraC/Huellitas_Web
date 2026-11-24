"""
Rutas del proyecto:
- /api/...   API REST (JSON) de la app adopciones
- /admin/    panel de administración de Django
- /...       páginas del sitio (app sitio, plantillas de Django)
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('adopciones.urls')),
    path('', include('sitio.urls')),
]
