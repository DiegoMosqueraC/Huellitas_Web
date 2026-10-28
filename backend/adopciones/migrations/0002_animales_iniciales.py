# Carga los 6 animales de ejemplo que antes estaban escritos a mano en index.html.
# Son datos de demostración (la fundación es ficticia).
from django.db import migrations

ANIMALES = [
    {
        'nombre': 'Luna', 'especie': 'perro', 'raza': 'Mestiza (cruce de labrador)', 'sexo': 'hembra',
        'edad_meses': 24, 'tamano': 'mediano', 'salud': 'Vacunada, desparasitada y esterilizada',
        'descripcion': 'Es juguetona y cariñosa, se lleva bien con niños y con otros perros.',
        'historia': 'Luna, rescatada en el barrio La Libertad.', 'foto': 'img/luna.jpg',
        'foto_alt': 'Fotografía de Luna, perra mestiza de pelaje claro, sentada y mirando a la cámara',
        'estado': 'DISPONIBLE',
    },
    {
        'nombre': 'Tomás', 'especie': 'gato', 'raza': 'Criollo', 'sexo': 'macho',
        'edad_meses': 12, 'tamano': 'pequeno', 'salud': 'Vacunado, desparasitado y esterilizado',
        'descripcion': 'Es tranquilo y curioso. Ideal para apartamento.',
        'historia': 'Tomás, rescatado de una alcantarilla cuando era cachorro.', 'foto': 'img/tomas.jpg',
        'foto_alt': 'Fotografía de Tomás, gato criollo joven de pelaje crema, sentado junto a una malla',
        'estado': 'DISPONIBLE',
    },
    {
        'nombre': 'Canela', 'especie': 'perro', 'raza': 'Criolla', 'sexo': 'hembra',
        'edad_meses': 6, 'tamano': 'pequeno',
        'salud': 'Primeras vacunas y desparasitada; esterilización programada',
        'descripcion': 'Llena de energía. Necesita una familia con tiempo para educarla. De adulta será mediana.',
        'historia': 'Canela, rescatada junto a sus cuatro hermanos.', 'foto': 'img/canela.jpg',
        'foto_alt': 'Fotografía de Canela, perra criolla joven de pelaje color canela, sentada',
        'estado': 'DISPONIBLE',
    },
    {
        'nombre': 'Zeus', 'especie': 'perro', 'raza': 'Labrador retriever', 'sexo': 'macho',
        'edad_meses': 60, 'tamano': 'grande', 'salud': 'Vacunado, desparasitado y esterilizado',
        'descripcion': 'Noble y protector. Necesita espacio amplio y paseos diarios.',
        'historia': 'Zeus, rescatado de una situación de maltrato. Fotografía: Can Botey.', 'foto': 'img/zeus.jpg',
        'foto_alt': 'Fotografía de Zeus, labrador retriever de pelaje negro, acostado en el piso',
        'estado': 'EN_PROCESO',
    },
    {
        'nombre': 'Miel', 'especie': 'gato', 'raza': 'Mestiza (cruce de persa)', 'sexo': 'hembra',
        'edad_meses': 36, 'tamano': 'pequeno', 'salud': 'Vacunada, desparasitada y esterilizada',
        'descripcion': 'Muy dulce y tranquila. Le encanta dormir al sol.',
        'historia': 'Miel, entregada al refugio por una familia que no podía cuidarla.', 'foto': 'img/miel.jpg',
        'foto_alt': 'Fotografía de Miel, gata mestiza de pelo largo color naranja, sentada sobre un tapete',
        'estado': 'DISPONIBLE',
    },
    {
        'nombre': 'Rocky', 'especie': 'perro', 'raza': 'Beagle', 'sexo': 'macho',
        'edad_meses': 96, 'tamano': 'mediano',
        'salud': 'Vacunado y esterilizado; requiere control veterinario cada 6 meses',
        'descripcion': 'Calmado y agradecido. Busca un hogar tranquilo para sus años dorados (adulto mayor).',
        'historia': 'Rocky, nuestro abuelito del refugio.', 'foto': 'img/rocky.jpg',
        'foto_alt': 'Fotografía de Rocky, beagle adulto mayor tricolor, acostado sobre una manta',
        'estado': 'DISPONIBLE',
    },
]


def cargar_animales(apps, schema_editor):
    Animal = apps.get_model('adopciones', 'Animal')
    for datos in ANIMALES:
        Animal.objects.create(**datos)


def borrar_animales(apps, schema_editor):
    Animal = apps.get_model('adopciones', 'Animal')
    Animal.objects.filter(nombre__in=[a['nombre'] for a in ANIMALES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('adopciones', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(cargar_animales, borrar_animales),
    ]
