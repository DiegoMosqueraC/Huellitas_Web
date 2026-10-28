"""
Rutas del proyecto:
- /api/...   API REST (JSON)
- /admin/    panel de administración de Django
- /...       frontend (HTML + CSS + JS de la carpeta refugio-html5)
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve


def frontend(request, ruta=''):
    respuesta = serve(request, ruta or 'index.html', document_root=settings.FRONTEND_DIR)
    # El navegador revalida cada archivo, así los cambios en HTML/CSS/JS se ven al recargar.
    respuesta['Cache-Control'] = 'no-cache'
    return respuesta


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('adopciones.urls')),
    re_path(r'^(?P<ruta>.*)$', frontend),
]
