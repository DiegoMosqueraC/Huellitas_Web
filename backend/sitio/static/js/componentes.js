/*
  Piezas de interfaz que crea JavaScript para los formularios y el panel:
  - crear(): arma elementos insertando los textos como texto, nunca como HTML.
  - mostrarMensaje(): mensajes de éxito, aviso o error.
  El encabezado, el pie, las tarjetas y las fichas de los animales son plantillas
  de Django (sitio/templates/sitio/), que el servidor arma antes de enviar la página.
*/

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

/* tipo: 'exito' | 'aviso' | 'error'. items: lista opcional de detalles. */
function mostrarMensaje(contenedor, tipo, titulo, items = []) {
  contenedor.replaceChildren(
    crear('div', { clase: `mensaje mensaje--${tipo}` },
      crear('p', {}, crear('strong', {}, titulo)),
      items.length ? crear('ul', {}, items.map((texto) => crear('li', {}, texto))) : null,
    ),
  );
}
