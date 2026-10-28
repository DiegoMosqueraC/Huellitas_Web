/*
  Controlador del registro de voluntarios: POST /api/voluntarios/
*/
import { api } from './api.js';
import { mostrarMensaje } from './componentes.js';
import { limpiarErrores, marcarErrores } from './formularios.js';

const formulario = document.querySelector('#form-voluntario');
const resultado = document.querySelector('#resultado-voluntario');
const botonEnviar = formulario.querySelector('button[type="submit"]');
const dias = formulario.querySelectorAll('input[name="disponibilidad"]');

// HTML5 no puede exigir "al menos una casilla", así que se avisa antes de enviar.
// El servidor lo vuelve a validar de todas formas.
function validarDias() {
  const algunoMarcado = [...dias].some((d) => d.checked);
  dias[0].setCustomValidity(algunoMarcado ? '' : 'Elige al menos un día disponible.');
}
dias.forEach((d) => d.addEventListener('change', validarDias));
validarDias();

function leerFormulario() {
  const datos = new FormData(formulario);
  return {
    nombre: datos.get('nombre').trim(),
    correo: datos.get('correo').trim(),
    telefono: datos.get('telefono').trim(),
    edad: Number(datos.get('edad')),
    red_social: datos.get('red_social').trim(),
    disponibilidad: datos.getAll('disponibilidad'),
    area: datos.get('area'),
    experiencia: datos.get('experiencia') === 'si',
    comentarios: datos.get('comentarios').trim(),
    acepta_datos: datos.has('acepta_datos'),
  };
}

formulario.addEventListener('submit', async (evento) => {
  evento.preventDefault();
  limpiarErrores(formulario);
  botonEnviar.disabled = true;
  mostrarMensaje(resultado, 'aviso', 'Enviando tu registro…');

  try {
    const respuesta = await api.registrarVoluntario(leerFormulario());
    mostrarMensaje(resultado, 'exito', `¡Registro #${respuesta.id} recibido!`, [
      respuesta.mensaje,
      `Estado actual: ${respuesta.estado}.`,
    ]);
    formulario.reset();
    validarDias();
  } catch (error) {
    const items = marcarErrores(formulario, error.detalles);
    mostrarMensaje(resultado, error.estado === 409 ? 'aviso' : 'error', error.message, items);
    formulario.querySelector('[aria-invalid="true"]')?.focus();
  } finally {
    botonEnviar.disabled = false;
    resultado.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
});
