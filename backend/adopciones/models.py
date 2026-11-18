"""
MODELO (capa de dominio).

Representa las entidades del negocio: Animal y SolicitudAdopcion.
No sabe nada de HTTP, de JSON ni de pantallas; solo describe los datos
y sus valores permitidos.
"""
from django.db import models
from django.db.models import Q


class Animal(models.Model):
    class Especie(models.TextChoices):
        PERRO = 'perro', 'Perro'
        GATO = 'gato', 'Gato'

    class Sexo(models.TextChoices):
        HEMBRA = 'hembra', 'Hembra'
        MACHO = 'macho', 'Macho'

    class Tamano(models.TextChoices):
        PEQUENO = 'pequeno', 'Pequeño'
        MEDIANO = 'mediano', 'Mediano'
        GRANDE = 'grande', 'Grande'

    class Estado(models.TextChoices):
        DISPONIBLE = 'DISPONIBLE', 'Disponible'
        EN_PROCESO = 'EN_PROCESO', 'En proceso de adopción'
        ADOPTADO = 'ADOPTADO', 'Adoptado'

    nombre = models.CharField(max_length=60)
    especie = models.CharField(max_length=10, choices=Especie.choices)
    raza = models.CharField(max_length=80)
    sexo = models.CharField(max_length=10, choices=Sexo.choices)
    edad_meses = models.PositiveIntegerField()
    tamano = models.CharField(max_length=10, choices=Tamano.choices)
    salud = models.CharField(max_length=200)
    descripcion = models.TextField()
    historia = models.CharField(max_length=200, blank=True)
    # Ruta de la foto relativa al frontend, por ejemplo "img/luna.jpg".
    foto = models.CharField(max_length=200, blank=True)
    foto_alt = models.CharField(max_length=250, blank=True)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.DISPONIBLE)
    fecha_ingreso = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['id']
        verbose_name_plural = 'animales'
        constraints = [
            models.CheckConstraint(condition=Q(edad_meses__lte=360), name='animal_edad_maxima'),
        ]

    def __str__(self):
        return f'{self.nombre} ({self.get_especie_display()})'


class SolicitudAdopcion(models.Model):
    class Estado(models.TextChoices):
        RECIBIDA = 'RECIBIDA', 'Recibida'
        EN_REVISION = 'EN_REVISION', 'En revisión'
        APROBADA = 'APROBADA', 'Aprobada'
        RECHAZADA = 'RECHAZADA', 'Rechazada'

    ESTADOS_ACTIVOS = (Estado.RECIBIDA, Estado.EN_REVISION)

    class TipoDocumento(models.TextChoices):
        CC = 'CC', 'Cédula de ciudadanía'
        CE = 'CE', 'Cédula de extranjería'
        PPT = 'PPT', 'Permiso por protección temporal'
        PA = 'PA', 'Pasaporte'

    class TipoVivienda(models.TextChoices):
        CASA = 'casa', 'Casa'
        APARTAMENTO = 'apartamento', 'Apartamento'
        FINCA = 'finca', 'Finca'

    class Tenencia(models.TextChoices):
        PROPIA = 'propia', 'Propia'
        ARRENDADA = 'arrendada', 'Arrendada'

    # null = "Aún no lo decido, quiero orientación".
    animal = models.ForeignKey(
        Animal, on_delete=models.PROTECT, null=True, blank=True, related_name='solicitudes'
    )
    nombre = models.CharField(max_length=100)
    tipo_documento = models.CharField(max_length=3, choices=TipoDocumento.choices)
    documento = models.CharField(max_length=15)
    fecha_nacimiento = models.DateField()
    correo = models.EmailField()
    telefono = models.CharField(max_length=10)
    direccion = models.CharField(max_length=150)
    ciudad = models.CharField(max_length=60)
    tipo_vivienda = models.CharField(max_length=12, choices=TipoVivienda.choices)
    tenencia = models.CharField(max_length=10, choices=Tenencia.choices)
    personas_hogar = models.PositiveSmallIntegerField()
    otras_mascotas = models.JSONField(default=list, blank=True)
    horas_solo = models.PositiveSmallIntegerField(default=0)
    fecha_visita = models.DateField(null=True, blank=True)
    hora_visita = models.TimeField(null=True, blank=True)
    motivo = models.TextField()
    medio = models.CharField(max_length=20, blank=True)
    acepta_datos = models.BooleanField()
    acepta_visita = models.BooleanField()
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.RECIBIDA)
    # Nota del administrador; obligatoria al rechazar.
    observacion = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'solicitud de adopción'
        verbose_name_plural = 'solicitudes de adopción'
        # Las mismas reglas del servicio, repetidas en la base de datos: aunque
        # alguien escriba sin pasar por la API, los datos no quedan inconsistentes.
        constraints = [
            models.CheckConstraint(
                condition=Q(personas_hogar__gte=1, personas_hogar__lte=20), name='solicitud_personas_hogar_rango'
            ),
            models.CheckConstraint(condition=Q(horas_solo__lte=12), name='solicitud_horas_solo_maximo'),
            models.CheckConstraint(
                condition=Q(acepta_datos=True, acepta_visita=True), name='solicitud_con_autorizaciones'
            ),
            models.UniqueConstraint(
                fields=['documento', 'animal'],
                condition=Q(estado__in=['RECIBIDA', 'EN_REVISION']),
                name='solicitud_activa_unica',
            ),
        ]

    def __str__(self):
        animal = self.animal.nombre if self.animal else 'sin preferencia'
        return f'Solicitud #{self.pk} de {self.nombre} ({animal})'


class Voluntario(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente de inducción'
        ACTIVO = 'ACTIVO', 'Activo'
        INACTIVO = 'INACTIVO', 'Inactivo'

    class Area(models.TextChoices):
        CUIDADO = 'cuidado', 'Cuidado y paseo de animales'
        EVENTOS = 'eventos', 'Eventos y ferias de adopción'
        TRANSPORTE = 'transporte', 'Transporte de animales'
        COMUNICACIONES = 'comunicaciones', 'Fotografía y redes sociales'
        HOGAR_PASO = 'hogar-paso', 'Hogar de paso temporal'

    DIAS = ['entre-semana', 'sabado', 'domingo']

    nombre = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    telefono = models.CharField(max_length=10)
    edad = models.PositiveSmallIntegerField()
    red_social = models.URLField(blank=True)
    disponibilidad = models.JSONField(default=list)
    area = models.CharField(max_length=15, choices=Area.choices)
    experiencia = models.BooleanField()
    comentarios = models.TextField(blank=True)
    acepta_datos = models.BooleanField()
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_registro']
        verbose_name_plural = 'voluntarios'
        constraints = [
            models.CheckConstraint(condition=Q(edad__gte=16, edad__lte=90), name='voluntario_edad_rango'),
            models.CheckConstraint(condition=Q(acepta_datos=True), name='voluntario_con_autorizacion'),
        ]

    def __str__(self):
        return f'{self.nombre} ({self.get_area_display()})'
