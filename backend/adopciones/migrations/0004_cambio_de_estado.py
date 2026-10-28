# Campos para gestionar el estado de solicitudes y voluntarios:
# observación del administrador y fecha de la última actualización (trazabilidad).
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adopciones', '0003_voluntario'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitudadopcion',
            name='observacion',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='solicitudadopcion',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='voluntario',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
