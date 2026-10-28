/*
  Controlador de la página de inicio (frontend).
  Detecta las acciones del usuario, pide los datos a la API mediante api.js
  y le entrega el resultado a los componentes para que lo presenten.
*/
import { api } from './api.js';
import { crear, filaAnimal, mostrarMensaje, tarjetaAnimal } from './componentes.js';
import { limpiarErrores, marcarErrores } from './formularios.js';

const listaAnimales = document.querySelector('#lista-animales');
const tablaAnimales = document.querySelector('#tabla-animales');
const totalAnimales = document.querySelector('#total-animales');
const filtros = document.querySelectorAll('[data-especie]');
const formulario = document.querySelector('#form-solicitud');
const selectAnimal = document.querySelector('#animal');
const resultado = document.querySelector('#resultado-solicitud');
const botonEnviar = formulario.querySelector('button[type="submit"]');

// Nombre del campo en la API -> nombre del campo en el formulario.
const CAMPOS_FORMULARIO = { animal_id: 'animal' };

/* ---------- Catálogo: GET /api/animales/ ---------- */

async function cargarCatalogo(especie = '') {
  listaAnimales.setAttribute('aria-busy', 'true');
  try {
    const animales = await api.listarAnimales(especie);
    listaAnimales.replaceChildren(...animales.map(tarjetaAnimal));
    if (!animales.length) mostrarMensaje(listaAnimales, 'aviso', 'No hay animales publicados con ese filtro.');
  } catch (error) {
    mostrarMensaje(listaAnimales, 'error', error.message);
  } finally {
    listaAnimales.removeAttribute('aria-busy');
  }
}

function pintarResumen(animales) {
  tablaAnimales.replaceChildren(...animales.map(filaAnimal));
  const disponibles = animales.filter((a) => a.estado === 'DISPONIBLE').length;
  totalAnimales.textContent = `Total: ${animales.length} animales publicados, ${disponibles} disponibles.`;
}

function llenarSelectAnimales(animales) {
  const grupos = { perro: 'Perros', gato: 'Gatos' };
  const opciones = Object.entries(grupos).map(([especie, etiqueta]) =>
    crear('optgroup', { label: etiqueta },
      animales.filter((a) => a.especie === especie).map((a) =>
        crear('option', { value: a.id, disabled: a.estado !== 'DISPONIBLE' },
          `${a.nombre} – ${a.raza}, ${a.edad_texto}${a.estado !== 'DISPONIBLE' ? ' – ' + a.estado_texto.toLowerCase() : ''}`),
      ),
    ),
  );
  selectAnimal.replaceChildren(
    crear('option', { value: '' }, 'Selecciona un animal'),
    ...opciones,
    crear('option', { value: 'sin-preferencia' }, 'Aún no lo decido, quiero orientación'),
  );

  // Viene de "Quiero adoptar a ...": index.html?animal=3#solicitud
  const elegido = new URLSearchParams(location.search).get('animal');
  if (elegido && selectAnimal.querySelector(`option[value="${CSS.escape(elegido)}"]:not([disabled])`)) {
    selectAnimal.value = elegido;
  }
}

async function iniciarCatalogo() {
  try {
    const animales = await api.listarAnimales();
    listaAnimales.replaceChildren(...animales.map(tarjetaAnimal));
    pintarResumen(animales);
    llenarSelectAnimales(animales);
  } catch (error) {
    mostrarMensaje(listaAnimales, 'error', error.message);
    totalAnimales.textContent = 'No fue posible cargar la información.';
  }
}

filtros.forEach((boton) => {
  boton.addEventListener('click', () => {
    filtros.forEach((b) => b.setAttribute('aria-pressed', String(b === boton)));
    cargarCatalogo(boton.dataset.especie);
  });
});

/* ---------- Solicitud: POST /api/solicitudes/ ---------- */

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
      `Estado actual: ${respuesta.estado}.`,
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
iniciarCatalogo();
