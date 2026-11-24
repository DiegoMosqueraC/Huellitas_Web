# Carga las jornadas de voluntariado que antes estaban escritas a mano en el HTML.
# Son datos de demostración; el personal las administra desde /admin/.
import datetime

from django.db import migrations

JORNADAS = [
    ('2026-12-05', '08:00', '12:00', 'Baño y cepillado', 'Refugio', 10),
    ('2026-12-13', '09:00', '15:00', 'Feria de adopción', 'Parque Santander, Cúcuta', 15),
    ('2026-12-19', '08:00', '11:00', 'Paseo y socialización', 'Refugio', 8),
    ('2027-01-16', '07:00', '13:00', 'Jornada de esterilización', 'Salón comunal, barrio de ejemplo', 12),
]


def cargar_jornadas(apps, schema_editor):
    Jornada = apps.get_model('adopciones', 'Jornada')
    for fecha, inicio, fin, actividad, lugar, cupos in JORNADAS:
        Jornada.objects.create(
            fecha=datetime.date.fromisoformat(fecha),
            hora_inicio=datetime.time.fromisoformat(inicio),
            hora_fin=datetime.time.fromisoformat(fin),
            actividad=actividad, lugar=lugar, cupos=cupos,
        )


def borrar_jornadas(apps, schema_editor):
    Jornada = apps.get_model('adopciones', 'Jornada')
    Jornada.objects.filter(actividad__in=[j[3] for j in JORNADAS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('adopciones', '0006_jornada'),
    ]

    operations = [
        migrations.RunPython(cargar_jornadas, borrar_jornadas),
    ]
