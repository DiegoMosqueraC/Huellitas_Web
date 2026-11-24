"""
Serializers: traducen entre JSON y objetos del modelo.

- Validan el FORMATO de la entrada (tipos, longitudes, patrones), que es
  la validación básica que hace el controlador antes de llamar al servicio.
- Definen la forma del JSON de salida (nombres claros y consistentes).
Las reglas del negocio NO van aquí: van en servicios.py.
"""
from rest_framework import serializers

from .models import Animal, Jornada, SolicitudAdopcion, Voluntario
from .servicios import SolicitudService, VoluntarioService


class AnimalSerializer(serializers.ModelSerializer):
    edad_texto = serializers.CharField(read_only=True)
    especie_texto = serializers.CharField(source='get_especie_display', read_only=True)
    sexo_texto = serializers.CharField(source='get_sexo_display', read_only=True)
    tamano_texto = serializers.CharField(source='get_tamano_display', read_only=True)
    estado_texto = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Animal
        fields = [
            'id', 'nombre', 'especie', 'especie_texto', 'raza', 'sexo', 'sexo_texto',
            'edad_meses', 'edad_texto', 'tamano', 'tamano_texto', 'salud', 'descripcion',
            'historia', 'foto', 'foto_alt', 'estado', 'estado_texto', 'fecha_ingreso',
        ]
        read_only_fields = ['id', 'fecha_ingreso']
        extra_kwargs = {
            'nombre': {'min_length': 2},
            'edad_meses': {'max_value': 360},
        }



class SolicitudEntradaSerializer(serializers.Serializer):
    """Lo que el cliente PUEDE enviar. Cualquier otro campo (por ejemplo "estado") se ignora."""
    animal_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    nombre = serializers.CharField(min_length=3, max_length=100)
    tipo_documento = serializers.ChoiceField(choices=SolicitudAdopcion.TipoDocumento.choices)
    documento = serializers.RegexField(
        r'^[0-9A-Za-z]{5,15}$', error_messages={'invalid': 'Entre 5 y 15 caracteres, solo letras y números.'}
    )
    fecha_nacimiento = serializers.DateField()
    correo = serializers.EmailField()
    telefono = serializers.RegexField(
        r'^3\d{9}$', error_messages={'invalid': 'Número celular de 10 dígitos que empieza por 3.'}
    )
    direccion = serializers.CharField(max_length=150)
    ciudad = serializers.CharField(max_length=60)
    tipo_vivienda = serializers.ChoiceField(choices=SolicitudAdopcion.TipoVivienda.choices)
    tenencia = serializers.ChoiceField(choices=SolicitudAdopcion.Tenencia.choices)
    personas_hogar = serializers.IntegerField(min_value=1, max_value=20)
    otras_mascotas = serializers.ListField(
        child=serializers.ChoiceField(choices=['perro', 'gato', 'otra', 'ninguna']),
        required=False, default=list,
    )
    horas_solo = serializers.IntegerField(min_value=0, max_value=12, required=False, default=0)
    fecha_visita = serializers.DateField(required=False, allow_null=True)
    hora_visita = serializers.TimeField(required=False, allow_null=True)
    motivo = serializers.CharField(min_length=20, max_length=1000)
    medio = serializers.ChoiceField(
        choices=['redes', 'amigo', 'jornada', 'otro'], required=False, allow_blank=True, default=''
    )
    acepta_datos = serializers.BooleanField()
    acepta_visita = serializers.BooleanField()


class AnimalResumenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Animal
        fields = ['id', 'nombre']


class SolicitudCreadaSerializer(serializers.ModelSerializer):
    """Respuesta del 201: lo que el cliente necesita para continuar."""
    animal = AnimalResumenSerializer(read_only=True)
    mensaje = serializers.SerializerMethodField()

    class Meta:
        model = SolicitudAdopcion
        fields = ['id', 'estado', 'animal', 'fecha_creacion', 'mensaje']

    def get_mensaje(self, solicitud):
        return f'Recibimos tu solicitud #{solicitud.id}. La revisaremos en un plazo de 3 a 5 días hábiles.'


class SolicitudDetalleSerializer(serializers.ModelSerializer):
    """Vista completa, solo para administradores (contiene datos personales)."""
    animal = AnimalResumenSerializer(read_only=True)
    estado_texto = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_vivienda_texto = serializers.CharField(source='get_tipo_vivienda_display', read_only=True)
    # Los estados a los que puede pasar, según la regla del servicio. La pantalla de
    # administración muestra solo esos botones; no repite la regla.
    estados_siguientes = serializers.SerializerMethodField()

    class Meta:
        model = SolicitudAdopcion
        fields = '__all__'

    def get_estados_siguientes(self, solicitud):
        return sorted(SolicitudService.TRANSICIONES[solicitud.estado])


class VoluntarioEntradaSerializer(serializers.Serializer):
    """Lo que el cliente PUEDE enviar. El estado lo decide el servidor."""
    nombre = serializers.CharField(min_length=3, max_length=100)
    correo = serializers.EmailField()
    telefono = serializers.RegexField(
        r'^3\d{9}$', error_messages={'invalid': 'Número celular de 10 dígitos que empieza por 3.'}
    )
    edad = serializers.IntegerField(min_value=16, max_value=90)
    red_social = serializers.URLField(required=False, allow_blank=True, default='')
    disponibilidad = serializers.ListField(
        child=serializers.ChoiceField(choices=Voluntario.DIAS),
        allow_empty=False,
        error_messages={'empty': 'Elige al menos un día disponible.'},
    )
    area = serializers.ChoiceField(choices=Voluntario.Area.choices)
    experiencia = serializers.BooleanField()
    comentarios = serializers.CharField(max_length=500, required=False, allow_blank=True, default='')
    acepta_datos = serializers.BooleanField()

    def validate_disponibilidad(self, dias):
        return list(dict.fromkeys(dias))


class VoluntarioRegistradoSerializer(serializers.ModelSerializer):
    """Respuesta del 201."""
    mensaje = serializers.SerializerMethodField()

    class Meta:
        model = Voluntario
        fields = ['id', 'nombre', 'area', 'estado', 'fecha_registro', 'mensaje']

    def get_mensaje(self, voluntario):
        return f'¡Gracias, {voluntario.nombre}! Te escribiremos a {voluntario.correo} para la jornada de inducción.'


class VoluntarioDetalleSerializer(serializers.ModelSerializer):
    """Vista completa, solo para administradores."""
    estado_texto = serializers.CharField(source='get_estado_display', read_only=True)
    area_texto = serializers.CharField(source='get_area_display', read_only=True)
    estados_siguientes = serializers.SerializerMethodField()

    class Meta:
        model = Voluntario
        fields = '__all__'

    def get_estados_siguientes(self, voluntario):
        return sorted(VoluntarioService.TRANSICIONES[voluntario.estado])


class SolicitudCambioEstadoSerializer(serializers.Serializer):
    """PATCH /api/solicitudes/{id}/: lo único que el administrador puede cambiar."""
    estado = serializers.ChoiceField(choices=SolicitudAdopcion.Estado.choices)
    observacion = serializers.CharField(max_length=500, required=False, allow_blank=True, default='')


class VoluntarioCambioEstadoSerializer(serializers.Serializer):
    """PATCH /api/voluntarios/{id}/"""
    estado = serializers.ChoiceField(choices=Voluntario.Estado.choices)


class InicioSesionSerializer(serializers.Serializer):
    usuario = serializers.CharField(max_length=150)
    clave = serializers.CharField(max_length=128, trim_whitespace=False)


class ConsultaSolicitudSerializer(serializers.Serializer):
    numero = serializers.IntegerField(min_value=1)
    documento = serializers.RegexField(
        r'^[0-9A-Za-z]{5,15}$', error_messages={'invalid': 'Entre 5 y 15 caracteres, solo letras y números.'}
    )


class SolicitudEstadoSerializer(serializers.ModelSerializer):
    """Lo que ve el solicitante: el estado de su proceso, sin sus datos personales."""
    animal = AnimalResumenSerializer(read_only=True)
    estado_texto = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = SolicitudAdopcion
        fields = ['id', 'estado', 'estado_texto', 'animal', 'observacion', 'fecha_creacion', 'fecha_actualizacion']


class JornadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Jornada
        fields = ['id', 'fecha', 'hora_inicio', 'hora_fin', 'actividad', 'lugar', 'cupos']
