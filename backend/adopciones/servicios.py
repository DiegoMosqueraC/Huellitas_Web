"""
SERVICE (capa de lógica de negocio).

Responde a la pregunta "¿qué debe ocurrir?" según las reglas de la fundación.
Usa los repositorios para leer y guardar, y lanza excepciones de negocio
(DatosInvalidos, RecursoNoEncontrado, Conflicto) cuando una regla no se cumple.
No conoce HTTP: el controlador decide la respuesta.
"""
from datetime import time

from django.db import transaction
from django.utils import timezone

from .errores import Conflicto, CredencialesInvalidas, DatosInvalidos, RecursoNoEncontrado
from .models import Animal, SolicitudAdopcion, Voluntario
from .repositorios import AnimalRepository, SesionRepository, SolicitudRepository, VoluntarioRepository


class AnimalService:

    def __init__(self, repositorio=None):
        self.repositorio = repositorio or AnimalRepository()

    def listar(self, especie=None, estado=None):
        errores = {}
        if especie and especie not in Animal.Especie.values:
            errores['especie'] = [f'Valores permitidos: {", ".join(Animal.Especie.values)}.']
        if estado and estado not in Animal.Estado.values:
            errores['estado'] = [f'Valores permitidos: {", ".join(Animal.Estado.values)}.']
        if errores:
            raise DatosInvalidos('Los filtros de la consulta no son válidos.', errores)
        return self.repositorio.obtener_todos(especie=especie, estado=estado)

    def obtener(self, animal_id):
        animal = self.repositorio.obtener_por_id(animal_id)
        if animal is None:
            raise RecursoNoEncontrado(f'No existe un animal con id {animal_id}.')
        return animal

    def crear(self, datos):
        return self.repositorio.guardar(datos)

    def actualizar(self, animal_id, datos):
        animal = self.obtener(animal_id)
        return self.repositorio.actualizar(animal, datos)

    def eliminar(self, animal_id):
        animal = self.obtener(animal_id)
        # Regla: no se borra el historial de un animal que ya tiene solicitudes.
        if self.repositorio.tiene_solicitudes(animal):
            raise Conflicto(
                f'{animal.nombre} tiene solicitudes de adopción registradas y no se puede eliminar. '
                'Cambia su estado a ADOPTADO en lugar de eliminarlo.'
            )
        self.repositorio.eliminar(animal)


class SolicitudService:
    EDAD_MINIMA = 18
    HORA_APERTURA = time(8, 0)
    HORA_CIERRE = time(16, 0)

    def __init__(self, solicitudes=None, animales=None):
        self.solicitudes = solicitudes or SolicitudRepository()
        self.animales = animales or AnimalRepository()

    def listar(self):
        return self.solicitudes.obtener_todas()

    def obtener(self, solicitud_id):
        solicitud = self.solicitudes.obtener_por_id(solicitud_id)
        if solicitud is None:
            raise RecursoNoEncontrado(f'No existe una solicitud con id {solicitud_id}.')
        return solicitud

    # Flujo del proceso de adopción. APROBADA y RECHAZADA son estados finales.
    TRANSICIONES = {
        SolicitudAdopcion.Estado.RECIBIDA: {SolicitudAdopcion.Estado.EN_REVISION, SolicitudAdopcion.Estado.RECHAZADA},
        SolicitudAdopcion.Estado.EN_REVISION: {SolicitudAdopcion.Estado.APROBADA, SolicitudAdopcion.Estado.RECHAZADA},
        SolicitudAdopcion.Estado.APROBADA: set(),
        SolicitudAdopcion.Estado.RECHAZADA: set(),
    }

    @transaction.atomic
    def cambiar_estado(self, solicitud_id, nuevo_estado, observacion=''):
        """
        Mueve una solicitud por el proceso de adopción (solo administradores).
        1. Solo se permiten los pasos de TRANSICIONES (409).
        2. Rechazar exige una observación para el solicitante (400).
        3. Aprobar exige un animal asignado y disponible (409), y lo pasa a EN_PROCESO.
        Todo ocurre en una transacción: o se actualizan la solicitud y el animal, o ninguno.
        """
        solicitud = self.obtener(solicitud_id)
        actual = SolicitudAdopcion.Estado(solicitud.estado)
        nuevo = SolicitudAdopcion.Estado(nuevo_estado)

        if nuevo not in self.TRANSICIONES[actual]:
            permitidos = ', '.join(sorted(self.TRANSICIONES[actual])) or 'ninguno (es un estado final)'
            raise Conflicto(
                f'La solicitud #{solicitud.id} está {actual.label.lower()} y no puede pasar a '
                f'{nuevo.label.lower()}. Estados permitidos desde aquí: {permitidos}.'
            )

        if nuevo == SolicitudAdopcion.Estado.RECHAZADA and not observacion.strip():
            raise DatosInvalidos(
                'Para rechazar una solicitud debes explicar el motivo.',
                {'observacion': ['Escribe el motivo del rechazo; se le comunicará al solicitante.']},
            )

        if nuevo == SolicitudAdopcion.Estado.APROBADA:
            if solicitud.animal is None:
                raise Conflicto('La solicitud no tiene un animal asignado. Orienta al solicitante antes de aprobarla.')
            # Se consulta de nuevo el animal: otra solicitud pudo aprobarse mientras tanto.
            animal = self.animales.obtener_por_id(solicitud.animal.id)
            if animal.estado != Animal.Estado.DISPONIBLE:
                raise Conflicto(
                    f'{animal.nombre} ya no está disponible (estado actual: '
                    f'{animal.get_estado_display().lower()}). No se puede aprobar esta solicitud.'
                )
            self.animales.actualizar(animal, {'estado': Animal.Estado.EN_PROCESO})

        return self.solicitudes.actualizar(solicitud, {'estado': nuevo, 'observacion': observacion.strip()})

    def registrar(self, datos):
        """
        Registra una solicitud de adopción.
        1. Verificar las reglas del solicitante (consentimientos, edad, visita).
        2. Verificar que el animal exista (404) y esté disponible (409).
        3. Evitar solicitudes duplicadas activas (409).
        4. Guardar con el estado que decide el servidor, nunca el que envía el cliente.
        """
        datos = dict(datos)
        self._validar_reglas_del_solicitante(datos)

        animal_id = datos.pop('animal_id', None)
        animal = None
        if animal_id is not None:
            animal = self.animales.obtener_por_id(animal_id)
            if animal is None:
                raise RecursoNoEncontrado(f'No existe un animal con id {animal_id}.')
            if animal.estado != Animal.Estado.DISPONIBLE:
                raise Conflicto(
                    f'{animal.nombre} no está disponible para adopción '
                    f'(estado actual: {animal.get_estado_display().lower()}).'
                )

        if self.solicitudes.existe_activa(datos['documento'], animal):
            raise Conflicto('Ya tienes una solicitud activa para este animal. Te contactaremos pronto.')

        datos['animal'] = animal
        datos['estado'] = SolicitudAdopcion.Estado.RECIBIDA
        return self.solicitudes.guardar(datos)

    def _validar_reglas_del_solicitante(self, datos):
        errores = {}
        hoy = timezone.localdate()

        if not datos.get('acepta_datos'):
            errores['acepta_datos'] = ['Debes autorizar el tratamiento de datos personales (Ley 1581 de 2012).']
        if not datos.get('acepta_visita'):
            errores['acepta_visita'] = ['Debes aceptar la visita previa y el seguimiento.']

        nacimiento = datos['fecha_nacimiento']
        edad = hoy.year - nacimiento.year - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))
        if edad < self.EDAD_MINIMA:
            errores['fecha_nacimiento'] = [f'Debes ser mayor de {self.EDAD_MINIMA} años para adoptar.']

        fecha_visita = datos.get('fecha_visita')
        if fecha_visita and fecha_visita < hoy:
            errores['fecha_visita'] = ['La fecha de visita no puede estar en el pasado.']

        hora_visita = datos.get('hora_visita')
        if hora_visita and not (self.HORA_APERTURA <= hora_visita <= self.HORA_CIERRE):
            errores['hora_visita'] = ['El refugio recibe visitas entre las 8:00 a. m. y las 4:00 p. m.']

        if errores:
            raise DatosInvalidos('La solicitud no cumple los requisitos de adopción.', errores)


class VoluntarioService:
    EDAD_ADULTO = 18
    # Áreas que implican llevar animales en un vehículo o tenerlos en casa.
    AREAS_SOLO_ADULTOS = {Voluntario.Area.TRANSPORTE, Voluntario.Area.HOGAR_PASO}

    def __init__(self, repositorio=None):
        self.repositorio = repositorio or VoluntarioRepository()

    def listar(self):
        return self.repositorio.obtener_todos()

    def obtener(self, voluntario_id):
        voluntario = self.repositorio.obtener_por_id(voluntario_id)
        if voluntario is None:
            raise RecursoNoEncontrado(f'No existe un voluntario con id {voluntario_id}.')
        return voluntario

    # PENDIENTE pasa a ACTIVO tras la inducción; ACTIVO e INACTIVO pueden alternarse.
    TRANSICIONES = {
        Voluntario.Estado.PENDIENTE: {Voluntario.Estado.ACTIVO, Voluntario.Estado.INACTIVO},
        Voluntario.Estado.ACTIVO: {Voluntario.Estado.INACTIVO},
        Voluntario.Estado.INACTIVO: {Voluntario.Estado.ACTIVO},
    }

    def cambiar_estado(self, voluntario_id, nuevo_estado):
        voluntario = self.obtener(voluntario_id)
        actual = Voluntario.Estado(voluntario.estado)
        nuevo = Voluntario.Estado(nuevo_estado)
        if nuevo not in self.TRANSICIONES[actual]:
            raise Conflicto(
                f'{voluntario.nombre} está {actual.label.lower()} y no puede pasar a {nuevo.label.lower()}.'
            )
        return self.repositorio.actualizar(voluntario, {'estado': nuevo})

    def registrar(self, datos):
        """
        Registra un voluntario.
        1. Verificar la autorización de datos y que el área sea apta para su edad (400).
        2. Evitar registros duplicados con el mismo correo (409).
        3. Guardar con estado PENDIENTE: la inducción la confirma la fundación.
        """
        datos = dict(datos)
        errores = {}
        if not datos.get('acepta_datos'):
            errores['acepta_datos'] = ['Debes autorizar el tratamiento de datos personales (Ley 1581 de 2012).']
        if datos['edad'] < self.EDAD_ADULTO and datos['area'] in self.AREAS_SOLO_ADULTOS:
            errores['area'] = ['Transporte y hogar de paso requieren ser mayor de 18 años. Elige otra área.']
        if errores:
            raise DatosInvalidos('El registro no cumple los requisitos del voluntariado.', errores)

        datos['correo'] = datos['correo'].lower()
        if self.repositorio.existe_correo(datos['correo']):
            raise Conflicto('Ya hay un voluntario registrado con este correo. Te contactaremos para la inducción.')

        datos['estado'] = Voluntario.Estado.PENDIENTE
        return self.repositorio.guardar(datos)


class SesionService:
    """Inicio y cierre de sesión del personal de la fundación."""

    def __init__(self, repositorio=None):
        self.repositorio = repositorio or SesionRepository()

    def iniciar_sesion(self, usuario, clave):
        cuenta = self.repositorio.verificar_credenciales(usuario, clave)
        if cuenta is None:
            # Mismo mensaje si falla el usuario o la contraseña: no se revela cuál existe.
            raise CredencialesInvalidas('Usuario o contraseña incorrectos.')
        return cuenta, self.repositorio.obtener_o_crear_token(cuenta)

    def cerrar_sesion(self, cuenta):
        # Borrar el token lo invalida de inmediato, aunque alguien lo haya copiado.
        self.repositorio.eliminar_token(cuenta)
