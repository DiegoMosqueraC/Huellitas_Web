/*
  Controlador del formulario de la página Adoptar: POST /api/solicitudes/
  La lista de animales y el animal elegido ya vienen en la página (los arma Django);
  este script solo envía la solicitud a la API y muestra la respuesta.
*/
(() => {
  const formulario = document.querySelector('#form-solicitud');
  const resultado = document.querySelector('#resultado-solicitud');
  const botonEnviar = formulario.querySelector('button[type="submit"]');

  // Nombre del campo en la API -> nombre del campo en el formulario.
  const CAMPOS_FORMULARIO = { animal_id: 'animal' };

  function leerFormulario() {
    const datos = new FormData(formulario);
    const animal = datos.get('animal');
    // El cliente solo envía lo que el contrato permite. El estado de la
    // solicitud lo decide el servidor, nunca el navegador.
    return {
      animal_id: animal === 'sin-preferencia' ? null : Number(animal),
      nombre: datos.get('nombre').trim(),
      tipo_documento: datos.get('tipo_documento'),
      documento: datos.get('documento').trim(),
      fecha_nacimiento: datos.get('fecha_nacimiento'),
      correo: datos.get('correo').trim(),
      telefono: datos.get('telefono').trim(),
      direccion: datos.get('direccion').trim(),
      ciudad: datos.get('ciudad').trim(),
      tipo_vivienda: datos.get('tipo_vivienda'),
      tenencia: datos.get('tenencia'),
      personas_hogar: Number(datos.get('personas_hogar')),
      otras_mascotas: datos.getAll('otras_mascotas'),
      horas_solo: Number(datos.get('horas_solo')),
      fecha_visita: datos.get('fecha_visita') || null,
      hora_visita: datos.get('hora_visita') || null,
      motivo: datos.get('motivo').trim(),
      medio: datos.get('medio') || '',
      acepta_datos: datos.has('acepta_datos'),
      acepta_visita: datos.has('acepta_visita'),
    };
  }

  formulario.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    limpiarErrores(formulario);
    botonEnviar.disabled = true;
    mostrarMensaje(resultado, 'aviso', 'Enviando tu solicitud…');

    try {
      const respuesta = await api.registrarSolicitud(leerFormulario());
      const animal = respuesta.animal ? ` para adoptar a ${respuesta.animal.nombre}` : '';
      mostrarMensaje(resultado, 'exito', `¡Solicitud #${respuesta.id} recibida${animal}!`, [
        respuesta.mensaje,
        `Guarda el número ${respuesta.id}: con él y tu documento puedes ver en qué va tu solicitud en "Mi solicitud".`,
      ]);
      formulario.reset();
      actualizarHorasSolo();
    } catch (error) {
      const items = marcarErrores(formulario, error.detalles, CAMPOS_FORMULARIO);
      mostrarMensaje(resultado, error.estado === 409 ? 'aviso' : 'error', error.message, items);
      formulario.querySelector('[aria-invalid="true"]')?.focus();
    } finally {
      botonEnviar.disabled = false;
      resultado.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  });

  /* ---------- Ayudas del formulario ---------- */

  const horasSolo = document.querySelector('#horas-solo');
  const horasSoloValor = document.querySelector('#horas-solo-valor');
  function actualizarHorasSolo() {
    horasSoloValor.textContent = horasSolo.value;
  }
  horasSolo.addEventListener('input', actualizarHorasSolo);

  // Fechas límite calculadas con el día de hoy en lugar de fechas fijas.
  const hoy = new Date();
  const dosDigitos = (n) => String(n).padStart(2, '0');
  const aIso = (fecha) => `${fecha.getFullYear()}-${dosDigitos(fecha.getMonth() + 1)}-${dosDigitos(fecha.getDate())}`;
  document.querySelector('#fecha-visita').min = aIso(hoy);
  document.querySelector('#fecha-nac').max = aIso(new Date(hoy.getFullYear() - 18, hoy.getMonth(), hoy.getDate()));

  actualizarHorasSolo();
})();
