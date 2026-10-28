/*
  Ayudas compartidas por los formularios que envían datos a la API
  (solicitud de adopción y registro de voluntarios): marcar en rojo los campos
  que el servidor rechazó y convertir sus errores en mensajes legibles.
*/

// campos: nombre del campo en la API -> nombre del campo en el formulario, cuando son distintos.
function etiquetaDe(formulario, campoApi, campos) {
  const nombre = campos[campoApi] ?? campoApi;
  const campo = formulario.elements[nombre];
  const elemento = campo instanceof RadioNodeList ? campo[0] : campo;
  const etiqueta = elemento && formulario.querySelector(`label[for="${elemento.id}"]`);
  return { elemento, texto: etiqueta ? etiqueta.textContent.replace('*', '').trim() : campoApi };
}

export function limpiarErrores(formulario) {
  formulario.querySelectorAll('[aria-invalid="true"]').forEach((el) => el.removeAttribute('aria-invalid'));
}

/* Marca los campos con error y devuelve la lista de mensajes "Etiqueta: error". */
export function marcarErrores(formulario, detalles, campos = {}) {
  const items = [];
  for (const [campo, mensajes] of Object.entries(detalles ?? {})) {
    const { elemento, texto } = etiquetaDe(formulario, campo, campos);
    elemento?.setAttribute('aria-invalid', 'true');
    items.push(`${texto}: ${[].concat(mensajes).join(' ')}`);
  }
  return items;
}
