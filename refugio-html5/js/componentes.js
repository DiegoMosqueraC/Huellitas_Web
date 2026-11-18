/*
  Componentes de la interfaz (capa de presentación).
  Cada componente tiene una sola responsabilidad y se reutiliza en varias páginas:
  - <hh-encabezado>: logo, nombre de la fundación y menú principal.
  - <hh-pie>: pie de página.
  - tarjetaAnimal(), filaAnimal(), retratoAnimal(): presentan un animal que llega de la API.
  - mostrarMensaje(): mensajes de éxito, aviso o error.
  Antes, el encabezado y el pie estaban copiados en cada página; ahora un cambio
  en el menú se hace en un solo lugar.
*/

const ENLACES_MENU = [
  ['inicio', 'Inicio'],
  ['animales', 'Animales'],
  ['como-adoptar', 'Cómo adoptar'],
  ['solicitud', 'Solicitud'],
  ['voluntarios', 'Voluntarios'],
  ['contacto', 'Contacto'],
];

class HhEncabezado extends HTMLElement {
  connectedCallback() {
    // En la página de inicio los enlaces son anclas; en las demás vuelven a index.html.
    const base = this.getAttribute('pagina') === 'inicio' ? '' : 'index.html';
    const enlaces = ENLACES_MENU
      .map(([id, texto]) => `<li><a href="${base}#${id}">${texto}</a></li>`)
      .join('');

    this.innerHTML = `
      <header class="encabezado">
        <div class="encabezado__interior">
          <a class="marca" href="${base || '#inicio'}">
            <img src="img/logo.svg" alt="" width="44" height="44">
            <span>Huellitas de Esperanza</span>
          </a>
          <nav aria-label="Navegación principal">
            <ul class="menu">${enlaces}</ul>
          </nav>
        </div>
      </header>`;
  }
}

class HhPie extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <footer class="pie">
        <div class="pie__interior">
          <p class="pie__marca">
            <img src="img/logo.svg" alt="" width="36" height="36">
            Fundación Huellitas de Esperanza
          </p>
          <p>Organización de ejemplo creada con fines académicos. Los animales, las cifras y los datos de contacto son de demostración.</p>
          <p>
            Proyecto de Desarrollo Avanzado de Aplicaciones en Red, Ingeniería de Software, FESC.
            Desarrollado por Diego Alejandro Mosquera Caicedo, José Miguel Vera Castillo y Camilo Andres Jaimes Gamboa.
          </p>
          <p><small>&copy; 2026. El logotipo es una ilustración propia. Las fotografías de los animales son imágenes de referencia usadas solo con fines académicos; sus derechos pertenecen a sus autores.</small></p>
          <p class="pie__enlaces"><a href="#">Volver arriba</a> <a href="admin.html">Acceso para el personal</a></p>
        </div>
      </footer>`;
  }
}

customElements.define('hh-encabezado', HhEncabezado);
customElements.define('hh-pie', HhPie);

/* Crea un elemento con atributos e hijos. Los textos se insertan como texto
   (no como HTML), así un dato de la API nunca se ejecuta como código. */
function crear(etiqueta, atributos = {}, ...hijos) {
  const elemento = document.createElement(etiqueta);
  for (const [nombre, valor] of Object.entries(atributos)) {
    if (valor === false || valor == null) continue;
    if (nombre === 'clase') elemento.className = valor;
    else elemento.setAttribute(nombre, valor === true ? '' : valor);
  }
  elemento.append(...hijos.flat(Infinity).filter((h) => h != null && h !== false));
  return elemento;
}

function fotoDe(animal) {
  return animal.foto || 'img/logo.svg';
}

function altDe(animal) {
  return animal.foto_alt || `Fotografía de ${animal.nombre}`;
}

function enlaceAdopcion(animal) {
  if (animal.estado !== 'DISPONIBLE') {
    return crear('p', { clase: 'etiqueta etiqueta--aviso' }, animal.estado_texto);
  }
  return crear('a', { clase: 'boton', href: `index.html?animal=${animal.id}#solicitud` }, `Quiero adoptar a ${animal.nombre}`);
}

/* La "placa" es el nombre del animal con forma de placa de collar: el sello visual del sitio. */
function tarjetaAnimal(animal) {
  const ficha = `animal.html?id=${animal.id}`;
  return crear('article', { clase: 'tarjeta', id: `animal-${animal.id}` },
    crear('img', { clase: 'tarjeta__foto', src: fotoDe(animal), alt: altDe(animal), loading: 'lazy', width: 400, height: 300 }),
    crear('div', { clase: 'tarjeta__cuerpo' },
      crear('h3', { clase: 'placa' }, animal.nombre),
      crear('ul', { clase: 'rasgos', 'aria-label': `Datos de ${animal.nombre}` },
        [animal.especie_texto, animal.sexo_texto, animal.edad_texto, animal.tamano_texto]
          .map((rasgo) => crear('li', {}, rasgo)),
      ),
      crear('p', { clase: 'tarjeta__raza' }, animal.raza),
      crear('p', {}, animal.descripcion),
      crear('p', { clase: 'tarjeta__acciones' },
        enlaceAdopcion(animal),
        crear('a', { href: ficha }, `Ver la ficha de ${animal.nombre}`),
      ),
    ),
  );
}

/* Retrato de la portada: foto enlazada a la ficha, con la placa del nombre. */
function retratoAnimal(animal) {
  return crear('a', { clase: 'retrato', href: `animal.html?id=${animal.id}` },
    crear('img', { src: fotoDe(animal), alt: altDe(animal), width: 320, height: 400 }),
    crear('span', { clase: 'placa' }, animal.nombre),
  );
}

function filaAnimal(animal) {
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
function mostrarMensaje(contenedor, tipo, titulo, items = []) {
  contenedor.replaceChildren(
    crear('div', { clase: `mensaje mensaje--${tipo}` },
      crear('p', {}, crear('strong', {}, titulo)),
      items.length ? crear('ul', {}, items.map((texto) => crear('li', {}, texto))) : null,
    ),
  );
}
