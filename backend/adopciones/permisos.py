"""
AUTORIZACIÓN: ¿qué puedes hacer?

- Cualquier visitante puede consultar animales y enviar una solicitud.
- Solo un administrador (usuario staff) puede crear, editar o eliminar
  animales y consultar las solicitudes recibidas (datos personales).

Si no hay token, DRF responde 401; si hay token pero el usuario no es
administrador, responde 403.
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission


def es_administrador(request):
    return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class LecturaPublicaEscrituraAdmin(BasePermission):

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or es_administrador(request)


class EnvioPublicoConsultaAdmin(BasePermission):

    def has_permission(self, request, view):
        return request.method == 'POST' or es_administrador(request)
