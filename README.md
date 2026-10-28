# Huellitas Web

Sistema de adopción de mascotas y voluntariado de la Fundación Huellitas de Esperanza (organización **de ejemplo**, con fines académicos).

Desarrollo Avanzado de Aplicaciones en Red, Ingeniería de Software, FESC, VI semestre.
Equipo: Diego Alejandro Mosquera Caicedo, José Miguel Vera Castillo, Camilo Andres Jaimes Gamboa.

## Evolución

| Entrega | Contenido |
|---|---|
| 1 | Página en HTML5 puro (sin CSS ni JavaScript) |
| 2 | Componentes reutilizables, CSS y API REST con Django + Django REST Framework organizada en capas (Controller → Service → Repository). Flujos verticales completos: **registrar una solicitud de adopción** y **registrarse como voluntario** |

## Estructura

```
Huellitas_Web_HTML5/
├── refugio-html5/            CAPA DE PRESENTACIÓN (frontend)
│   ├── index.html            Inicio, catálogo, solicitud, voluntarios, contacto
│   ├── animal.html           Ficha de un animal (GET /api/animales/{id}/)
│   ├── admin.html            Panel del personal: sesión, solicitudes y voluntarios
│   ├── css/estilos.css
│   ├── js/api.js             Cliente HTTP: fetch + formato de error
│   ├── js/componentes.js     <hh-encabezado>, <hh-pie>, tarjetas, mensajes
│   ├── js/formularios.js     Marcado de errores compartido por los formularios
│   ├── js/inicio.js          Controlador: catálogo y solicitud de adopción
│   ├── js/voluntarios.js     Controlador: registro de voluntarios
│   ├── js/detalle.js         Controlador de la ficha
│   ├── js/admin.js           Controlador del panel de administración
│   └── img/
├── backend/                  API REST (Django + DRF)
│   ├── huellitas/            Configuración (settings.py, urls.py)
│   └── adopciones/
│       ├── models.py         MODELO: Animal, SolicitudAdopcion, Voluntario
│       ├── repositorios.py   REPOSITORY: acceso a datos
│       ├── servicios.py      SERVICE: reglas de negocio
│       ├── views.py          CONTROLLER: recibe, coordina, responde
│       ├── serializers.py    Formato JSON de entrada y salida
│       ├── errores.py        Errores de negocio + manejador global
│       ├── autenticacion.py  Token Bearer (401)
│       ├── permisos.py       Quién puede hacer qué (403)
│       ├── urls.py           Endpoints
│       ├── admin.py          Panel /admin/ (sus acciones usan los servicios)
│       ├── tests.py          Matriz de pruebas (48 casos)
│       └── migrations/       Esquema + 6 animales iniciales
└── docs/                     Actividades de clase
    ├── 01-componentes.md
    ├── 02-arquitectura-por-capas.md
    ├── 03-mvc.md
    ├── 04-contrato-api.md
    ├── 05-pruebas.md
    ├── 06-semaforo-y-pendientes.md
    └── evidencias/resultado-pruebas.txt
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

Luego abrir **http://127.0.0.1:8000/**. Django sirve la página y la API en el mismo origen.

> No abras `index.html` con doble clic: los módulos de JavaScript necesitan un servidor. Si prefieres Live Server de VS Code (puerto 5500), deja también encendido `runserver`; la API ya permite ese origen (CORS).

### Ejecutar las pruebas

```powershell
cd backend
.venv\Scripts\python manage.py test adopciones -v 2
```

### Panel de administración

1. Crear una cuenta para el personal (pide usuario, correo y contraseña):

   ```powershell
   cd backend
   .venv\Scripts\python manage.py createsuperuser
   ```

2. Abrir **http://127.0.0.1:8000/admin.html** (también hay un enlace "Acceso para el personal" en el pie de página) e iniciar sesión.
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
| GET | `/api/animales/` | Público | Lista animales (`?especie=perro\|gato`, `?estado=...`) |
| GET | `/api/animales/{id}/` | Público | Un animal |
| POST | `/api/animales/` | Administrador | Crea un animal |
| PUT / PATCH | `/api/animales/{id}/` | Administrador | Actualiza un animal |
| DELETE | `/api/animales/{id}/` | Administrador | Elimina (409 si tiene solicitudes) |
| POST | `/api/solicitudes/` | Público | Registra una solicitud de adopción |
| GET | `/api/solicitudes/` | Administrador | Lista las solicitudes |
| GET | `/api/solicitudes/{id}/` | Administrador | Una solicitud |
| PATCH | `/api/solicitudes/{id}/` | Administrador | Cambia el estado: EN_REVISION, APROBADA o RECHAZADA (con observación) |
| POST | `/api/voluntarios/` | Público | Registra un voluntario |
| GET | `/api/voluntarios/` | Administrador | Lista los voluntarios |
| GET | `/api/voluntarios/{id}/` | Administrador | Un voluntario |
| PATCH | `/api/voluntarios/{id}/` | Administrador | Activa o inactiva un voluntario |
| POST | `/api/sesion/` | Público (10 intentos por minuto) | Inicia sesión y devuelve el token |
| DELETE | `/api/sesion/` | Con token | Cierra sesión e invalida el token |

El contrato completo (entrada, proceso, salida, errores y seguridad) está en [docs/04-contrato-api.md](docs/04-contrato-api.md).

## Preguntas individuales

Las preguntas individuales de las clases ("responda sin consultar al equipo", "desafío individual") las debe responder cada integrante con sus propias palabras. Esta documentación sirve de apoyo, no de respuesta.
