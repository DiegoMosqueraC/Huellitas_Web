# 6. Semáforo del proyecto y pendientes

Fecha de corte: 27/10/2026.

🟢 LISTO: funciona y está probado · 🟡 EN DESARROLLO: existe parcialmente · 🔴 CRÍTICO: no existe o no funciona

> Regla de la clase: no ocultar los rojos. Los rojos son el plan de trabajo.

## 6.1 Semáforo

| Aspecto | Estado | Evidencia o motivo |
|---|---|---|
| Interfaz | 🟢 | HTML5 semántico + `estilos.css`, adaptada a celular |
| Navegación | 🟢 | Menú como componente compartido entre `index.html` y `animal.html` |
| Funcionalidades: catálogo y detalle | 🟢 | Consumen la API; pruebas T01–T05 y manuales |
| Funcionalidades: solicitud de adopción | 🟢 | Flujo vertical completo; pruebas T13–T21 y manuales |
| Funcionalidades: registro de voluntarios | 🟢 | `POST /api/voluntarios/` conectado al formulario; pruebas T25–T32 y manuales |
| API | 🟢 | Contrato documentado en `04-contrato-api.md` |
| Endpoints | 🟢 | Animales (CRUD), solicitudes y voluntarios (registro, consulta y cambio de estado con PATCH) |
| Gestión del proceso de adopción | 🟢 | Pantalla `admin.html` con inicio de sesión, solicitudes y voluntarios; usa los PATCH de la API. También está el panel `/admin/` de Django con las mismas reglas |
| Backend | 🟢 | Django + DRF con Controller → Service → Repository |
| Datos | 🟡 | SQLite con datos iniciales por migración; las fotos son rutas fijas del frontend |
| Seguridad | 🟡 | Token Bearer con cierre de sesión que lo invalida, permisos 401/403, límite de 10 intentos de inicio de sesión por minuto, validación e integridad. Faltan HTTPS y llave secreta por variable de entorno en producción |
| Pruebas | 🟢 | 48 pruebas automáticas (todas PASS) + pruebas manuales y por HTTP |
| Documentación | 🟢 | Carpeta `docs/` y `README.md` |
| Arquitectura | 🟢 | Componentes, capas y MVC documentados y aplicados |

## 6.2 Lista concreta de pendientes (plan de trabajo)

1. ✅ **Voluntarios** (estaba en rojo): hecho el 27/10/2026 con el modelo `Voluntario`, `VoluntarioService`, `VoluntarioRepository`, `POST /api/voluntarios/` y el formulario conectado. Reutilizó el mismo formato de error, el cliente `api.js` y las ayudas de `formularios.js`.
2. ✅ **Gestión de solicitudes y voluntarios:** hecho el 27/10/2026. `PATCH /api/solicitudes/{id}/` controla las transiciones y aprueba en una transacción que pasa el animal a EN_PROCESO; `PATCH /api/voluntarios/{id}/` activa e inactiva voluntarios. Las acciones del panel `/admin/` usan el mismo servicio.
   - ✅ **Pantalla de administración en el frontend:** hecha el 27/10/2026 (`admin.html`, `js/admin.js`, `POST`/`DELETE /api/sesion/`).
   - 🟡 **Gestión de animales desde `admin.html`:** crear, editar y retirar animales hoy se hace por la API o en `/admin/`; la pantalla propia solo gestiona solicitudes y voluntarios.
   - 🟡 **Adopción que no se concreta:** APROBADA es un estado final. Si la familia desiste, falta un paso para "cancelar" que devuelva el animal a DISPONIBLE.
   - 🟡 **Otras solicitudes del mismo animal:** al aprobar una, las demás solicitudes activas para ese animal siguen abiertas (ya no se pueden aprobar: dan 409). Se podrían rechazar automáticamente con una observación.
3. 🟡 **Notificaciones:** `NotificacionService` para enviar un correo al registrar la solicitud (componente aparte del controlador, como se vio en la Actividad 2).
4. 🟡 **Fotos:** guardar las fotos de los animales y de la vivienda como archivos del backend (`ImageField` + carpeta `media/`) en lugar de rutas fijas. Por ahora el campo de foto del formulario está deshabilitado.
5. 🟡 **Reto del cambio:** cuentas de solicitante y "Mis solicitudes" (ver 4.8).
6. 🟡 **Despliegue seguro:** `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY` propia, HTTPS y servir el frontend con un servidor web (no con Django).
7. **Próxima clase (persistencia + integración real):** decidir el motor de base de datos definitivo. Gracias a los repositorios, el cambio se limita a `settings.py` y a `repositorios.py`.

## 6.3 Bloqueos y riesgos técnicos identificados

- **Fotos en la base de datos:** guardar la ruta del frontend acopla el backend con la estructura de carpetas del frontend.
- **Abrir `index.html` con doble clic no funciona:** los módulos de JavaScript necesitan un servidor (`file://` los bloquea). Siempre se usa `http://127.0.0.1:8000/` (o Live Server con la API encendida).
- **Datos personales:** las solicitudes contienen documento, dirección y teléfono. Antes de publicar el sitio se necesita HTTPS y una política de retención de datos.
