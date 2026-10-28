"""
CONTROLLER (capa de control).

Cada controlador:
- RECIBE parámetros, body y encabezados de la petición HTTP.
- Valida lo básico del formato con un serializer.
- COORDINA: llama al servicio adecuado.
- DEVUELVE el código HTTP y el JSON de respuesta.
No contiene reglas del negocio ni consultas a la base de datos.
Los errores que lanza el servicio los convierte en JSON el manejador
global de errores.py.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .errores import RecursoNoEncontrado
from .permisos import EnvioPublicoConsultaAdmin, LecturaPublicaEscrituraAdmin
from .serializers import (
    AnimalSerializer,
    InicioSesionSerializer,
    SolicitudCambioEstadoSerializer,
    SolicitudCreadaSerializer,
    SolicitudDetalleSerializer,
    SolicitudEntradaSerializer,
    VoluntarioCambioEstadoSerializer,
    VoluntarioDetalleSerializer,
    VoluntarioEntradaSerializer,
    VoluntarioRegistradoSerializer,
)
from .servicios import AnimalService, SesionService, SolicitudService, VoluntarioService


class AnimalesController(APIView):
    """GET /api/animales/  ·  POST /api/animales/"""
    permission_classes = [LecturaPublicaEscrituraAdmin]
    servicio = AnimalService()

    def get(self, request):
        animales = self.servicio.listar(
            especie=request.query_params.get('especie'),
            estado=request.query_params.get('estado'),
        )
        return Response(AnimalSerializer(animales, many=True).data)

    def post(self, request):
        entrada = AnimalSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        animal = self.servicio.crear(entrada.validated_data)
        return Response(
            AnimalSerializer(animal).data,
            status=status.HTTP_201_CREATED,
            headers={'Location': f'/api/animales/{animal.id}/'},
        )


class AnimalDetalleController(APIView):
    """GET, PUT, PATCH y DELETE /api/animales/{id}/"""
    permission_classes = [LecturaPublicaEscrituraAdmin]
    servicio = AnimalService()

    def get(self, request, id):
        return Response(AnimalSerializer(self.servicio.obtener(id)).data)

    def put(self, request, id):
        return self._actualizar(request, id, parcial=False)

    def patch(self, request, id):
        return self._actualizar(request, id, parcial=True)

    def delete(self, request, id):
        self.servicio.eliminar(id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _actualizar(self, request, id, parcial):
        entrada = AnimalSerializer(data=request.data, partial=parcial)
        entrada.is_valid(raise_exception=True)
        animal = self.servicio.actualizar(id, entrada.validated_data)
        return Response(AnimalSerializer(animal).data)


class SolicitudesController(APIView):
    """POST /api/solicitudes/ (público)  ·  GET /api/solicitudes/ (administrador)"""
    permission_classes = [EnvioPublicoConsultaAdmin]
    servicio = SolicitudService()

    def get(self, request):
        return Response(SolicitudDetalleSerializer(self.servicio.listar(), many=True).data)

    def post(self, request):
        entrada = SolicitudEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        solicitud = self.servicio.registrar(entrada.validated_data)
        return Response(
            SolicitudCreadaSerializer(solicitud).data,
            status=status.HTTP_201_CREATED,
            headers={'Location': f'/api/solicitudes/{solicitud.id}/'},
        )


class SolicitudDetalleController(APIView):
    """GET y PATCH /api/solicitudes/{id}/ (administrador)"""
    permission_classes = [EnvioPublicoConsultaAdmin]
    servicio = SolicitudService()

    def get(self, request, id):
        return Response(SolicitudDetalleSerializer(self.servicio.obtener(id)).data)

    def patch(self, request, id):
        entrada = SolicitudCambioEstadoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        solicitud = self.servicio.cambiar_estado(
            id, entrada.validated_data['estado'], entrada.validated_data['observacion']
        )
        return Response(SolicitudDetalleSerializer(solicitud).data)


class VoluntariosController(APIView):
    """POST /api/voluntarios/ (público)  ·  GET /api/voluntarios/ (administrador)"""
    permission_classes = [EnvioPublicoConsultaAdmin]
    servicio = VoluntarioService()

    def get(self, request):
        return Response(VoluntarioDetalleSerializer(self.servicio.listar(), many=True).data)

    def post(self, request):
        entrada = VoluntarioEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        voluntario = self.servicio.registrar(entrada.validated_data)
        return Response(
            VoluntarioRegistradoSerializer(voluntario).data,
            status=status.HTTP_201_CREATED,
            headers={'Location': f'/api/voluntarios/{voluntario.id}/'},
        )


class VoluntarioDetalleController(APIView):
    """GET y PATCH /api/voluntarios/{id}/ (administrador)"""
    permission_classes = [EnvioPublicoConsultaAdmin]
    servicio = VoluntarioService()

    def get(self, request, id):
        return Response(VoluntarioDetalleSerializer(self.servicio.obtener(id)).data)

    def patch(self, request, id):
        entrada = VoluntarioCambioEstadoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        voluntario = self.servicio.cambiar_estado(id, entrada.validated_data['estado'])
        return Response(VoluntarioDetalleSerializer(voluntario).data)


class SesionController(APIView):
    """POST /api/sesion/ (iniciar sesión)  ·  DELETE /api/sesion/ (cerrar sesión)"""
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'inicio_sesion'
    servicio = SesionService()

    def get_permissions(self):
        return [IsAuthenticated()] if self.request.method == 'DELETE' else [AllowAny()]

    def get_throttles(self):
        return super().get_throttles() if self.request.method == 'POST' else []

    def post(self, request):
        entrada = InicioSesionSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        cuenta, token = self.servicio.iniciar_sesion(**entrada.validated_data)
        return Response({
            'token': token,
            'usuario': cuenta.get_username(),
            'es_administrador': cuenta.is_staff,
        })

    def delete(self, request):
        self.servicio.cerrar_sesion(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([AllowAny])
def ruta_no_encontrada(request, ruta=''):
    """Cualquier /api/... que no exista responde 404 en JSON, no una página HTML."""
    raise RecursoNoEncontrado(f'No existe el endpoint {request.method} {request.path}.')
