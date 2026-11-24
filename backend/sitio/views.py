"""
Vistas de las páginas (capa de presentación; en Django, MVC se llama MTV).

Cada vista le pide los datos al MISMO servicio que usa la API REST y se los
entrega a una plantilla. Las reglas del negocio no se repiten aquí.
Los formularios de las páginas siguen enviando sus datos a la API (js/*.js).
"""
from django.shortcuts import render

from adopciones.errores import DatosInvalidos, RecursoNoEncontrado
from adopciones.models import Animal
from adopciones.servicios import AnimalService, JornadaService

animales_servicio = AnimalService()
jornadas_servicio = JornadaService()


def inicio(request):
    disponibles = animales_servicio.listar(estado=Animal.Estado.DISPONIBLE)
    return render(request, 'sitio/inicio.html', {
        'seccion': 'inicio',
        'retratos': disponibles[:3],
        'total_disponibles': len(disponibles),
        'proxima_jornada': next(iter(jornadas_servicio.proximas()), None),
    })


def animales(request):
    especie = request.GET.get('especie', '')
    tamano = request.GET.get('tamano', '')
    aviso = None
    try:
        lista = animales_servicio.listar(especie=especie or None, tamano=tamano or None)
    except DatosInvalidos:
        aviso = 'Ese filtro no existe; te mostramos todos los animales.'
        especie = tamano = ''
        lista = animales_servicio.listar()
    return render(request, 'sitio/animales.html', {
        'seccion': 'animales',
        'animales': lista,
        'disponibles': sum(a.estado == Animal.Estado.DISPONIBLE for a in lista),
        'especie': especie,
        'tamano': tamano,
        'especies': Animal.Especie.choices,
        'tamanos': Animal.Tamano.choices,
        'aviso': aviso,
    })


def ficha(request, id):
    try:
        animal = animales_servicio.obtener(id)
    except RecursoNoEncontrado:
        # La página 404 propia también en modo desarrollo (Http404 mostraría la página técnica de Django).
        return render(request, '404.html', {'seccion': 'animales'}, status=404)
    return render(request, 'sitio/animal.html', {'seccion': 'animales', 'animal': animal})


def adoptar(request):
    animales = animales_servicio.listar()
    return render(request, 'sitio/adoptar.html', {
        'seccion': 'adoptar',
        'grupos': [
            ('Perros', [a for a in animales if a.especie == Animal.Especie.PERRO]),
            ('Gatos', [a for a in animales if a.especie == Animal.Especie.GATO]),
        ],
        # Viene de "Quiero adoptar a ...": /adoptar/?animal=3
        'elegido': request.GET.get('animal', ''),
    })


def voluntarios(request):
    return render(request, 'sitio/voluntarios.html', {
        'seccion': 'voluntarios',
        'jornadas': jornadas_servicio.proximas(),
    })


def consulta(request):
    return render(request, 'sitio/consulta.html', {'seccion': 'consulta'})


def contacto(request):
    return render(request, 'sitio/contacto.html', {'seccion': 'contacto'})


def panel(request):
    return render(request, 'sitio/panel.html', {'seccion': 'panel'})
