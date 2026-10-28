/*
  Controlador de la página de detalle: GET /api/animales/{id}/
  animal.html?id=3
*/
import { api } from './api.js';
import { crear, enlaceAdopcion, fotoDe, mostrarMensaje } from './componentes.js';

const contenedor = document.querySelector('#detalle-animal');

function pintarDetalle(animal) {
  document.title = `${animal.nombre} | Huellitas de Esperanza`;
  contenedor.replaceChildren(
    crear('article', { clase: 'detalle' },
      crear('figure', {},
        crear('img', { src: fotoDe(animal), alt: animal.foto_alt || `Fotografía de ${animal.nombre}` }),
        animal.historia ? crear('figcaption', {}, animal.historia) : null,
      ),
      crear('div', {},
        crear('h1', {}, animal.nombre),
        crear('p', {}, animal.descripcion),
        crear('dl', { clase: 'ficha' },
          [
            ['Especie', animal.especie_texto],
            ['Raza', animal.raza],
            ['Sexo', animal.sexo_texto],
            ['Edad', animal.edad_texto],
            ['Tamaño', animal.tamano_texto],
            ['Salud', animal.salud],
            ['Estado', animal.estado_texto],
          ].map(([termino, valor]) => [crear('dt', {}, termino), crear('dd', {}, valor)]),
        ),
        crear('p', { clase: 'tarjeta__acciones' },
          crear('a', { href: 'index.html#animales' }, 'Ver todos los animales'),
          enlaceAdopcion(animal),
        ),
      ),
    ),
  );
}

async function iniciar() {
  const id = new URLSearchParams(location.search).get('id');
  if (!id || !/^\d+$/.test(id)) {
    mostrarMensaje(contenedor, 'error', 'No indicaste qué animal quieres ver.', ['Vuelve al catálogo y elige uno.']);
    return;
  }
  try {
    pintarDetalle(await api.obtenerAnimal(id));
  } catch (error) {
    const titulo = error.estado === 404 ? 'Este animal no existe o ya no está publicado.' : error.message;
    mostrarMensaje(contenedor, 'error', titulo);
    contenedor.append(crear('p', {}, crear('a', { href: 'index.html#animales' }, 'Volver al catálogo')));
  }
}

iniciar();
