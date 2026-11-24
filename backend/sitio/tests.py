"""
Pruebas de las páginas del sitio (plantillas de Django).
Cada página responde 200, muestra los datos de la base de datos y marca su
sección en el menú. Ejecutar todas las pruebas:  python manage.py test -v 2
"""
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from adopciones.models import Jornada


class PaginasTests(TestCase):

    def test_P01_todas_las_paginas_responden(self):
        """P01 Las páginas del mapa del sitio responden 200 y marcan su sección en el menú."""
        paginas = {
            'sitio:inicio': 'Inicio', 'sitio:animales': 'Animales', 'sitio:adoptar': 'Adoptar',
            'sitio:voluntarios': 'Voluntarios', 'sitio:consulta': 'Mi solicitud', 'sitio:contacto': 'Contacto',
        }
        for nombre, enlace in paginas.items():
            with self.subTest(nombre):
                r = self.client.get(reverse(nombre))
                self.assertEqual(r.status_code, 200)
                self.assertContains(r, f'aria-current="page">{enlace}</a>', html=False)
                self.assertContains(r, 'Mapa del sitio')
        self.assertEqual(self.client.get(reverse('sitio:panel')).status_code, 200)

    def test_P02_inicio_con_datos_reales(self):
        """P02 Inicio muestra cuántos animales están disponibles y tres retratos."""
        r = self.client.get(reverse('sitio:inicio'))
        self.assertContains(r, 'hay 5 animales esperando')
        self.assertContains(r, 'class="retrato"', count=3)

    def test_P03_catalogo_y_filtros(self):
        """P03 /animales/ lista los 6 animales; ?especie=gato solo gatos; ?tamano=grande solo Zeus; filtro inválido avisa."""
        r = self.client.get(reverse('sitio:animales'))
        self.assertContains(r, 'class="tarjeta"', count=6)
        r = self.client.get(reverse('sitio:animales'), {'especie': 'gato'})
        self.assertContains(r, 'class="tarjeta"', count=2)
        self.assertContains(r, 'Tomás')
        self.assertNotContains(r, 'id="animal-1"')
        r = self.client.get(reverse('sitio:animales'), {'tamano': 'grande'})
        self.assertContains(r, 'class="tarjeta"', count=1)
        self.assertContains(r, 'Zeus')
        r = self.client.get(reverse('sitio:animales'), {'especie': 'loro'})
        self.assertContains(r, 'Ese filtro no existe')
        self.assertContains(r, 'class="tarjeta"', count=6)

    def test_P04_ficha_de_un_animal(self):
        """P04 /animales/1/ muestra la ficha de Luna; /animales/999/ responde 404 con la página propia."""
        r = self.client.get(reverse('sitio:ficha', args=[1]))
        self.assertContains(r, 'placa placa--grande">Luna</h1>', html=False)
        self.assertContains(r, '2 años')
        self.assertContains(r, '/adoptar/?animal=1#solicitud')
        r = self.client.get(reverse('sitio:ficha', args=[999]))
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, 'No encontramos esta página', status_code=404)

    def test_P05_adoptar_preselecciona_el_animal(self):
        """P05 /adoptar/?animal=3 deja elegida a Canela; Zeus (en proceso) aparece deshabilitado."""
        r = self.client.get(reverse('sitio:adoptar'), {'animal': 3})
        html = r.content.decode()
        canela = html[html.index('<option value="3"'):html.index('</option>', html.index('<option value="3"'))]
        zeus = html[html.index('<option value="4"'):html.index('</option>', html.index('<option value="4"'))]
        self.assertIn('selected', canela)
        self.assertIn('disabled', zeus)

    def test_P06_jornadas_desde_la_base_de_datos(self):
        """P06 /voluntarios/ muestra las jornadas futuras y oculta las pasadas; sin jornadas, un aviso."""
        Jornada.objects.all().delete()
        self.assertContains(self.client.get(reverse('sitio:voluntarios')), 'no hay jornadas programadas')
        hoy = timezone.localdate()
        Jornada.objects.create(fecha=hoy + timedelta(days=2), hora_inicio='08:00', hora_fin='12:00',
                               actividad='Baño de prueba', lugar='Refugio', cupos=5)
        Jornada.objects.create(fecha=hoy - timedelta(days=2), hora_inicio='08:00', hora_fin='12:00',
                               actividad='Jornada vieja', lugar='Refugio', cupos=5)
        r = self.client.get(reverse('sitio:voluntarios'))
        self.assertContains(r, 'Baño de prueba')
        self.assertNotContains(r, 'Jornada vieja')
        self.assertContains(self.client.get(reverse('sitio:inicio')), 'Próxima jornada')
