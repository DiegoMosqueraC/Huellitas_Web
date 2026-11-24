# Huellitas Web

Sistema de adopción de mascotas y voluntariado de la Fundación Huellitas de Esperanza (organización **de ejemplo**, con fines académicos).

Desarrollo Avanzado de Aplicaciones en Red, Ingeniería de Software, FESC, VI semestre.
Equipo: Diego Alejandro Mosquera Caicedo, José Miguel Vera Castillo, Camilo Andres Jaimes Gamboa.

## Evolución

| Entrega | Contenido |
|---|---|
| 1 | Página en HTML5 puro (sin CSS ni JavaScript) |
| 2 | Componentes reutilizables, CSS y API REST con Django + Django REST Framework organizada en capas (Controller → Service → Repository). Flujos verticales completos: **registrar una solicitud de adopción** y **registrarse como voluntario** |
| 3 | Persistencia e integración real: restricciones de integridad en la base de datos, errores 409 y 503 de la fuente de datos, prueba de persistencia después de reiniciar, panel de administración y rediseño visual de la página |
| 4 | Sitio de varias páginas con plantillas de Django (adiós a la página única), consulta del estado de una solicitud, jornadas de voluntariado en la base de datos y filtro por tamaño |

## Estructura

```
Huellitas_Web_HTML5/
├── backend/                  Proyecto Django
│   ├── huellitas/            Configuración (settings.py, urls.py)
│   ├── sitio/                PÁGINAS (presentación: vistas + plantillas)
│   │   ├── views.py          Una vista por página; usan los servicios de adopciones
│   │   ├── urls.py           Mapa del sitio
│   │   ├── tests.py          Pruebas de las páginas (P01 a P06)
│   │   ├── templates/sitio/  base.html (encabezado, menú y pie) y una plantilla por página
│   │   ├── templates/404.html, 500.html
│   │   └── static/           css/estilos.css, img/ y js/ (formularios y panel que usan la API)
│   └── adopciones/           API REST (Django REST Framework)
│       ├── models.py         MODELO: Animal, SolicitudAdopcion, Voluntario, Jornada
│       ├── repositorios.py   REPOSITORY: acceso a datos
│       ├── servicios.py      SERVICE: reglas de negocio
│       ├── views.py          CONTROLLER: recibe, coordina, responde
│       ├── serializers.py    Formato JSON de entrada y salida
│       ├── errores.py        Errores de negocio + manejador global
│       ├── autenticacion.py  Token Bearer (401)
│       ├── permisos.py       Quién puede hacer qué (403)
│       ├── urls.py           Endpoints
│       ├── admin.py          Panel /admin/ (sus acciones usan los servicios)
│       ├── tests.py          Matriz de pruebas de la API (T01 a T58)
│       └── migrations/       Esquema, datos iniciales (animales y jornadas) y restricciones
│   └── verificar_persistencia.py  Prueba: registrar, reiniciar el servicio y consultar
└── docs/                     Actividades de clase
    ├── 01-componentes.md
    ├── 02-arquitectura-por-capas.md
    ├── 03-mvc.md
    ├── 04-contrato-api.md
    ├── 05-pruebas.md
    ├── 06-semaforo-y-pendientes.md
    ├── 07-sitio-django.md          Mapa del sitio y arquitectura de la entrega 4
    ├── Taller_Integracion_Equipo_HuellitasWeb.pdf   Documento del taller (y su .docx)
    └── evidencias/               Salidas de las pruebas, de la persistencia y de la estructura de la BD
```

## Cómo ejecutarlo (Windows)

Requisitos: Python 3.10 o superior.

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py runserver
```

Luego abrir **http://127.0.0.1:8000/**. Django sirve las páginas y la API.

## Mapa del sitio

| Dirección | Página |
|---|---|
| `/` | Inicio: portada, quiénes somos, cómo ayudar y próxima jornada |
| `/animales/` | Catálogo con filtros por especie y tamaño (`?especie=gato&tamano=pequeno`) y tabla resumen |
| `/animales/{id}/` | Ficha de un animal |
| `/adoptar/` | Requisitos, pasos, preguntas frecuentes y formulario de solicitud (`?animal={id}` lo deja elegido) |
| `/voluntarios/` | Próximas jornadas y registro de voluntarios |
| `/mi-solicitud/` | Consulta del estado de una solicitud con su número y el documento |
| `/contacto/` | Dirección, horario y otras formas de ayudar |
| `/panel/` | Panel del personal (requiere cuenta) |
| `/admin/` | Administración de Django: animales, jornadas, solicitudes y voluntarios |

### Ejecutar las pruebas

```powershell
cd backend
.venv\Scripts\python manage.py test -v 2
```

Prueba de persistencia (enciende y apaga su propio servidor en el puerto 8010 y borra lo que crea):

```powershell
cd backend
.venv\Scripts\python verificar_persistencia.py
```

### Panel de administración

1. Crear una cuenta para el personal (pide usuario, correo y contraseña):

   ```powershell
   cd backend
   .venv\Scripts\python manage.py createsuperuser
   ```

2. Abrir **http://127.0.0.1:8000/panel/** (también está en el pie de página, "Acceso para el personal") e iniciar sesión.
3. En la pestaña **Solicitudes** se pasan a revisión, se aprueban o se rechazan (el rechazo pide el motivo). En **Voluntarios** se activan después de la inducción o se inactivan.

### Usar la API de administrador directamente

Obtener un token con `POST /api/sesion/` (`{"usuario": "...", "clave": "..."}`) y enviarlo en cada petición protegida:

```http
GET /api/solicitudes/
Authorization: Bearer <token>
```

Por ejemplo, para mover una solicitud por el proceso de adopción:

```http
PATCH /api/solicitudes/1/
Authorization: Bearer <token>
Content-Type: application/json

{ "estado": "EN_REVISION" }
```

El panel de administración está en http://127.0.0.1:8000/admin/. Allí el estado es de solo lectura; se cambia con las acciones de la lista ("Pasar a EN REVISIÓN", "APROBAR", "ACTIVAR", "INACTIVAR"), que aplican las mismas reglas que la API.

## Endpoints

| Método | Endpoint | Quién | Descripción |
|---|---|---|---|
| GET | `/api/animales/` | Público | Lista animales (`?especie=perro\|gato`, `?tamano=pequeno\|mediano\|grande`, `?estado=...`) |
| GET | `/api/animales/{id}/` | Público | Un animal |
| POST | `/api/animales/` | Administrador | Crea un animal |
| PUT / PATCH | `/api/animales/{id}/` | Administrador | Actualiza un animal |
| DELETE | `/api/animales/{id}/` | Administrador | Elimina (409 si tiene solicitudes) |
| POST | `/api/solicitudes/` | Público | Registra una solicitud de adopción |
| GET | `/api/solicitudes/` | Administrador | Lista las solicitudes |
| GET | `/api/solicitudes/{id}/` | Administrador | Una solicitud |
| PATCH | `/api/solicitudes/{id}/` | Administrador | Cambia el estado: EN_REVISION, APROBADA o RECHAZADA (con observación) |
| POST | `/api/solicitudes/consulta/` | Público (10 por minuto) | Estado de una solicitud con `{numero, documento}`, sin datos personales |
| POST | `/api/voluntarios/` | Público | Registra un voluntario |
| GET | `/api/voluntarios/` | Administrador | Lista los voluntarios |
| GET | `/api/voluntarios/{id}/` | Administrador | Un voluntario |
| PATCH | `/api/voluntarios/{id}/` | Administrador | Activa o inactiva un voluntario |
| POST | `/api/sesion/` | Público (10 intentos por minuto) | Inicia sesión y devuelve el token |
| DELETE | `/api/sesion/` | Con token | Cierra sesión e invalida el token |
| GET | `/api/jornadas/` | Público | Próximas jornadas de voluntariado |

El contrato completo (entrada, proceso, salida, errores y seguridad) está en [docs/04-contrato-api.md](docs/04-contrato-api.md).

## Preguntas individuales

Las preguntas individuales de las clases ("responda sin consultar al equipo", "desafío individual") las debe responder cada integrante con sus propias palabras. Esta documentación sirve de apoyo, no de respuesta.
