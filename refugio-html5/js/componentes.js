/*
  Componentes de la interfaz (capa de presentación).
  Cada componente tiene una sola responsabilidad y se reutiliza en varias páginas:
  - <hh-encabezado>: logo, nombre de la fundación y menú principal.
  - <hh-pie>: pie de página.
  - tarjetaAnimal(), filaAnimal(): presentan un animal que llega de la API.
  - mostrarMensaje(): mensajes de éxito, aviso o error.
  Antes, el encabezado y el pie estaban copiados en cada página; ahora un cambio
  en el menú se hace en un solo lugar.
*/

const ENLACES_MENU = [
  ['inicio', 'Inicio'],
  ['animales', 'Animales en adopción'],
  ['como-adoptar', 'Cómo adoptar'],
  ['solicitud', 'Solicitud de adopción'],
  ['voluntarios', 'Voluntarios'],
  ['contacto', 'Contacto'],
];

class HhEncabezado extends HTMLElement {
  connectedCallback() {
    const enInicio = this.getAttribute('pagina') === 'inicio';
    const base = enInicio ? '' : 'index.html';
    const titulo = enInicio
      ? '<h1>Fundación Huellitas de Esperanza</h1>'
      : '<p class="marca"><a href="index.html">Fundación Huellitas de Esperanza</a></p>';
    const enlaces = ENLACES_MENU
      .map(([id, texto]) => `<li><a href="${base}#${id}">${texto}</a></li>`)
      .join('');

    this.innerHTML = `
      <header class="encabezado">
        <div class="encabezado__marca">
          <img src="img/logo.svg" alt="Logo de la Fundación Huellitas de Esperanza: una huella de perro dentro de un corazón" width="72" height="72">
          <div>
            ${titulo}
            <p class="encabezado__lema">Rescatamos, cuidamos y buscamos un hogar responsable para perros y gatos en situación de abandono.</p>
          </div>
        </div>
        <nav aria-label="Navegación principal">
          <ul class="menu">${enlaces}</ul>
        </nav>
        <p class="aviso-demo"><small>Organización de ejemplo creada con fines académicos. Los datos mostrados son de demostración.</small></p>
      </header>`;
  }
}

class HhPie extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <footer class="pie">
        <p>&copy; 2026 Fundación Huellitas de Esperanza (organización de ejemplo).</p>
        <p>
          Proyecto académico de Desarrollo Avanzado de Aplicaciones en Red, Ingeniería de Software, FESC.
          Desarrollado por Diego Alejandro Mosquera Caicedo, José Miguel Vera Castillo y Camilo Andres Jaimes Gamboa.
        </p>
        <p><small>El logotipo es una ilustración propia. Las fotografías de los animales son imágenes de referencia usadas solo con fines académicos; sus derechos pertenecen a sus autores.</small>
          <a href="#">Volver arriba</a> · <a href="admin.html">Acceso para el personal</a></p>
      </footer>`;
  }
}

customElements.define('hh-encabezado', HhEncabezado);
customElements.define('hh-pie', HhPie);

/* Crea un elemento con atributos e hijos. Los textos se insertan como texto
   (no como HTML), así un dato de la API nunca se ejecuta como código. */
export function crear(etiqueta, atributos = {}, ...hijos) {
  const elemento = document.createElement(etiqueta);
  for (const [nombre, valor] of Object.entries(atributos)) {
    if (valor === false || valor == null) continue;
    if (nombre === 'clase') elemento.className = valor;
    else elemento.setAttribute(nombre, valor === true ? '' : valor);
  }
  elemento.append(...hijos.flat(Infinity).filter((h) => h != null && h !== false));
  return elemento;
}

export function fotoDe(animal) {
  return animal.foto || 'img/logo.svg';
}

export function enlaceAdopcion(animal) {
  if (animal.estado !== 'DISPONIBLE') {
    return crear('p', { clase: 'etiqueta etiqueta--aviso' }, animal.estado_texto);
  }
  return crear('a', { clase: 'boton', href: `index.html?animal=${animal.id}#solicitud` }, `Quiero adoptar a ${animal.nombre}`);
}

export function tarjetaAnimal(animal) {
  return crear('article', { clase: 'tarjeta', id: `animal-${animal.id}` },
    crear('img', { src: fotoDe(animal), alt: animal.foto_alt || `Fotografía de ${animal.nombre}`, loading: 'lazy', width: 300, height: 300 }),
    crear('div', { clase: 'tarjeta__cuerpo' },
      crear('h3', {}, animal.nombre),
      crear('p', { clase: 'tarjeta__datos' }, `${animal.especie_texto} · ${animal.raza} · ${animal.sexo_texto} · ${animal.edad_texto} · ${animal.tamano_texto}`),
      crear('p', {}, animal.descripcion),
      crear('p', { clase: 'tarjeta__acciones' },
        crear('a', { href: `animal.html?id=${animal.id}` }, 'Ver detalle'),
        enlaceAdopcion(animal),
      ),
    ),
  );
}

export function filaAnimal(animal) {
  return crear('tr', {},
    crear('td', {}, crear('a', { href: `animal.html?id=${animal.id}` }, animal.nombre)),
    crear('td', {}, animal.especie_texto),
    crear('td', {}, animal.raza),
    crear('td', {}, animal.sexo_texto),
    crear('td', {}, animal.edad_texto),
    crear('td', {}, animal.tamano_texto),
    crear('td', {}, animal.estado_texto),
  );
}

/* tipo: 'exito' | 'aviso' | 'error'. items: lista opcional de detalles. */
export function mostrarMensaje(contenedor, tipo, titulo, items = []) {
  contenedor.replaceChildren(
    crear('div', { clase: `mensaje mensaje--${tipo}` },
      crear('p', {}, crear('strong', {}, titulo)),
      items.length ? crear('ul', {}, items.map((texto) => crear('li', {}, texto))) : null,
    ),
  );
}
