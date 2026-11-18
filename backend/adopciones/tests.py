"""
Matriz de pruebas de la API (ver docs/05-pruebas.md).

"Funciona" no es suficiente: además del camino feliz se prueba que la API
falla correctamente (400, 401, 403, 404, 409, 429, 500 y 503 controlados).
Ejecutar:  python manage.py test adopciones -v 2
"""
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import IntegrityError, OperationalError, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Animal, SolicitudAdopcion, Voluntario
from .repositorios import SolicitudRepository

LUNA_ID = 1
ZEUS_ID = 4  # estado EN_PROCESO en los datos iniciales


def solicitud_valida(**cambios):
    datos = {
        'animal_id': LUNA_ID,
        'nombre': 'María Fernanda Pérez',
        'tipo_documento': 'CC',
        'documento': '1090123456',
        'fecha_nacimiento': '1995-05-10',
        'correo': 'maria@correo.com',
        'telefono': '3001234567',
        'direccion': 'Calle 10 # 5-20, barrio Centro',
        'ciudad': 'Cúcuta',
        'tipo_vivienda': 'casa',
        'tenencia': 'propia',
        'personas_hogar': 3,
        'otras_mascotas': ['ninguna'],
        'horas_solo': 4,
        'fecha_visita': (timezone.localdate() + timedelta(days=7)).isoformat(),
        'hora_visita': '10:00',
        'motivo': 'Tenemos un patio grande y tiempo para pasearla todos los días.',
        'medio': 'redes',
        'acepta_datos': True,
        'acepta_visita': True,
    }
    datos.update(cambios)
    return datos


class PruebaBase(APITestCase):

    def setUp(self):
        admin = User.objects.create_user('admin_prueba', password='clave-de-prueba', is_staff=True)
        voluntario = User.objects.create_user('voluntario_prueba', password='clave-de-prueba')
        self.token_admin = Token.objects.create(user=admin).key
        self.token_voluntario = Token.objects.create(user=voluntario).key

    def como(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def assertError(self, respuesta, estado, codigo):
        self.assertEqual(respuesta.status_code, estado, respuesta.content)
        self.assertEqual(respuesta['Content-Type'], 'application/json')
        self.assertEqual(respuesta.data['error']['estado'], estado)
        self.assertEqual(respuesta.data['error']['codigo'], codigo)
        self.assertTrue(respuesta.data['error']['mensaje'])


class AnimalesApiTests(PruebaBase):

    def test_T01_listar_animales(self):
        """T01 GET /api/animales/ -> 200 con los 6 animales iniciales."""
        r = self.client.get('/api/animales/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 6)
        self.assertEqual(r.data[0]['nombre'], 'Luna')

    def test_T02_filtrar_por_especie(self):
        """T02 GET /api/animales/?especie=gato -> 200 solo gatos."""
        r = self.client.get('/api/animales/', {'especie': 'gato'})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual({a['nombre'] for a in r.data}, {'Tomás', 'Miel'})

    def test_T03_filtro_invalido(self):
        """T03 GET /api/animales/?especie=loro -> 400 DATOS_INVALIDOS."""
        r = self.client.get('/api/animales/', {'especie': 'loro'})
        self.assertError(r, 400, 'DATOS_INVALIDOS')
        self.assertIn('especie', r.data['error']['detalles'])

    def test_T04_consultar_un_animal(self):
        """T04 GET /api/animales/1/ -> 200 con Luna."""
        r = self.client.get(f'/api/animales/{LUNA_ID}/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['nombre'], 'Luna')
        self.assertEqual(r.data['edad_texto'], '2 años')

    def test_T05_animal_inexistente(self):
        """T05 GET /api/animales/999/ -> 404 RECURSO_NO_ENCONTRADO."""
        r = self.client.get('/api/animales/999/')
        self.assertError(r, 404, 'RECURSO_NO_ENCONTRADO')

    def test_T06_crear_sin_token(self):
        """T06 POST /api/animales/ sin token -> 401 NO_AUTENTICADO."""
        r = self.client.post('/api/animales/', {'nombre': 'Toby'}, format='json')
        self.assertError(r, 401, 'NO_AUTENTICADO')
        self.assertIn('Bearer', r['WWW-Authenticate'])

    def test_T07_crear_sin_permiso(self):
        """T07 POST /api/animales/ con token de usuario no administrador -> 403 SIN_PERMISO."""
        self.como(self.token_voluntario)
        r = self.client.post('/api/animales/', {'nombre': 'Toby'}, format='json')
        self.assertError(r, 403, 'SIN_PERMISO')

    def test_T08_crear_animal(self):
        """T08 POST /api/animales/ como administrador -> 201 y encabezado Location."""
        self.como(self.token_admin)
        r = self.client.post('/api/animales/', {
            'nombre': 'Toby', 'especie': 'perro', 'raza': 'Criollo', 'sexo': 'macho',
            'edad_meses': 18, 'tamano': 'mediano', 'salud': 'Vacunado',
            'descripcion': 'Alegre y sociable.',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.content)
        self.assertEqual(r.data['estado'], 'DISPONIBLE')
        self.assertEqual(r['Location'], f'/api/animales/{r.data["id"]}/')

    def test_T09_crear_con_datos_invalidos(self):
        """T09 POST /api/animales/ con edad negativa y especie desconocida -> 400 con detalles por campo."""
        self.como(self.token_admin)
        r = self.client.post('/api/animales/', {
            'nombre': 'Toby', 'especie': 'loro', 'raza': 'Criollo', 'sexo': 'macho',
            'edad_meses': -5, 'tamano': 'mediano', 'salud': 'Vacunado', 'descripcion': 'Alegre.',
        }, format='json')
        self.assertError(r, 400, 'DATOS_INVALIDOS')
        self.assertIn('edad_meses', r.data['error']['detalles'])
        self.assertIn('especie', r.data['error']['detalles'])

    def test_T10_actualizar_animal(self):
        """T10 PATCH /api/animales/4/ como administrador -> 200 con el estado actualizado."""
        self.como(self.token_admin)
        r = self.client.patch(f'/api/animales/{ZEUS_ID}/', {'estado': 'ADOPTADO'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['estado'], 'ADOPTADO')

    def test_T11_eliminar_animal(self):
        """T11 DELETE /api/animales/6/ -> 204 y luego GET -> 404."""
        self.como(self.token_admin)
        r = self.client.delete('/api/animales/6/')
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertError(self.client.get('/api/animales/6/'), 404, 'RECURSO_NO_ENCONTRADO')

    def test_T12_eliminar_animal_con_solicitudes(self):
        """T12 DELETE de un animal que tiene solicitudes -> 409 CONFLICTO."""
        self.client.post('/api/solicitudes/', solicitud_valida(), format='json')
        self.como(self.token_admin)
        r = self.client.delete(f'/api/animales/{LUNA_ID}/')
        self.assertError(r, 409, 'CONFLICTO')
        self.assertTrue(Animal.objects.filter(pk=LUNA_ID).exists())


class SolicitudesApiTests(PruebaBase):

    def test_T13_registrar_solicitud(self):
        """T13 POST /api/solicitudes/ válida -> 201 con id, estado RECIBIDA y animal."""
        r = self.client.post('/api/solicitudes/', solicitud_valida(), format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.content)
        self.assertEqual(r.data['estado'], 'RECIBIDA')
        self.assertEqual(r.data['animal'], {'id': LUNA_ID, 'nombre': 'Luna'})
        self.assertEqual(r['Location'], f'/api/solicitudes/{r.data["id"]}/')
        self.assertEqual(SolicitudAdopcion.objects.count(), 1)

    def test_T14_formato_invalido(self):
        """T14 POST con celular, correo y motivo inválidos -> 400 con un detalle por campo, sin llegar a la BD."""
        r = self.client.post('/api/solicitudes/', solicitud_valida(
            telefono='12345', correo='no-es-correo', motivo='corto'
        ), format='json')
        self.assertError(r, 400, 'DATOS_INVALIDOS')
        self.assertEqual(set(r.data['error']['detalles']), {'telefono', 'correo', 'motivo'})
        self.assertEqual(SolicitudAdopcion.objects.count(), 0)

    def test_T15_menor_de_edad(self):
        """T15 POST de un menor de 18 años -> 400 (regla de negocio del servicio)."""
        hace_15_anios = timezone.localdate().replace(year=timezone.localdate().year - 15)
        r = self.client.post('/api/solicitudes/', solicitud_valida(
            fecha_nacimiento=hace_15_anios.isoformat()
        ), format='json')
        self.assertError(r, 400, 'DATOS_INVALIDOS')
        self.assertIn('fecha_nacimiento', r.data['error']['detalles'])

    def test_T16_sin_autorizaciones(self):
        """T16 POST sin aceptar el tratamiento de datos ni la visita -> 400."""
        r = self.client.post('/api/solicitudes/', solicitud_valida(
            acepta_datos=False, acepta_visita=False
        ), format='json')
        self.assertError(r, 400, 'DATOS_INVALIDOS')
        self.assertEqual(set(r.data['error']['detalles']), {'acepta_datos', 'acepta_visita'})

    def test_T17_animal_inexistente(self):
        """T17 POST para un animal que no existe -> 404."""
        r = self.client.post('/api/solicitudes/', solicitud_valida(animal_id=999), format='json')
        self.assertError(r, 404, 'RECURSO_NO_ENCONTRADO')

    def test_T18_animal_no_disponible(self):
        """T18 POST para Zeus (en proceso de adopción) -> 409 CONFLICTO."""
        r = self.client.post('/api/solicitudes/', solicitud_valida(animal_id=ZEUS_ID), format='json')
        self.assertError(r, 409, 'CONFLICTO')
        self.assertIn('Zeus', r.data['error']['mensaje'])

    def test_T19_solicitud_duplicada(self):
        """T19 Segunda solicitud activa del mismo documento para el mismo animal -> 409."""
        self.client.post('/api/solicitudes/', solicitud_valida(), format='json')
        r = self.client.post('/api/solicitudes/', solicitud_valida(), format='json')
        self.assertError(r, 409, 'CONFLICTO')
        self.assertEqual(SolicitudAdopcion.objects.count(), 1)

    def test_T20_cliente_no_decide_el_estado(self):
        """T20 Integridad: si el cliente envía "estado": "APROBADA", el servidor lo ignora -> RECIBIDA."""
        r = self.client.post('/api/solicitudes/', solicitud_valida(estado='APROBADA'), format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['estado'], 'RECIBIDA')

    def test_T21_json_mal_formado(self):
        """T21 POST con un cuerpo que no es JSON válido -> 400 JSON_INVALIDO."""
        r = self.client.generic('POST', '/api/solicitudes/', '{"nombre": ', content_type='application/json')
        self.assertError(r, 400, 'JSON_INVALIDO')

    def test_T22_consultar_solicitudes_requiere_admin(self):
        """T22 GET /api/solicitudes/: sin token 401, voluntario 403, administrador 200."""
        self.client.post('/api/solicitudes/', solicitud_valida(), format='json')
        self.assertError(self.client.get('/api/solicitudes/'), 401, 'NO_AUTENTICADO')
        self.como(self.token_voluntario)
        self.assertError(self.client.get('/api/solicitudes/'), 403, 'SIN_PERMISO')
        self.como(self.token_admin)
        r = self.client.get('/api/solicitudes/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 1)

    def test_T23_error_inesperado_controlado(self):
        """T23 Falla de la base de datos -> 500 ERROR_INTERNO sin exponer detalles internos."""
        with patch('adopciones.repositorios.AnimalRepository.obtener_todos',
                   side_effect=RuntimeError('conexión perdida con la base de datos')):
            with self.assertLogs('adopciones', level='ERROR'):
                r = self.client.get('/api/animales/')
        self.assertError(r, 500, 'ERROR_INTERNO')
        self.assertNotIn('conexión perdida', r.data['error']['mensaje'])

    def test_T24_endpoint_inexistente(self):
        """T24 GET /api/mascotas/ (no existe) -> 404 en JSON, no una página HTML."""
        r = self.client.get('/api/mascotas/')
        self.assertError(r, 404, 'RECURSO_NO_ENCONTRADO')


def voluntario_valido(**cambios):
    datos = {
        'nombre': 'Andrés Felipe Gómez',
        'correo': 'andres@correo.com',
        'telefono': '3157654321',
        'edad': 22,
        'red_social': '',
        'disponibilidad': ['sabado', 'domingo'],
        'area': 'cuidado',
        'experiencia': True,
        'comentarios': 'Tuve perros toda mi vida y quiero ayudar los fines de semana.',
        'acepta_datos': True,
    }
    datos.update(cambios)
    return datos


class VoluntariosApiTests(PruebaBase):

    def test_T25_registrar_voluntario(self):
        """T25 POST /api/voluntarios/ válido -> 201 con estado PENDIENTE y Location."""
        r = self.client.post('/api/voluntarios/', voluntario_valido(), format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.content)
        self.assertEqual(r.data['estado'], 'PENDIENTE')
        self.assertEqual(r['Location'], f'/api/voluntarios/{r.data["id"]}/')
        self.assertEqual(Voluntario.objects.get().disponibilidad, ['sabado', 'domingo'])

    def test_T26_formato_invalido(self):
        """T26 POST sin días disponibles, con celular y edad inválidos -> 400 con detalles; nada se guarda."""
        r = self.client.post('/api/voluntarios/', voluntario_valido(
            disponibilidad=[], telefono='555', edad=12
        ), format='json')
        self.assertError(r, 400, 'DATOS_INVALIDOS')
        self.assertEqual(set(r.data['error']['detalles']), {'disponibilidad', 'telefono', 'edad'})
        self.assertEqual(Voluntario.objects.count(), 0)

    def test_T27_menor_en_area_de_adultos(self):
        """T27 Voluntario de 16 años en hogar de paso -> 400 (regla de negocio); en eventos -> 201."""
        r = self.client.post('/api/voluntarios/', voluntario_valido(edad=16, area='hogar-paso'), format='json')
        self.assertError(r, 400, 'DATOS_INVALIDOS')
        self.assertIn('area', r.data['error']['detalles'])
        r = self.client.post('/api/voluntarios/', voluntario_valido(edad=16, area='eventos'), format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_T28_sin_autorizacion_de_datos(self):
        """T28 POST sin autorizar el tratamiento de datos -> 400."""
        r = self.client.post('/api/voluntarios/', voluntario_valido(acepta_datos=False), format='json')
        self.assertError(r, 400, 'DATOS_INVALIDOS')
        self.assertIn('acepta_datos', r.data['error']['detalles'])

    def test_T29_correo_duplicado(self):
        """T29 Segundo registro con el mismo correo (con mayúsculas) -> 409."""
        self.client.post('/api/voluntarios/', voluntario_valido(), format='json')
        r = self.client.post('/api/voluntarios/', voluntario_valido(correo='ANDRES@correo.com'), format='json')
        self.assertError(r, 409, 'CONFLICTO')
        self.assertEqual(Voluntario.objects.count(), 1)

    def test_T30_cliente_no_decide_el_estado(self):
        """T30 Integridad: "estado": "ACTIVO" enviado por el cliente se ignora -> PENDIENTE."""
        r = self.client.post('/api/voluntarios/', voluntario_valido(estado='ACTIVO'), format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['estado'], 'PENDIENTE')

    def test_T31_consultar_voluntarios_requiere_admin(self):
        """T31 GET /api/voluntarios/: sin token 401, voluntario 403, administrador 200."""
        self.client.post('/api/voluntarios/', voluntario_valido(), format='json')
        self.assertError(self.client.get('/api/voluntarios/'), 401, 'NO_AUTENTICADO')
        self.como(self.token_voluntario)
        self.assertError(self.client.get('/api/voluntarios/'), 403, 'SIN_PERMISO')
        self.como(self.token_admin)
        r = self.client.get('/api/voluntarios/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data[0]['correo'], 'andres@correo.com')

    def test_T32_voluntario_inexistente(self):
        """T32 GET /api/voluntarios/999/ como administrador -> 404."""
        self.como(self.token_admin)
        self.assertError(self.client.get('/api/voluntarios/999/'), 404, 'RECURSO_NO_ENCONTRADO')


class CambioDeEstadoApiTests(PruebaBase):
    """PATCH de solicitudes y voluntarios: el proceso de adopción y la inducción."""

    def crear_solicitud(self, **cambios):
        r = self.client.post('/api/solicitudes/', solicitud_valida(**cambios), format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.content)
        return r.data['id']

    def patch(self, ruta, datos):
        return self.client.patch(ruta, datos, format='json')

    def test_T33_proceso_completo_de_aprobacion(self):
        """T33 RECIBIDA -> EN_REVISION -> APROBADA (200) y el animal pasa a EN_PROCESO."""
        sid = self.crear_solicitud()
        self.como(self.token_admin)
        r = self.patch(f'/api/solicitudes/{sid}/', {'estado': 'EN_REVISION'})
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.content)
        self.assertEqual(r.data['estado'], 'EN_REVISION')
        r = self.patch(f'/api/solicitudes/{sid}/', {'estado': 'APROBADA'})
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.content)
        self.assertEqual(r.data['estado'], 'APROBADA')
        self.assertEqual(Animal.objects.get(pk=LUNA_ID).estado, 'EN_PROCESO')

    def test_T34_transicion_no_permitida(self):
        """T34 RECIBIDA -> APROBADA saltándose la revisión -> 409; el animal sigue DISPONIBLE."""
        sid = self.crear_solicitud()
        self.como(self.token_admin)
        r = self.patch(f'/api/solicitudes/{sid}/', {'estado': 'APROBADA'})
        self.assertError(r, 409, 'CONFLICTO')
        self.assertEqual(Animal.objects.get(pk=LUNA_ID).estado, 'DISPONIBLE')

    def test_T35_estado_final(self):
        """T35 Una solicitud RECHAZADA no puede volver a EN_REVISION -> 409."""
        sid = self.crear_solicitud()
        self.como(self.token_admin)
        self.patch(f'/api/solicitudes/{sid}/', {'estado': 'RECHAZADA', 'observacion': 'Vivienda sin cerramiento.'})
        r = self.patch(f'/api/solicitudes/{sid}/', {'estado': 'EN_REVISION'})
        self.assertError(r, 409, 'CONFLICTO')
        self.assertIn('estado final', r.data['error']['mensaje'])

    def test_T36_rechazo_exige_observacion(self):
        """T36 Rechazar sin observación -> 400; con observación -> 200 y queda guardada."""
        sid = self.crear_solicitud()
        self.como(self.token_admin)
        r = self.patch(f'/api/solicitudes/{sid}/', {'estado': 'RECHAZADA'})
        self.assertError(r, 400, 'DATOS_INVALIDOS')
        self.assertIn('observacion', r.data['error']['detalles'])
        r = self.patch(f'/api/solicitudes/{sid}/', {'estado': 'RECHAZADA', 'observacion': 'Vivienda sin cerramiento.'})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['observacion'], 'Vivienda sin cerramiento.')

    def test_T37_estado_desconocido(self):
        """T37 PATCH con "estado": "PERDIDA" -> 400 con detalle en estado."""
        sid = self.crear_solicitud()
        self.como(self.token_admin)
        r = self.patch(f'/api/solicitudes/{sid}/', {'estado': 'PERDIDA'})
        self.assertError(r, 400, 'DATOS_INVALIDOS')
        self.assertIn('estado', r.data['error']['detalles'])

    def test_T38_dos_solicitudes_para_el_mismo_animal(self):
        """T38 Aprobada una solicitud de Luna, aprobar otra para Luna -> 409 y la segunda queda EN_REVISION."""
        primera = self.crear_solicitud()
        segunda = self.crear_solicitud(documento='1090555444', correo='otra@correo.com')
        self.como(self.token_admin)
        for sid in (primera, segunda):
            self.patch(f'/api/solicitudes/{sid}/', {'estado': 'EN_REVISION'})
        self.assertEqual(self.patch(f'/api/solicitudes/{primera}/', {'estado': 'APROBADA'}).status_code, 200)
        r = self.patch(f'/api/solicitudes/{segunda}/', {'estado': 'APROBADA'})
        self.assertError(r, 409, 'CONFLICTO')
        self.assertEqual(SolicitudAdopcion.objects.get(pk=segunda).estado, 'EN_REVISION')

    def test_T39_aprobar_sin_animal_asignado(self):
        """T39 Aprobar una solicitud "sin preferencia" (sin animal) -> 409."""
        sid = self.crear_solicitud(animal_id=None)
        self.como(self.token_admin)
        self.patch(f'/api/solicitudes/{sid}/', {'estado': 'EN_REVISION'})
        r = self.patch(f'/api/solicitudes/{sid}/', {'estado': 'APROBADA'})
        self.assertError(r, 409, 'CONFLICTO')

    def test_T40_cambiar_estado_requiere_admin(self):
        """T40 PATCH de solicitud o voluntario sin token -> 401; como voluntario -> 403; inexistente -> 404."""
        sid = self.crear_solicitud()
        self.assertError(self.patch(f'/api/solicitudes/{sid}/', {'estado': 'EN_REVISION'}), 401, 'NO_AUTENTICADO')
        self.assertError(self.patch('/api/voluntarios/1/', {'estado': 'ACTIVO'}), 401, 'NO_AUTENTICADO')
        self.como(self.token_voluntario)
        self.assertError(self.patch(f'/api/solicitudes/{sid}/', {'estado': 'EN_REVISION'}), 403, 'SIN_PERMISO')
        self.como(self.token_admin)
        self.assertError(self.patch('/api/solicitudes/999/', {'estado': 'EN_REVISION'}), 404, 'RECURSO_NO_ENCONTRADO')
        self.assertError(self.patch('/api/voluntarios/999/', {'estado': 'ACTIVO'}), 404, 'RECURSO_NO_ENCONTRADO')
        self.assertEqual(SolicitudAdopcion.objects.get(pk=sid).estado, 'RECIBIDA')

    def test_T41_activar_voluntario(self):
        """T41 Voluntario PENDIENTE -> ACTIVO (200); ACTIVO -> PENDIENTE (409)."""
        vid = self.client.post('/api/voluntarios/', voluntario_valido(), format='json').data['id']
        self.como(self.token_admin)
        r = self.patch(f'/api/voluntarios/{vid}/', {'estado': 'ACTIVO'})
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.content)
        self.assertEqual(r.data['estado'], 'ACTIVO')
        self.assertError(self.patch(f'/api/voluntarios/{vid}/', {'estado': 'PENDIENTE'}), 409, 'CONFLICTO')

    def test_T42_admin_de_django_usa_el_mismo_servicio(self):
        """T42 La acción "Aprobar" del panel /admin/ respeta las mismas reglas que la API."""
        sid = self.crear_solicitud()
        User.objects.create_superuser('jefe', password='clave-de-prueba')
        self.client.login(username='jefe', password='clave-de-prueba')
        lista = '/admin/adopciones/solicitudadopcion/'
        self.client.post(lista, {'action': 'aprobar', '_selected_action': [sid]})
        self.assertEqual(SolicitudAdopcion.objects.get(pk=sid).estado, 'RECIBIDA')
        self.client.post(lista, {'action': 'pasar_a_revision', '_selected_action': [sid]})
        self.client.post(lista, {'action': 'aprobar', '_selected_action': [sid]})
        self.assertEqual(SolicitudAdopcion.objects.get(pk=sid).estado, 'APROBADA')
        self.assertEqual(Animal.objects.get(pk=LUNA_ID).estado, 'EN_PROCESO')


class SesionApiTests(PruebaBase):
    """POST y DELETE /api/sesion/: lo que usa la pantalla de administración."""

    def setUp(self):
        super().setUp()
        cache.clear()  # el límite de intentos se guarda en la caché

    def iniciar(self, usuario='admin_prueba', clave='clave-de-prueba'):
        return self.client.post('/api/sesion/', {'usuario': usuario, 'clave': clave}, format='json')

    def test_T43_iniciar_sesion(self):
        """T43 Credenciales correctas de administrador -> 200 con token que sirve para consultar solicitudes."""
        r = self.iniciar()
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.content)
        self.assertEqual(r.data['usuario'], 'admin_prueba')
        self.assertTrue(r.data['es_administrador'])
        self.como(r.data['token'])
        self.assertEqual(self.client.get('/api/solicitudes/').status_code, status.HTTP_200_OK)

    def test_T44_credenciales_incorrectas(self):
        """T44 Contraseña o usuario incorrectos -> 401 con el mismo mensaje en ambos casos; sin campos -> 400."""
        mala_clave = self.iniciar(clave='equivocada')
        no_existe = self.iniciar(usuario='nadie')
        self.assertError(mala_clave, 401, 'CREDENCIALES_INVALIDAS')
        self.assertError(no_existe, 401, 'CREDENCIALES_INVALIDAS')
        self.assertEqual(mala_clave.data['error']['mensaje'], no_existe.data['error']['mensaje'])
        r = self.client.post('/api/sesion/', {}, format='json')
        self.assertError(r, 400, 'DATOS_INVALIDOS')
        self.assertEqual(set(r.data['error']['detalles']), {'usuario', 'clave'})

    def test_T45_usuario_no_administrador(self):
        """T45 Un usuario que no es administrador inicia sesión (es_administrador false) pero recibe 403 en las solicitudes."""
        r = self.iniciar(usuario='voluntario_prueba')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertFalse(r.data['es_administrador'])
        self.como(r.data['token'])
        self.assertError(self.client.get('/api/solicitudes/'), 403, 'SIN_PERMISO')

    def test_T46_cerrar_sesion_invalida_el_token(self):
        """T46 DELETE /api/sesion/ -> 204; el mismo token después -> 401. Sin token -> 401."""
        self.assertError(self.client.delete('/api/sesion/'), 401, 'NO_AUTENTICADO')
        token = self.iniciar().data['token']
        self.como(token)
        self.assertEqual(self.client.delete('/api/sesion/').status_code, status.HTTP_204_NO_CONTENT)
        self.assertError(self.client.get('/api/solicitudes/'), 401, 'NO_AUTENTICADO')

    def test_T47_limite_de_intentos(self):
        """T47 Más de 10 intentos por minuto desde la misma IP -> 429 DEMASIADOS_INTENTOS, aunque la clave sea correcta."""
        for _ in range(10):
            self.iniciar(clave='equivocada')
        r = self.iniciar()
        self.assertError(r, 429, 'DEMASIADOS_INTENTOS')

    def test_T48_estados_siguientes(self):
        """T48 El detalle trae los estados a los que se puede pasar, tomados de la regla del servicio."""
        r = self.client.post('/api/solicitudes/', solicitud_valida(), format='json')
        self.como(self.token_admin)
        detalle = self.client.get(f'/api/solicitudes/{r.data["id"]}/').data
        self.assertEqual(detalle['estados_siguientes'], ['EN_REVISION', 'RECHAZADA'])
        self.assertEqual(detalle['estado_texto'], 'Recibida')
        vid = self.client.post('/api/voluntarios/', voluntario_valido(), format='json').data['id']
        self.assertEqual(self.client.get(f'/api/voluntarios/{vid}/').data['estados_siguientes'], ['ACTIVO', 'INACTIVO'])


class PersistenciaEIntegridadTests(PruebaBase):
    """Unidad 3, clase 2: la fuente de datos real, sus restricciones, transacciones y fallos."""

    def test_T49_base_de_datos_no_disponible(self):
        """T49 Si la base de datos no responde -> 503 SERVICIO_NO_DISPONIBLE con Retry-After, sin detalles internos."""
        with patch('adopciones.repositorios.AnimalRepository.obtener_todos',
                   side_effect=OperationalError('unable to open database file')):
            with self.assertLogs('adopciones', level='ERROR'):
                r = self.client.get('/api/animales/')
        self.assertError(r, 503, 'SERVICIO_NO_DISPONIBLE')
        self.assertEqual(r['Retry-After'], '30')
        self.assertNotIn('database file', r.data['error']['mensaje'])

    def test_T50_la_aprobacion_es_atomica(self):
        """T50 Si falla guardar la solicitud al aprobar, el animal NO queda EN_PROCESO (rollback de la transacción)."""
        sid = self.client.post('/api/solicitudes/', solicitud_valida(), format='json').data['id']
        self.como(self.token_admin)
        self.client.patch(f'/api/solicitudes/{sid}/', {'estado': 'EN_REVISION'}, format='json')
        actualizar_real = SolicitudRepository.actualizar

        def falla_al_aprobar(repositorio, solicitud, datos):
            if datos['estado'] == 'APROBADA':
                raise RuntimeError('fallo simulado después de actualizar el animal')
            return actualizar_real(repositorio, solicitud, datos)

        with patch('adopciones.repositorios.SolicitudRepository.actualizar', falla_al_aprobar):
            with self.assertLogs('adopciones', level='ERROR'):
                r = self.client.patch(f'/api/solicitudes/{sid}/', {'estado': 'APROBADA'}, format='json')
        self.assertError(r, 500, 'ERROR_INTERNO')
        self.assertEqual(Animal.objects.get(pk=LUNA_ID).estado, 'DISPONIBLE')
        self.assertEqual(SolicitudAdopcion.objects.get(pk=sid).estado, 'EN_REVISION')

    def test_T51_la_base_de_datos_rechaza_datos_invalidos(self):
        """T51 Aunque se escriba sin pasar por la API, las restricciones CHECK y UNIQUE de la BD rechazan el registro."""
        self.client.post('/api/solicitudes/', solicitud_valida(), format='json')
        original = SolicitudAdopcion.objects.get()

        def copia(**cambios):
            datos = {c.name: getattr(original, c.name) for c in SolicitudAdopcion._meta.concrete_fields if c.name != 'id'}
            datos.update(cambios)
            return datos

        casos = {
            'UNIQUE solicitud activa duplicada': lambda: SolicitudAdopcion.objects.create(**copia()),
            'CHECK personas_hogar': lambda: SolicitudAdopcion.objects.create(**copia(documento='A1', personas_hogar=0)),
            'CHECK horas_solo': lambda: SolicitudAdopcion.objects.create(**copia(documento='A2', horas_solo=20)),
            'CHECK autorizaciones': lambda: SolicitudAdopcion.objects.create(**copia(documento='A3', acepta_datos=False)),
            'CHECK edad del voluntario': lambda: Voluntario.objects.create(
                nombre='Niño', correo='n@correo.com', telefono='3000000000', edad=10, disponibilidad=['sabado'],
                area='cuidado', experiencia=False, acepta_datos=True),
            'CHECK edad del animal': lambda: Animal.objects.filter(pk=LUNA_ID).update(edad_meses=9999),
        }
        for nombre, operacion in casos.items():
            with self.subTest(nombre), self.assertRaises(IntegrityError), transaction.atomic():
                operacion()
        self.assertEqual(SolicitudAdopcion.objects.count(), 1)

    def test_T52_conflicto_detectado_por_la_base_de_datos(self):
        """T52 Dos registros simultáneos con el mismo correo: el servicio no lo ve, la BD sí -> 409 controlado, no 500."""
        self.client.post('/api/voluntarios/', voluntario_valido(), format='json')
        with patch('adopciones.repositorios.VoluntarioRepository.existe_correo', return_value=False):
            with self.assertLogs('adopciones', level='WARNING'):
                r = self.client.post('/api/voluntarios/', voluntario_valido(), format='json')
        self.assertError(r, 409, 'CONFLICTO')

    def test_T53_lo_que_se_guarda_es_lo_que_se_consulta(self):
        """T53 Consistencia entre operaciones: POST -> GET lista -> GET detalle -> PATCH -> GET devuelven el mismo registro."""
        creada = self.client.post('/api/solicitudes/', solicitud_valida(), format='json').data
        self.como(self.token_admin)
        lista = self.client.get('/api/solicitudes/').data
        detalle = self.client.get(f'/api/solicitudes/{creada["id"]}/').data
        self.assertEqual([s['id'] for s in lista], [creada['id']])
        self.assertEqual(detalle['documento'], '1090123456')
        self.assertEqual(detalle['otras_mascotas'], ['ninguna'])
        self.client.patch(f'/api/solicitudes/{creada["id"]}/', {'estado': 'EN_REVISION'}, format='json')
        self.assertEqual(self.client.get(f'/api/solicitudes/{creada["id"]}/').data['estado'], 'EN_REVISION')
