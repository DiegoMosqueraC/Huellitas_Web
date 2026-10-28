/*
  Cliente HTTP del frontend.
  Construye la solicitud (método, endpoint, encabezados, cuerpo JSON), la envía
  con fetch() y convierte la respuesta en datos o en un ErrorApi con el formato
  de error que define el contrato de la API.
*/

// Con Django la página y la API comparten origen. Con Live Server (puerto 5500)
// la API sigue en el puerto 8000.
const BASE_API = location.port === '5500' ? 'http://127.0.0.1:8000/api' : '/api';

/* Sesión del administrador. Se guarda en sessionStorage (se borra al cerrar la
   pestaña) y no en localStorage, para que el token no quede guardado en el equipo. */
const CLAVE_SESION = 'huellitas.sesion';

export const sesion = {
  obtener() {
    try {
      return JSON.parse(sessionStorage.getItem(CLAVE_SESION));
    } catch {
      return null;
    }
  },
  guardar(datos) {
    try {
      sessionStorage.setItem(CLAVE_SESION, JSON.stringify(datos));
    } catch {
      /* Sin almacenamiento la sesión dura solo mientras la página esté abierta. */
    }
  },
  borrar() {
    try {
      sessionStorage.removeItem(CLAVE_SESION);
    } catch {
      /* Nada que borrar. */
    }
  },
};

export class ErrorApi extends Error {
  constructor(estado, codigo, mensaje, detalles = null) {
    super(mensaje);
    this.estado = estado;
    this.codigo = codigo;
    this.detalles = detalles;
  }
}

async function solicitar(metodo, ruta, cuerpo, { autenticado = false } = {}) {
  const opciones = { method: metodo, headers: { Accept: 'application/json' } };
  if (cuerpo !== undefined) {
    opciones.headers['Content-Type'] = 'application/json';
    opciones.body = JSON.stringify(cuerpo);
  }
  // El token solo viaja en las operaciones de administración: así un token vencido
  // no afecta las páginas públicas.
  const token = autenticado && sesion.obtener()?.token;
  if (token) opciones.headers.Authorization = `Bearer ${token}`;

  let respuesta;
  try {
    respuesta = await fetch(BASE_API + ruta, opciones);
  } catch {
    throw new ErrorApi(0, 'SIN_CONEXION', 'No fue posible conectar con el servidor. Verifica que la API esté encendida.');
  }

  if (respuesta.status === 204) return null;
  const datos = await respuesta.json().catch(() => null);

  if (!respuesta.ok) {
    const error = datos?.error;
    throw new ErrorApi(
      respuesta.status,
      error?.codigo ?? 'ERROR',
      error?.mensaje ?? `El servidor respondió con el código ${respuesta.status}.`,
      error?.detalles ?? null,
    );
  }
  return datos;
}

const ADMIN = { autenticado: true };

export const api = {
  listarAnimales: (especie) =>
    solicitar('GET', '/animales/' + (especie ? `?especie=${encodeURIComponent(especie)}` : '')),
  obtenerAnimal: (id) => solicitar('GET', `/animales/${encodeURIComponent(id)}/`),
  registrarSolicitud: (datos) => solicitar('POST', '/solicitudes/', datos),
  registrarVoluntario: (datos) => solicitar('POST', '/voluntarios/', datos),

  // Administración (requieren sesión de administrador).
  iniciarSesion: (usuario, clave) => solicitar('POST', '/sesion/', { usuario, clave }),
  cerrarSesion: () => solicitar('DELETE', '/sesion/', undefined, ADMIN),
  listarSolicitudes: () => solicitar('GET', '/solicitudes/', undefined, ADMIN),
  cambiarEstadoSolicitud: (id, estado, observacion = '') =>
    solicitar('PATCH', `/solicitudes/${encodeURIComponent(id)}/`, { estado, observacion }, ADMIN),
  listarVoluntarios: () => solicitar('GET', '/voluntarios/', undefined, ADMIN),
  cambiarEstadoVoluntario: (id, estado) =>
    solicitar('PATCH', `/voluntarios/${encodeURIComponent(id)}/`, { estado }, ADMIN),
};
