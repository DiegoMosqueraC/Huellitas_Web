"""
AUTENTICACIÓN: ¿quién eres?

Acepta el encabezado "Authorization: Bearer <token>". Los tokens se crean
para los usuarios administradores de la fundación (ver README).
"""
from rest_framework.authentication import TokenAuthentication


class BearerTokenAuthentication(TokenAuthentication):
    keyword = 'Bearer'
