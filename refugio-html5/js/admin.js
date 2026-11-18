/*
  Controlador del panel de administración (admin.html).
  - Inicia y cierra sesión con /api/sesion/.
  - Lista solicitudes y voluntarios, y cambia su estado con PATCH.
  Los botones de cada fila salen de "estados_siguientes", que calcula el servidor,
  así esta pantalla no repite la regla de qué estado sigue a cuál.
*/
(() => {
  const vistaAcceso = document.querySelector('#acceso');
  const formAcceso = document.querySelector('#form-acceso');
  const resultadoAcceso = document.querySelector('#resultado-acceso');
  const panel = document.querySelector('#panel');
  const usuarioActual = document.querySelector('#usuario-actual');
  const avisoPanel = document.querySelector('#aviso-panel');
  const pestanas = document.querySelectorAll('[data-vista]');
  const tablaSolicitudes = document.querySelector('#tabla-solicitudes');
  const tablaVoluntarios = document.querySelector('#tabla-voluntarios');
  const filtroSolicitudes = document.querySelector('#filtro-solicitudes');
  const filtroVoluntarios = document.querySelector('#filtro-voluntarios');
  const dialogoDetalle = document.querySelector('#dialogo-detalle');
  const dialogoRechazo = document.querySelector('#dialogo-rechazo');
  const formRechazo = document.querySelector('#form-rechazo');
  const resultadoRechazo = document.querySelector('#resultado-rechazo');

  const TEXTO_ACCION = {
    EN_REVISION: 'Pasar a revisión',
    APROBADA: 'Aprobar',
    RECHAZADA: 'Rechazar',
    ACTIVO: 'Activar',
    INACTIVO: 'Inactivar',
  };
  const TEXTO_DIA = { 'entre-semana': 'L-V', sabado: 'Sáb', domingo: 'Dom' };

  let solicitudes = [];
  let voluntarios = [];
  let solicitudARechazar = null;

  const fecha = (iso) => new Date(iso).toLocaleDateString('es-CO', { day: 'numeric', month: 'short', year: 'numeric' });

  /* ---------- Sesión ---------- */

  function mostrarAcceso(tipo, mensaje) {
    panel.hidden = true;
    vistaAcceso.hidden = false;
    if (mensaje) mostrarMensaje(resultadoAcceso, tipo, mensaje);
    formAcceso.elements.usuario.focus();
  }

  async function mostrarPanel() {
    vistaAcceso.hidden = true;
    panel.hidden = false;
    usuarioActual.textContent = sesion.obtener().usuario;
    await cargarDatos();
  }

  // Un 401 en cualquier momento significa que el token ya no sirve (por ejemplo,
  // se cerró la sesión en otra pestaña): se vuelve a pedir el inicio de sesión.
  function manejarError(error, contenedor) {
    if (error.estado === 401) {
      sesion.borrar();
      mostrarAcceso('aviso', 'Tu sesión terminó. Inicia sesión de nuevo.');
      return;
    }
    mostrarMensaje(contenedor, error.estado === 409 ? 'aviso' : 'error', error.message, marcarErrores(formRechazo, error.detalles));
  }

  formAcceso.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const boton = formAcceso.querySelector('button[type="submit"]');
    boton.disabled = true;
    try {
      const datos = await api.iniciarSesion(formAcceso.elements.usuario.value.trim(), formAcceso.elements.clave.value);
      sesion.guardar(datos);
      if (!datos.es_administrador) {
        // Tiene cuenta pero no es personal administrativo: se descarta el token.
        await api.cerrarSesion().catch(() => {});
        sesion.borrar();
        mostrarMensaje(resultadoAcceso, 'error', 'Tu usuario no tiene permisos de administrador.');
        return;
      }
      formAcceso.reset();
      resultadoAcceso.replaceChildren();
      await mostrarPanel();
    } catch (error) {
      mostrarMensaje(resultadoAcceso, 'error', error.message);
      formAcceso.elements.clave.select();
    } finally {
      boton.disabled = false;
    }
  });

  document.querySelector('#boton-salir').addEventListener('click', async () => {
    await api.cerrarSesion().catch(() => {});
    sesion.borrar();
    mostrarAcceso('exito', 'Cerraste sesión.');
  });

  document.querySelector('#boton-actualizar').addEventListener('click', () => cargarDatos());

  /* ---------- Datos ---------- */

  async function cargarDatos() {
    try {
      [solicitudes, voluntarios] = await Promise.all([api.listarSolicitudes(), api.listarVoluntarios()]);
      avisoPanel.replaceChildren();
      pintarSolicitudes();
      pintarVoluntarios();
    } catch (error) {
      manejarError(error, avisoPanel);
    }
  }

  function etiquetaEstado(registro) {
    return crear('span', { clase: `estado estado--${registro.estado.toLowerCase()}` }, registro.estado_texto);
  }

  function botonesDeEstado(registro, tipo) {
    return registro.estados_siguientes.map((estado) =>
      crear('button', {
        type: 'button',
        clase: `accion${estado === 'RECHAZADA' || estado === 'INACTIVO' ? ' accion--peligro' : ''}`,
        'data-tipo': tipo,
        'data-id': registro.id,
        'data-estado': estado,
      }, TEXTO_ACCION[estado]),
    );
  }

  function filaVacia(columnas, texto) {
    return crear('tr', {}, crear('td', { colspan: columnas }, texto));
  }

  function pintarSolicitudes() {
    const filtro = filtroSolicitudes.value;
    const visibles = solicitudes.filter((s) => !filtro || s.estado === filtro);
    tablaSolicitudes.replaceChildren(
      ...(visibles.length ? visibles.map((s) =>
        crear('tr', {},
          crear('td', {}, String(s.id)),
          crear('td', {}, fecha(s.fecha_creacion)),
          crear('td', {}, s.nombre, crear('br'), crear('small', {}, `${s.tipo_documento} ${s.documento}`)),
          crear('td', {}, s.animal ? crear('a', { href: `animal.html?id=${s.animal.id}` }, s.animal.nombre) : 'Sin preferencia'),
          crear('td', {}, etiquetaEstado(s)),
          crear('td', { clase: 'celda-acciones' },
            crear('button', { type: 'button', clase: 'accion accion--neutra', 'data-tipo': 'ver', 'data-id': s.id }, 'Ver'),
            botonesDeEstado(s, 'solicitud'),
          ),
        )) : [filaVacia(6, 'No hay solicitudes con este filtro.')]),
    );
    const porRevisar = solicitudes.filter((s) => s.estado === 'RECIBIDA' || s.estado === 'EN_REVISION').length;
    document.querySelector('#contador-solicitudes').textContent = `(${porRevisar} por atender)`;
  }

  function pintarVoluntarios() {
    const filtro = filtroVoluntarios.value;
    const visibles = voluntarios.filter((v) => !filtro || v.estado === filtro);
    tablaVoluntarios.replaceChildren(
      ...(visibles.length ? visibles.map((v) =>
        crear('tr', {},
          crear('td', {}, v.nombre),
          crear('td', {}, crear('a', { href: `mailto:${v.correo}` }, v.correo), crear('br'), crear('small', {}, v.telefono)),
          crear('td', {}, String(v.edad)),
          crear('td', {}, v.area_texto),
          crear('td', {}, v.disponibilidad.map((d) => TEXTO_DIA[d] ?? d).join(', ')),
          crear('td', {}, etiquetaEstado(v)),
          crear('td', { clase: 'celda-acciones' }, botonesDeEstado(v, 'voluntario')),
        )) : [filaVacia(7, 'No hay voluntarios con este filtro.')]),
    );
    const pendientes = voluntarios.filter((v) => v.estado === 'PENDIENTE').length;
    document.querySelector('#contador-voluntarios').textContent = `(${pendientes} ${pendientes === 1 ? 'pendiente' : 'pendientes'})`;
  }

  /* ---------- Acciones ---------- */

  function reemplazar(lista, actualizado) {
    return lista.map((r) => (r.id === actualizado.id ? actualizado : r));
  }

  async function cambiarSolicitud(id, estado, observacion = '') {
    const actualizada = await api.cambiarEstadoSolicitud(id, estado, observacion);
    solicitudes = reemplazar(solicitudes, actualizada);
    pintarSolicitudes();
    const extra = estado === 'APROBADA' ? ` ${actualizada.animal.nombre} quedó "en proceso de adopción".` : '';
    mostrarMensaje(avisoPanel, 'exito', `Solicitud #${id}: ${actualizada.estado_texto}.${extra}`);
  }

  async function cambiarVoluntario(id, estado) {
    const actualizado = await api.cambiarEstadoVoluntario(id, estado);
    voluntarios = reemplazar(voluntarios, actualizado);
    pintarVoluntarios();
    mostrarMensaje(avisoPanel, 'exito', `${actualizado.nombre}: ${actualizado.estado_texto}.`);
  }

  function verSolicitud(id) {
    const s = solicitudes.find((x) => x.id === id);
    const visita = s.fecha_visita ? `${s.fecha_visita}${s.hora_visita ? ' a las ' + s.hora_visita.slice(0, 5) : ''}` : 'Sin preferencia';
    const filas = [
      ['Solicitante', s.nombre],
      ['Documento', `${s.tipo_documento} ${s.documento}`],
      ['Nacimiento', s.fecha_nacimiento],
      ['Correo', s.correo],
      ['Celular', s.telefono],
      ['Dirección', `${s.direccion}, ${s.ciudad}`],
      ['Vivienda', `${s.tipo_vivienda_texto} (${s.tenencia})`],
      ['Personas en el hogar', String(s.personas_hogar)],
      ['Otras mascotas', s.otras_mascotas.join(', ') || 'No indicó'],
      ['Horas solo al día', String(s.horas_solo)],
      ['Visita preferida', visita],
      ['Motivo', s.motivo],
      ['Estado', s.estado_texto],
      ['Observación', s.observacion || '—'],
      ['Última actualización', new Date(s.fecha_actualizacion).toLocaleString('es-CO')],
    ];
    document.querySelector('#titulo-detalle').textContent =
      `Solicitud #${s.id}${s.animal ? ' · ' + s.animal.nombre : ''}`;
    document.querySelector('#contenido-detalle').replaceChildren(
      ...filas.flatMap(([termino, valor]) => [crear('dt', {}, termino), crear('dd', {}, valor)]),
    );
    dialogoDetalle.showModal();
  }

  function abrirRechazo(id) {
    solicitudARechazar = id;
    formRechazo.reset();
    limpiarErrores(formRechazo);
    resultadoRechazo.replaceChildren();
    document.querySelector('#titulo-rechazo').textContent = `Rechazar la solicitud #${id}`;
    dialogoRechazo.showModal();
  }

  document.querySelector('#cancelar-rechazo').addEventListener('click', () => dialogoRechazo.close());

  formRechazo.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    limpiarErrores(formRechazo);
    try {
      await cambiarSolicitud(solicitudARechazar, 'RECHAZADA', formRechazo.elements.observacion.value);
      dialogoRechazo.close();
    } catch (error) {
      manejarError(error, resultadoRechazo);
    }
  });

  // Un solo manejador para todos los botones de las tablas (delegación de eventos).
  panel.addEventListener('click', async (evento) => {
    const boton = evento.target.closest('button[data-tipo]');
    if (!boton) return;
    const id = Number(boton.dataset.id);
    const { tipo, estado } = boton.dataset;

    if (tipo === 'ver') return verSolicitud(id);
    if (tipo === 'solicitud' && estado === 'RECHAZADA') return abrirRechazo(id);
    if (tipo === 'solicitud' && estado === 'APROBADA' &&
        !confirm(`¿Aprobar la solicitud #${id}? Es definitivo y el animal quedará "en proceso de adopción".`)) return;

    boton.disabled = true;
    try {
      if (tipo === 'solicitud') await cambiarSolicitud(id, estado);
      else await cambiarVoluntario(id, estado);
    } catch (error) {
      manejarError(error, avisoPanel);
      boton.disabled = false;
    }
  });

  pestanas.forEach((pestana) => {
    pestana.addEventListener('click', () => {
      pestanas.forEach((p) => {
        p.setAttribute('aria-pressed', String(p === pestana));
        document.getElementById(p.dataset.vista).hidden = p !== pestana;
      });
    });
  });

  filtroSolicitudes.addEventListener('change', pintarSolicitudes);
  filtroVoluntarios.addEventListener('change', pintarVoluntarios);

  /* ---------- Inicio ---------- */

  if (sesion.obtener()?.token) mostrarPanel();
  else mostrarAcceso();
})();
