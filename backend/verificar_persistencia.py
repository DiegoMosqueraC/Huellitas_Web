"""
Prueba de integración: persistencia después de reiniciar el servicio.

Demuestra que el endpoint no simula el almacenamiento:
1. Enciende el servidor y registra una solicitud con POST /api/solicitudes/.
2. Comprobación doble: lee el registro directamente del archivo SQLite.
3. Apaga el servidor (el proceso termina; nada queda en memoria).
4. Lo enciende de nuevo y consulta el registro con GET /api/solicitudes/{id}/.
Al terminar borra lo que creó. Uso:  .venv\\Scripts\\python verificar_persistencia.py
"""
import json
import os
import secrets
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import django

BASE_DIR = Path(__file__).resolve().parent
PUERTO = 8010
BASE = f'http://127.0.0.1:{PUERTO}/api'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'huellitas.settings')
django.setup()

from django.conf import settings  # noqa: E402
from django.contrib.auth.models import User  # noqa: E402

from adopciones.models import SolicitudAdopcion  # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def llamar(metodo, ruta, cuerpo=None, token=None):
    cabeceras = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    if token:
        cabeceras['Authorization'] = f'Bearer {token}'
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    peticion = urllib.request.Request(BASE + ruta, datos, cabeceras, method=metodo)
    try:
        with urllib.request.urlopen(peticion, timeout=10) as respuesta:
            return respuesta.status, json.loads(respuesta.read() or 'null')
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read() or 'null')


def encender():
    proceso = subprocess.Popen(
        [sys.executable, 'manage.py', 'runserver', f'127.0.0.1:{PUERTO}', '--noreload'],
        cwd=BASE_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(60):
        try:
            llamar('GET', '/animales/')
            return proceso
        except OSError:
            time.sleep(0.5)
    proceso.kill()
    raise SystemExit('El servidor no respondió.')


def apagar(proceso):
    proceso.terminate()
    proceso.wait(timeout=15)
    try:
        llamar('GET', '/animales/')
    except OSError:
        return
    raise SystemExit('El servidor sigue respondiendo después de apagarlo.')


def comprobar(condicion, mensaje):
    print(('  OK    ' if condicion else '  FALLA ') + mensaje)
    if not condicion:
        raise SystemExit(1)


clave = secrets.token_urlsafe(18)
admin = User.objects.create_user('verificacion_persistencia', password=clave, is_staff=True)
solicitud_id = None
servidor = None
try:
    print("Fuente de datos: SQLite, archivo backend/db.sqlite3")

    print('\n1. Se enciende el servicio y se registra una solicitud')
    servidor = encender()
    estado, creada = llamar('POST', '/solicitudes/', {
        'animal_id': 2, 'nombre': 'Persona De Prueba', 'tipo_documento': 'CC', 'documento': '9000000001',
        'fecha_nacimiento': '1990-01-01', 'correo': 'prueba@correo.com', 'telefono': '3000000001',
        'direccion': 'Calle 1 # 2-3', 'ciudad': 'Cúcuta', 'tipo_vivienda': 'casa', 'tenencia': 'propia',
        'personas_hogar': 2, 'motivo': 'Registro creado por la prueba de persistencia.',
        'acepta_datos': True, 'acepta_visita': True,
    })
    comprobar(estado == 201, f'POST /api/solicitudes/ -> {estado}, id {creada.get("id")}, estado {creada.get("estado")}')
    solicitud_id = creada['id']

    print('\n2. Comprobación doble: el registro está en la base de datos')
    with sqlite3.connect(settings.DATABASES['default']['NAME']) as conexion:
        fila = conexion.execute(
            'SELECT id, nombre, documento, estado FROM adopciones_solicitudadopcion WHERE id = ?', (solicitud_id,)
        ).fetchone()
    comprobar(fila == (solicitud_id, 'Persona De Prueba', '9000000001', 'RECIBIDA'), f'SELECT directo en SQLite -> {fila}')

    print('\n3. Se apaga el servicio')
    apagar(servidor)
    servidor = None
    comprobar(True, 'El servidor ya no acepta conexiones')

    print('\n4. Se enciende de nuevo y se consulta el mismo registro')
    servidor = encender()
    estado, sesion = llamar('POST', '/sesion/', {'usuario': admin.username, 'clave': clave})
    comprobar(estado == 200, f'POST /api/sesion/ -> {estado}')
    estado, leida = llamar('GET', f'/solicitudes/{solicitud_id}/', token=sesion['token'])
    comprobar(estado == 200, f'GET /api/solicitudes/{solicitud_id}/ -> {estado}')
    comprobar(
        (leida['nombre'], leida['documento'], leida['estado']) == ('Persona De Prueba', '9000000001', 'RECIBIDA'),
        f'Mismos datos que antes del reinicio: {leida["nombre"]}, {leida["documento"]}, {leida["estado"]}',
    )
    estado, repetida = llamar('POST', '/solicitudes/', {
        'animal_id': 2, 'nombre': 'Persona De Prueba', 'tipo_documento': 'CC', 'documento': '9000000001',
        'fecha_nacimiento': '1990-01-01', 'correo': 'prueba@correo.com', 'telefono': '3000000001',
        'direccion': 'Calle 1 # 2-3', 'ciudad': 'Cúcuta', 'tipo_vivienda': 'casa', 'tenencia': 'propia',
        'personas_hogar': 2, 'motivo': 'Registro creado por la prueba de persistencia.',
        'acepta_datos': True, 'acepta_visita': True,
    })
    comprobar(estado == 409, f'Repetir el POST después del reinicio -> {estado} (el servicio recuerda la solicitud)')

    print('\nRESULTADO: la información persiste después de reiniciar el servicio.')
finally:
    if servidor:
        servidor.terminate()
    if solicitud_id:
        SolicitudAdopcion.objects.filter(pk=solicitud_id).delete()
    admin.delete()
