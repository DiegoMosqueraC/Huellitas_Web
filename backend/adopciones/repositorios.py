"""
REPOSITORY / DAO (capa de acceso a datos).

Responde a la pregunta "¿cómo accedo a los datos?".
Solo consulta, guarda, actualiza y elimina. No decide permisos, no aplica
reglas del negocio y no conoce códigos HTTP.
Si mañana cambiamos SQLite por PostgreSQL u Oracle, solo cambia esta capa
(y la configuración), no los servicios ni los controladores.
"""
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

from .models import Animal, SolicitudAdopcion, Voluntario


class AnimalRepository:

    def obtener_todos(self, especie=None, estado=None):
        consulta = Animal.objects.all()
        if especie:
            consulta = consulta.filter(especie=especie)
        if estado:
            consulta = consulta.filter(estado=estado)
        return list(consulta)

    def obtener_por_id(self, animal_id):
        return Animal.objects.filter(pk=animal_id).first()

    def guardar(self, datos):
        return Animal.objects.create(**datos)

    def actualizar(self, animal, datos):
        for campo, valor in datos.items():
            setattr(animal, campo, valor)
        animal.save()
        return animal

    def eliminar(self, animal):
        animal.delete()

    def tiene_solicitudes(self, animal):
        return animal.solicitudes.exists()


class SolicitudRepository:

    def obtener_todas(self):
        return list(SolicitudAdopcion.objects.select_related('animal'))

    def obtener_por_id(self, solicitud_id):
        return SolicitudAdopcion.objects.select_related('animal').filter(pk=solicitud_id).first()

    def guardar(self, datos):
        return SolicitudAdopcion.objects.create(**datos)

    def actualizar(self, solicitud, datos):
        for campo, valor in datos.items():
            setattr(solicitud, campo, valor)
        solicitud.save()
        return solicitud

    def existe_activa(self, documento, animal):
        return SolicitudAdopcion.objects.filter(
            documento=documento,
            animal=animal,
            estado__in=SolicitudAdopcion.ESTADOS_ACTIVOS,
        ).exists()


class VoluntarioRepository:

    def obtener_todos(self):
        return list(Voluntario.objects.all())

    def obtener_por_id(self, voluntario_id):
        return Voluntario.objects.filter(pk=voluntario_id).first()

    def guardar(self, datos):
        return Voluntario.objects.create(**datos)

    def actualizar(self, voluntario, datos):
        for campo, valor in datos.items():
            setattr(voluntario, campo, valor)
        voluntario.save()
        return voluntario

    def existe_correo(self, correo):
        return Voluntario.objects.filter(correo__iexact=correo).exists()


class SesionRepository:
    """Usuarios y tokens (tablas de Django y de DRF)."""

    def verificar_credenciales(self, usuario, clave):
        # Devuelve None si no coinciden o si la cuenta está desactivada.
        return authenticate(username=usuario, password=clave)

    def obtener_o_crear_token(self, usuario):
        token, _ = Token.objects.get_or_create(user=usuario)
        return token.key

    def eliminar_token(self, usuario):
        Token.objects.filter(user=usuario).delete()
