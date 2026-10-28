"""
Los errores también se diseñan.

1. Excepciones de negocio que lanza la capa de servicio (no conocen HTTP,
   pero cada una sabe a qué código corresponde).
2. Manejador global que convierte CUALQUIER error de la API en una
   respuesta JSON clara, consistente y predecible:

   {
     "error": {
       "estado": 404,
       "codigo": "RECURSO_NO_ENCONTRADO",
       "mensaje": "No existe un animal con id 999.",
       "detalles": null,
       "ruta": "/api/animales/999/",
       "fecha": "2026-10-27T19:30:00-05:00"
     }
   }
"""
import logging

from django.http import Http404
from django.utils import timezone
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger('adopciones')


class ErrorDeNegocio(Exception):
    estado_http = status.HTTP_400_BAD_REQUEST
    codigo = 'ERROR_DE_NEGOCIO'

    def __init__(self, mensaje, detalles=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.detalles = detalles


class DatosInvalidos(ErrorDeNegocio):
    estado_http = status.HTTP_400_BAD_REQUEST
    codigo = 'DATOS_INVALIDOS'


class RecursoNoEncontrado(ErrorDeNegocio):
    estado_http = status.HTTP_404_NOT_FOUND
    codigo = 'RECURSO_NO_ENCONTRADO'


class Conflicto(ErrorDeNegocio):
    estado_http = status.HTTP_409_CONFLICT
    codigo = 'CONFLICTO'


class CredencialesInvalidas(ErrorDeNegocio):
    estado_http = status.HTTP_401_UNAUTHORIZED
    codigo = 'CREDENCIALES_INVALIDAS'


# Código y mensaje para los errores que genera el propio framework.
ERRORES_DEL_FRAMEWORK = {
    exceptions.ParseError: ('JSON_INVALIDO', 'El cuerpo de la solicitud no es un JSON válido.'),
    exceptions.ValidationError: ('DATOS_INVALIDOS', 'La solicitud tiene datos inválidos. Revisa los detalles.'),
    exceptions.NotAuthenticated: ('NO_AUTENTICADO', 'Debes enviar un token válido en el encabezado Authorization: Bearer <token>.'),
    exceptions.AuthenticationFailed: ('NO_AUTENTICADO', 'El token enviado no es válido.'),
    exceptions.PermissionDenied: ('SIN_PERMISO', 'Tu usuario no tiene permiso para realizar esta operación.'),
    exceptions.NotFound: ('RECURSO_NO_ENCONTRADO', 'El recurso solicitado no existe.'),
    Http404: ('RECURSO_NO_ENCONTRADO', 'El recurso solicitado no existe.'),
    exceptions.MethodNotAllowed: ('METODO_NO_PERMITIDO', 'Este endpoint no admite el método HTTP usado.'),
    exceptions.UnsupportedMediaType: ('TIPO_NO_SOPORTADO', 'Envía el cuerpo como application/json.'),
    exceptions.Throttled: ('DEMASIADOS_INTENTOS', 'Hiciste demasiados intentos seguidos. Espera un minuto e inténtalo de nuevo.'),
}


def cuerpo_de_error(estado, codigo, mensaje, detalles, ruta):
    return {
        'error': {
            'estado': estado,
            'codigo': codigo,
            'mensaje': mensaje,
            'detalles': detalles,
            'ruta': ruta,
            'fecha': timezone.localtime().isoformat(timespec='seconds'),
        }
    }


def manejador_de_errores(exc, context):
    request = context.get('request')
    ruta = request.path if request else ''

    if isinstance(exc, ErrorDeNegocio):
        respuesta = Response(
            cuerpo_de_error(exc.estado_http, exc.codigo, exc.mensaje, exc.detalles, ruta),
            status=exc.estado_http,
        )
        if exc.estado_http == status.HTTP_401_UNAUTHORIZED:
            respuesta['WWW-Authenticate'] = 'Bearer'
        return respuesta

    # Errores conocidos del framework: se conserva el código HTTP y los
    # encabezados (por ejemplo WWW-Authenticate en el 401), y se cambia el cuerpo.
    respuesta = exception_handler(exc, context)
    if respuesta is not None:
        codigo, mensaje = 'ERROR', 'No fue posible procesar la solicitud.'
        for tipo, (codigo_tipo, mensaje_tipo) in ERRORES_DEL_FRAMEWORK.items():
            if isinstance(exc, tipo):
                codigo, mensaje = codigo_tipo, mensaje_tipo
                break
        detalles = respuesta.data if isinstance(exc, exceptions.ValidationError) else None
        respuesta.data = cuerpo_de_error(respuesta.status_code, codigo, mensaje, detalles, ruta)
        return respuesta

    # Error inesperado: se registra para trazabilidad, pero al cliente no se
    # le muestran detalles internos (rutas, consultas, trazas).
    logger.exception('Error inesperado en %s %s', request.method if request else '', ruta)
    return Response(
        cuerpo_de_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            'ERROR_INTERNO',
            'Ocurrió un error inesperado en el servidor. Intenta de nuevo más tarde.',
            None,
            ruta,
        ),
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
