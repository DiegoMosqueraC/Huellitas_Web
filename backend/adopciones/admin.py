"""
Panel de administración de Django.

El estado de solicitudes y voluntarios es de solo lectura aquí: se cambia con
las acciones de la lista, que llaman al MISMO servicio que usa la API
(PATCH /api/solicitudes/{id}/ y PATCH /api/voluntarios/{id}/). Así las reglas
del negocio viven en un solo lugar, aunque haya dos "controladores".
"""
from django.contrib import admin, messages

from .errores import ErrorDeNegocio
from .models import Animal, SolicitudAdopcion, Voluntario
from .servicios import SolicitudService, VoluntarioService


def aplicar_a_cada_uno(modeladmin, request, queryset, cambiar):
    correctos = 0
    for objeto in queryset:
        try:
            cambiar(objeto)
            correctos += 1
        except ErrorDeNegocio as error:
            modeladmin.message_user(request, f'#{objeto.pk}: {error.mensaje}', messages.ERROR)
    if correctos:
        modeladmin.message_user(request, f'{correctos} registro(s) actualizados.', messages.SUCCESS)


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'especie', 'raza', 'edad_meses', 'tamano', 'estado']
    list_filter = ['especie', 'estado']


@admin.register(SolicitudAdopcion)
class SolicitudAdopcionAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'documento', 'animal', 'estado', 'fecha_creacion', 'fecha_actualizacion']
    list_filter = ['estado']
    readonly_fields = ['estado', 'observacion', 'fecha_creacion', 'fecha_actualizacion']
    actions = ['pasar_a_revision', 'aprobar']

    @admin.action(description='Pasar a EN REVISIÓN')
    def pasar_a_revision(self, request, queryset):
        servicio = SolicitudService()
        aplicar_a_cada_uno(self, request, queryset,
                           lambda s: servicio.cambiar_estado(s.pk, SolicitudAdopcion.Estado.EN_REVISION))

    @admin.action(description='APROBAR (el animal pasa a "en proceso")')
    def aprobar(self, request, queryset):
        servicio = SolicitudService()
        aplicar_a_cada_uno(self, request, queryset,
                           lambda s: servicio.cambiar_estado(s.pk, SolicitudAdopcion.Estado.APROBADA))


@admin.register(Voluntario)
class VoluntarioAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'correo', 'edad', 'area', 'estado', 'fecha_registro']
    list_filter = ['area', 'estado']
    readonly_fields = ['estado', 'fecha_registro', 'fecha_actualizacion']
    actions = ['activar', 'inactivar']

    @admin.action(description='ACTIVAR (inducción realizada)')
    def activar(self, request, queryset):
        servicio = VoluntarioService()
        aplicar_a_cada_uno(self, request, queryset,
                           lambda v: servicio.cambiar_estado(v.pk, Voluntario.Estado.ACTIVO))

    @admin.action(description='INACTIVAR')
    def inactivar(self, request, queryset):
        servicio = VoluntarioService()
        aplicar_a_cada_uno(self, request, queryset,
                           lambda v: servicio.cambiar_estado(v.pk, Voluntario.Estado.INACTIVO))
