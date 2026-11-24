/*
  Animaciones del sitio (todas las páginas; se carga desde base.html).
  - Sombra del encabezado al desplazarse.
  - Tarjetas, pasos y cifras que aparecen al llegar a ellos.
  - Cifras de la portada que cuentan hasta su valor.
  Si el visitante pidió reducir el movimiento, base.html no pone la clase "anima"
  y aquí solo queda la sombra del encabezado.
*/
(function () {
  const raiz = document.documentElement;

  const encabezado = document.querySelector('.encabezado');
  const sombrear = () => encabezado.classList.toggle('con-sombra', window.scrollY > 8);
  window.addEventListener('scroll', sombrear, { passive: true });
  sombrear();

  if (!raiz.classList.contains('anima')) return;

  // Al terminar la entrada de la portada se quitan sus animaciones (deja libres los efectos al pasar el puntero).
  setTimeout(() => raiz.classList.add('listo'), 2600);

  const contar = (elemento) => {
    const final = parseInt(elemento.textContent, 10);
    if (Number.isNaN(final)) return;
    const inicio = performance.now();
    const paso = (ahora) => {
      const t = Math.min((ahora - inicio) / 1200, 1);
      elemento.textContent = Math.round(final * (1 - Math.pow(1 - t, 3)));
      if (t < 1) requestAnimationFrame(paso);
    };
    requestAnimationFrame(paso);
  };

  const elementos = document.querySelectorAll(
    '.rejilla-animales > *, .caminos > *, .cifras li, .requisitos li, .pasos li, .contacto__rejilla > *'
  );
  if (!('IntersectionObserver' in window)) {
    elementos.forEach((e) => e.classList.add('revelado'));
    return;
  }

  const observador = new IntersectionObserver((entradas) => {
    entradas.forEach(({ isIntersecting, target }) => {
      if (!isIntersecting) return;
      observador.unobserve(target);
      target.classList.add('visible');
      const numero = target.querySelector('.cifras strong, :scope > strong');
      if (numero) contar(numero);
      const espera = 700 + (parseInt(target.style.getPropertyValue('--orden'), 10) || 0) * 80;
      setTimeout(() => target.classList.add('revelado'), espera + 50);
    });
  }, { rootMargin: '0px 0px -8% 0px' });

  elementos.forEach((e) => {
    // Escalonado dentro de cada grupo, máximo 6 pasos para no hacer esperar.
    e.style.setProperty('--orden', Math.min([...e.parentElement.children].indexOf(e), 6));
    observador.observe(e);
  });
})();
