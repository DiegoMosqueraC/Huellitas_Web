/*
  Controlador de la página Mi solicitud: POST /api/solicitudes/consulta/
  Muestra el estado de una solicitud a partir de su número y el documento del solicitante.
*/
(() => {
  const formulario = document.querySelector('#form-consulta');
  const resultado = document.querySelector('#resultado-consulta');
  const botonEnviar = formulario.querySelector('button[type="submit"]');

  const fecha = (iso) => new Date(iso).toLocaleDateString('es-CO', { day: 'numeric', month: 'long', year: 'numeric' });

  function pintarSolicitud(s) {
    resultado.replaceChildren(
      crear('article', { clase: 'tarjeta-estado' },
        crear('h2', {}, `Solicitud #${s.id}`),
        crear('p', {}, crear('span', { clase: `estado estado--${s.estado.toLowerCase()}` }, s.estado_texto)),
        crear('dl', { clase: 'ficha' },
          crear('dt', {}, 'Animal'),
          crear('dd', {}, s.animal ? crear('a', { href: `/animales/${s.animal.id}/` }, s.animal.nombre) : 'Sin preferencia (te orientaremos)'),
          crear('dt', {}, 'Enviada el'),
          crear('dd', {}, fecha(s.fecha_creacion)),
          crear('dt', {}, 'Última actualización'),
          crear('dd', {}, fecha(s.fecha_actualizacion)),
          s.observacion ? [crear('dt', {}, 'Observación'), crear('dd', {}, s.observacion)] : null,
        ),
      ),
    );
  }

  formulario.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    limpiarErrores(formulario);
    botonEnviar.disabled = true;
    mostrarMensaje(resultado, 'aviso', 'Consultando…');
    try {
      const datos = new FormData(formulario);
      pintarSolicitud(await api.consultarSolicitud(Number(datos.get('numero')), datos.get('documento').trim()));
    } catch (error) {
      const items = marcarErrores(formulario, error.detalles);
      mostrarMensaje(resultado, error.estado === 404 ? 'aviso' : 'error', error.message, items);
    } finally {
      botonEnviar.disabled = false;
    }
  });
})();
