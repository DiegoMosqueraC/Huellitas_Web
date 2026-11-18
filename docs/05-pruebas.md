# 5. Matriz de pruebas

"Funciona" no es suficiente: se prueba el camino feliz y que la API **falle correctamente**.

- **Herramienta:** pruebas automáticas de Django REST Framework (`APITestCase`) en `backend/adopciones/tests.py`.
- **Cómo ejecutarlas:** `cd backend` y luego `.venv\Scripts\python manage.py test adopciones -v 2`
- **Evidencia:** salida completa de la ejecución en [`evidencias/resultado-pruebas.txt`](evidencias/resultado-pruebas.txt) (53 pruebas, 53 OK, 10/11/2026).
- Cada prueba usa una base de datos temporal en memoria con los 6 animales iniciales; no modifica `db.sqlite3`.

## 5.1 Resumen por tipo de caso

| Caso | Resultado esperado | Pruebas | Estado |
|---|---|---|---|
| Solicitud válida | 200 / 201 / 204 | T01, T02, T04, T08, T10, T11, T13, T20, T25, T30, T33, T36, T41, T42, T43, T45, T46, T48 | PASS |
| ID inexistente | 404 | T05, T17, T24, T32, T40 | PASS |
| Datos inválidos | 400 | T03, T09, T14, T15, T16, T21, T26, T27, T28, T36, T37, T44 | PASS |
| Sin autenticación | 401 | T06, T22, T31, T40, T44, T46 | PASS |
| Sin permisos | 403 | T07, T22, T31, T40, T45 | PASS |
| Conflicto | 409 | T12, T18, T19, T29, T34, T35, T38, T39, T41 | PASS |
| Demasiados intentos | 429 | T47 | PASS |
| Error inesperado | 500 | T23, T50 | PASS |
| Base de datos no disponible | 503 | T49 | PASS |
| Restricciones de la base de datos | `IntegrityError` → 409 | T51, T52 | PASS |
| Consistencia entre operaciones | 201 → 200 → 200 | T53 | PASS |

## 5.2 Detalle de cada prueba

| ID | Entrada | Esperado | Obtenido | Estado |
|---|---|---|---|---|
| T01 | `GET /api/animales/` | 200 con 6 animales | 200, 6 animales, el primero Luna | PASS |
| T02 | `GET /api/animales/?especie=gato` | 200 solo gatos | 200, Tomás y Miel | PASS |
| T03 | `GET /api/animales/?especie=loro` | 400 `DATOS_INVALIDOS` con detalle `especie` | 400, detalle en `especie` | PASS |
| T04 | `GET /api/animales/1/` | 200 Luna, `edad_texto` "2 años" | 200, Luna, "2 años" | PASS |
| T05 | `GET /api/animales/999/` | 404 `RECURSO_NO_ENCONTRADO` | 404 con JSON de error | PASS |
| T06 | `POST /api/animales/` sin token | 401 `NO_AUTENTICADO` y `WWW-Authenticate: Bearer` | 401 con el encabezado | PASS |
| T07 | `POST /api/animales/` con token de usuario no administrador | 403 `SIN_PERMISO` | 403 | PASS |
| T08 | `POST /api/animales/` como administrador con datos válidos | 201, estado DISPONIBLE y `Location` | 201, `Location: /api/animales/7/` | PASS |
| T09 | `POST /api/animales/` con `edad_meses: -5` y `especie: "loro"` | 400 con detalles en ambos campos | 400, detalles en `edad_meses` y `especie` | PASS |
| T10 | `PATCH /api/animales/4/` `{"estado": "ADOPTADO"}` | 200 con el estado nuevo | 200, ADOPTADO | PASS |
| T11 | `DELETE /api/animales/6/` y luego `GET` | 204 y luego 404 | 204 / 404 | PASS |
| T12 | `DELETE /api/animales/1/` con una solicitud registrada | 409 `CONFLICTO`; el animal no se borra | 409, Luna sigue existiendo | PASS |
| T13 | `POST /api/solicitudes/` válida | 201, estado RECIBIDA, animal Luna, `Location` | 201 con esos datos; 1 registro en la BD | PASS |
| T14 | `POST /api/solicitudes/` con celular, correo y motivo inválidos | 400 con 3 detalles; nada se guarda | 400, detalles en `telefono`, `correo`, `motivo`; 0 registros | PASS |
| T15 | `POST /api/solicitudes/` de un menor de 15 años | 400 con detalle `fecha_nacimiento` | 400 | PASS |
| T16 | `POST /api/solicitudes/` sin autorizaciones | 400 con detalles `acepta_datos` y `acepta_visita` | 400 | PASS |
| T17 | `POST /api/solicitudes/` con `animal_id: 999` | 404 | 404 | PASS |
| T18 | `POST /api/solicitudes/` para Zeus (EN_PROCESO) | 409 con el nombre del animal en el mensaje | 409 "Zeus no está disponible…" | PASS |
| T19 | Misma solicitud enviada dos veces | 409 en la segunda; 1 solo registro | 409; 1 registro | PASS |
| T20 | `POST /api/solicitudes/` con `"estado": "APROBADA"` | 201 con estado RECIBIDA (integridad) | 201, RECIBIDA | PASS |
| T21 | `POST /api/solicitudes/` con cuerpo `{"nombre": ` | 400 `JSON_INVALIDO` | 400 | PASS |
| T22 | `GET /api/solicitudes/` sin token, como voluntario y como administrador | 401, 403 y 200 | 401, 403, 200 | PASS |
| T23 | `GET /api/animales/` simulando que la BD falla | 500 `ERROR_INTERNO` sin exponer el error interno | 500, mensaje genérico, error registrado en el log | PASS |
| T24 | `GET /api/mascotas/` (no existe) | 404 en JSON, no una página HTML | 404 JSON | PASS |
| T25 | `POST /api/voluntarios/` válido | 201, estado PENDIENTE y `Location` | 201, PENDIENTE, días guardados | PASS |
| T26 | `POST /api/voluntarios/` sin días, celular "555" y edad 12 | 400 con 3 detalles; nada se guarda | 400, detalles en `disponibilidad`, `telefono`, `edad`; 0 registros | PASS |
| T27 | Voluntario de 16 años en hogar de paso, y luego en eventos | 400 con detalle `area`; luego 201 | 400 / 201 | PASS |
| T28 | `POST /api/voluntarios/` sin autorizar datos | 400 con detalle `acepta_datos` | 400 | PASS |
| T29 | Segundo registro con el mismo correo en mayúsculas | 409; 1 solo registro | 409; 1 registro | PASS |
| T30 | `POST /api/voluntarios/` con `"estado": "ACTIVO"` | 201 con estado PENDIENTE (integridad) | 201, PENDIENTE | PASS |
| T31 | `GET /api/voluntarios/` sin token, como voluntario y como administrador | 401, 403 y 200 | 401, 403, 200 | PASS |
| T32 | `GET /api/voluntarios/999/` como administrador | 404 | 404 | PASS |
| T33 | `PATCH` solicitud RECIBIDA → EN_REVISION → APROBADA | 200 y 200; Luna pasa a EN_PROCESO | 200 / 200; Luna EN_PROCESO | PASS |
| T34 | `PATCH` RECIBIDA → APROBADA (se salta la revisión) | 409; Luna sigue DISPONIBLE | 409; DISPONIBLE | PASS |
| T35 | `PATCH` RECHAZADA → EN_REVISION | 409 "estado final" | 409 | PASS |
| T36 | Rechazar sin observación, y luego con observación | 400 con detalle `observacion`; luego 200 y la observación guardada | 400 / 200 | PASS |
| T37 | `PATCH` con `"estado": "PERDIDA"` | 400 con detalle `estado` | 400 | PASS |
| T38 | Dos solicitudes para Luna: aprobar la primera y luego la segunda | 409 en la segunda, que queda EN_REVISION | 409; EN_REVISION | PASS |
| T39 | Aprobar una solicitud sin animal asignado | 409 | 409 | PASS |
| T40 | `PATCH` sin token, como voluntario y sobre ids inexistentes | 401, 403 y 404; el estado no cambia | 401, 403, 404; RECIBIDA | PASS |
| T41 | Voluntario PENDIENTE → ACTIVO, y luego ACTIVO → PENDIENTE | 200 y luego 409 | 200 / 409 | PASS |
| T42 | Acciones del panel `/admin/`: "Aprobar" una RECIBIDA, luego revisar y aprobar | La primera se rechaza (sigue RECIBIDA); luego APROBADA y Luna EN_PROCESO | Igual a lo esperado | PASS |
| T43 | `POST /api/sesion/` con credenciales de administrador | 200 con token que sirve para `GET /api/solicitudes/` | 200; el token funciona | PASS |
| T44 | Contraseña incorrecta, usuario inexistente y cuerpo vacío | 401, 401 con el mismo mensaje, y 400 | Igual a lo esperado | PASS |
| T45 | Inicio de sesión de un usuario no administrador | 200 con `es_administrador: false`; 403 en solicitudes | Igual a lo esperado | PASS |
| T46 | `DELETE /api/sesion/` sin token, y luego con token | 401; luego 204 y el token ya no sirve (401) | Igual a lo esperado | PASS |
| T47 | 10 intentos fallidos y luego uno correcto | 429 `DEMASIADOS_INTENTOS` | 429 | PASS |
| T48 | Detalle de solicitud RECIBIDA y de voluntario PENDIENTE | `estados_siguientes` = [EN_REVISION, RECHAZADA] y [ACTIVO, INACTIVO] | Igual a lo esperado | PASS |
| T49 | `GET /api/animales/` con la base de datos sin responder (`OperationalError` simulado) | 503 `SERVICIO_NO_DISPONIBLE` con `Retry-After`, sin detalles internos | 503, `Retry-After: 30` | PASS |
| T50 | Aprobar una solicitud provocando una falla después de actualizar el animal | 500 controlado; la transacción revierte todo | Luna sigue DISPONIBLE y la solicitud EN_REVISION | PASS |
| T51 | Seis escrituras inválidas directo con el ORM (duplicado activo, personas 0, horas 20, sin autorizaciones, voluntario de 10 años, animal de 9999 meses) | La base de datos lanza `IntegrityError` en cada una | Las seis rechazadas; sigue 1 registro | PASS |
| T52 | Segundo voluntario con el mismo correo, simulando que el servicio no lo detectó (carrera) | 409 `CONFLICTO` controlado, no 500 | 409 | PASS |
| T53 | `POST` → `GET` lista → `GET` detalle → `PATCH` → `GET` | El mismo registro con los mismos datos en todas | Coincide | PASS |

## 5.3 Pruebas manuales en el navegador (27/10/2026)

Con el servidor encendido (`http://127.0.0.1:8000/`):

| Caso | Pasos | Resultado |
|---|---|---|
| Catálogo | Abrir la página de inicio | 6 tarjetas, tabla con "Total: 6 animales publicados, 5 disponibles.", Zeus deshabilitado en el formulario |
| Filtro | Pulsar "Gatos" | Solo Tomás y Miel |
| Solicitud válida | Llenar el formulario para Luna y enviar | Mensaje "¡Solicitud #1 recibida para adoptar a Luna!" con estado RECIBIDA |
| Solicitud duplicada | Enviar de nuevo la misma solicitud | Aviso "Ya tienes una solicitud activa para este animal." |
| Error de servidor en un campo | Desactivar la validación HTML y enviar un celular de 5 dígitos | Mensaje de error y el campo Celular marcado en rojo |
| Detalle | Abrir `animal.html?id=4` | Ficha de Zeus con la etiqueta "En proceso de adopción" |
| Detalle inexistente | Abrir `animal.html?id=999` | "Este animal no existe o ya no está publicado." |
| Celular (375 px) | Vista móvil del formulario | Sin desplazamiento horizontal |
| Voluntario sin días | Intentar enviar sin marcar días | El navegador avisa "Elige al menos un día disponible." |
| Voluntario menor en hogar de paso | Edad 16, área "Hogar de paso temporal" | Error del servidor y el campo Área marcado en rojo |
| Voluntario válido | Edad 22, área "Cuidado y paseo", sábados | "¡Registro #1 recibido!" con estado PENDIENTE |
| Voluntario duplicado | Enviar otra vez con el mismo correo | Aviso "Ya hay un voluntario registrado con este correo." |

Las solicitudes y los voluntarios creados durante estas pruebas se borraron después de la base de datos de desarrollo.

## 5.4 Pantalla de administración en el navegador (27/10/2026)

Con un administrador temporal (contraseña aleatoria), dos solicitudes y un voluntario de ejemplo. Al terminar se borró todo y Luna volvió a DISPONIBLE.

| Caso | Resultado |
|---|---|
| Contraseña incorrecta | "Usuario o contraseña incorrectos." |
| Inicio de sesión correcto | Panel con 2 solicitudes, "(2 por atender)", botones "Pasar a revisión" y "Rechazar"; nada guardado en `localStorage` |
| Pasar a revisión la solicitud de Laura | "Solicitud #2: En revisión." y los botones cambian a "Aprobar" y "Rechazar" |
| Aprobarla (con confirmación) | "Luna quedó en proceso de adopción"; la API pública muestra a Luna EN_PROCESO |
| Rechazar la de Jorge sin escribir motivo (validación HTML desactivada) | El servidor responde 400 y el campo Motivo queda marcado en rojo |
| Rechazarla con motivo | "Solicitud #3: Rechazada."; el detalle ("Ver") muestra la observación |
| Activar al voluntario | Queda "Activo" con el botón "Inactivar" |
| Token alterado y "Actualizar" | Vuelve al inicio de sesión: "Tu sesión terminó." El catálogo público sigue funcionando con el token malo guardado |
| Cerrar sesión | "Cerraste sesión."; el token anterior responde 401 en el servidor |

## 5.5 Verificación de los PATCH contra el servidor real (27/10/2026)

Se creó un administrador temporal con token y se recorrió el flujo completo por HTTP. Los resultados están en la tabla de respuestas reales de `04-contrato-api.md` (sección 4.2.2). Al terminar se borraron el usuario temporal, la solicitud y el voluntario, y Canela volvió a DISPONIBLE.

## 5.6 Persistencia después de reiniciar el servicio (17/11/2026)

Prueba obligatoria del taller de integración: registrar, verificar, reiniciar el servicio y consultar de nuevo. Es repetible con:

```powershell
cd backend
.venv\Scripts\python verificar_persistencia.py
```

El guion enciende el servidor en el puerto 8010, registra una solicitud con `POST /api/solicitudes/`, la lee directamente del archivo SQLite, apaga el servidor (comprueba que ya no acepta conexiones), lo enciende de nuevo y consulta el mismo registro con `GET /api/solicitudes/{id}/`. Al terminar borra el registro y el usuario temporal que creó.

| Momento | Comprobación | Resultado |
|---|---|---|
| Antes del reinicio | `POST /api/solicitudes/` | 201, estado RECIBIDA |
| Antes del reinicio | `SELECT` directo en SQLite | El registro está con los datos enviados |
| Servicio apagado | Petición al servidor | Conexión rechazada |
| Después del reinicio | `GET /api/solicitudes/{id}/` | 200, mismos datos |
| Después del reinicio | Repetir el `POST` | 409: el servicio recuerda la solicitud |

Evidencias: [`evidencias/persistencia-tras-reinicio.txt`](evidencias/persistencia-tras-reinicio.txt) y [`evidencias/estructura-base-de-datos.txt`](evidencias/estructura-base-de-datos.txt) (tablas, migraciones, llaves y restricciones leídas del archivo SQLite).
