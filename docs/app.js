/* ---------------------------------------------------------------------------
   Panel de monitoreo — lógica del navegador.
   Lee docs/datos/noticias.json (lo genera scripts/recolectar.py) y lo dibuja.
--------------------------------------------------------------------------- */

const ZONA = "America/Mexico_City";
const $ = (sel) => document.querySelector(sel);

const estado = {
  datos: null,
  seccionActiva: null,
  busqueda: "",
};

/* ------------------------------- Fechas -------------------------------- */

function hora(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleTimeString("es-MX", {
    timeZone: ZONA, hour: "2-digit", minute: "2-digit", hour12: false,
  });
}

function antiguedad(iso) {
  if (!iso) return "";
  const minutos = Math.round((Date.now() - new Date(iso)) / 60000);
  if (minutos < 60) return `hace ${Math.max(minutos, 1)} min`;
  const horas = Math.round(minutos / 60);
  if (horas < 24) return `hace ${horas} h`;
  return `hace ${Math.round(horas / 24)} d`;
}

function esFresco(iso) {
  return iso ? Date.now() - new Date(iso) < 90 * 60 * 1000 : false;
}

function fechaLarga() {
  const texto = new Date().toLocaleDateString("es-MX", {
    timeZone: ZONA, weekday: "long", day: "numeric", month: "long", year: "numeric",
  });
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

/* ------------------------------ Dibujado ------------------------------- */

function coincide(nota) {
  if (!estado.busqueda) return true;
  const aguja = estado.busqueda.toLowerCase();
  return (nota.titulo + " " + nota.resumen + " " + nota.fuente)
    .toLowerCase().includes(aguja);
}

function notasVisibles(clave) {
  const seccion = estado.datos.secciones[clave];
  return Object.values(seccion.grupos)
    .flatMap((g) => g.articulos)
    .filter(coincide);
}

function dibujarLomo() {
  const lomo = $("#lomo");
  lomo.innerHTML = "";
  Object.entries(estado.datos.secciones).forEach(([clave, seccion]) => {
    const boton = document.createElement("button");
    boton.className = "lomo__boton";
    boton.type = "button";
    boton.setAttribute("aria-current", String(clave === estado.seccionActiva));
    boton.innerHTML = `<span>${seccion.codigo}</span>
      <span class="lomo__cuenta">${notasVisibles(clave).length}</span>`;
    boton.title = seccion.titulo;
    boton.addEventListener("click", () => activar(clave));
    lomo.append(boton);
  });
}

function nodoNota(nota) {
  const a = document.createElement("a");
  a.className = "nota";
  a.href = nota.url;
  a.target = "_blank";
  a.rel = "noopener";
  a.dataset.fresco = esFresco(nota.fecha) ? "si" : "no";

  // "también en" son los medios cuya versión de la misma historia se colapsó.
  const repetida = (nota.tambien_en || []).length;
  const coro = repetida
    ? `también en ${repetida === 1 ? nota.tambien_en[0].split(" · ")[0] : `${repetida} medios`}`
    : "";
  const pie = [nota.fuente, antiguedad(nota.fecha), coro].filter(Boolean).join(" · ");
  a.innerHTML = `
    <span class="nota__hora">${hora(nota.fecha)}</span>
    <h3 class="nota__titular"></h3>
    ${nota.resumen ? '<p class="nota__resumen"></p>' : ""}
    <p class="nota__pie"></p>`;
  a.querySelector(".nota__titular").textContent = nota.titulo;
  a.querySelector(".nota__pie").textContent = pie;
  if (nota.resumen) a.querySelector(".nota__resumen").textContent = nota.resumen;
  return a;
}

function dibujarSecciones() {
  const contenedor = $("#secciones");
  contenedor.innerHTML = "";

  Object.entries(estado.datos.secciones).forEach(([clave, seccion]) => {
    const bloque = document.createElement("section");
    bloque.className = "seccion";
    bloque.dataset.activa = clave === estado.seccionActiva ? "si" : "no";

    const titulo = document.createElement("h2");
    titulo.className = "seccion__titulo";
    titulo.innerHTML = `<span>${seccion.titulo}</span>
      <span class="seccion__codigo">${seccion.codigo}</span>`;
    bloque.append(titulo);

    const copiar = document.createElement("button");
    copiar.className = "seccion__copiar";
    copiar.type = "button";
    copiar.textContent = "Copiar titulares de esta sección";
    copiar.addEventListener("click", () => copiarSeccion(clave, copiar));
    bloque.append(copiar);

    let totales = 0;
    Object.values(seccion.grupos).forEach((grupo) => {
      const notas = grupo.articulos.filter(coincide);
      totales += notas.length;

      // Buscando, un grupo sin resultados solo estorba.
      if (estado.busqueda && notas.length === 0) return;

      const caja = document.createElement("div");
      caja.className = "grupo";
      const encabezado = document.createElement("h3");
      encabezado.className = "grupo__titulo";
      encabezado.innerHTML = `<span>${grupo.titulo}</span>
        <span class="grupo__cuenta">${notas.length}</span>`;
      caja.append(encabezado);

      if (notas.length === 0) {
        const vacio = document.createElement("p");
        vacio.className = "vacio";
        vacio.textContent = estado.datos.desde
          ? "Nada nuevo desde la medianoche. La siguiente recolección es a las 6:30."
          : "Sin titulares nuevos. Revisa el estado de las fuentes al final de la página.";
        caja.append(vacio);
      } else {
        notas.forEach((nota, i) => {
          const nodo = nodoNota(nota);
          nodo.style.animationDelay = `${Math.min(i, 12) * 18}ms`;
          caja.append(nodo);
        });
      }
      bloque.append(caja);
    });

    if (totales === 0 && estado.busqueda) {
      const vacio = document.createElement("p");
      vacio.className = "vacio";
      vacio.textContent = `Nada con “${estado.busqueda}” en esta sección. Prueba otra palabra o revisa las demás secciones: el número junto a cada código dice cuántos titulares coinciden.`;
      bloque.append(vacio);
    }

    contenedor.append(bloque);
  });
}

function activar(clave) {
  estado.seccionActiva = clave;
  location.hash = clave;
  document.querySelectorAll(".seccion").forEach((s, i) => {
    s.dataset.activa = Object.keys(estado.datos.secciones)[i] === clave ? "si" : "no";
  });
  document.querySelectorAll(".lomo__boton").forEach((b, i) => {
    b.setAttribute("aria-current", String(Object.keys(estado.datos.secciones)[i] === clave));
  });
  window.scrollTo({ top: 0, behavior: "instant" });
}

async function copiarSeccion(clave, boton) {
  const lineas = notasVisibles(clave).map(
    (n) => `${n.titulo}\n${n.fuente} — ${n.url}`
  );
  const texto = `${estado.datos.secciones[clave].titulo} · ${fechaLarga()}\n\n${lineas.join("\n\n")}`;
  try {
    await navigator.clipboard.writeText(texto);
    boton.textContent = `${lineas.length} titulares copiados`;
  } catch {
    boton.textContent = "El navegador bloqueó el portapapeles";
  }
  setTimeout(() => { boton.textContent = "Copiar titulares de esta sección"; }, 2600);
}

/* ------------------------------- Fuentes -------------------------------- */

function dibujarSalud() {
  const lista = $("#salud-lista");
  const rotas = estado.datos.fuentes.filter((f) => f.estado === "error");
  $("#salud-resumen").textContent =
    `Estado de las fuentes — ${estado.datos.fuentes.length - rotas.length} vivas, ${rotas.length} con problemas`;

  lista.innerHTML = "";
  estado.datos.fuentes.forEach((f) => {
    const li = document.createElement("li");
    li.dataset.estado = f.estado;
    li.textContent = `${f.estado === "ok" ? "✓" : "✗"} ${f.nombre} — ${f.detalle}`;
    lista.append(li);
  });
}

/* -------------------------------- Arranque ------------------------------ */

// Los resúmenes se pueden apagar; la preferencia se queda en este navegador.
function conectarResumenes() {
  const boton = document.querySelector("#resumenes");
  const guardado = localStorage.getItem("panel:resumenes");
  let visibles = guardado !== "no";

  const pintar = () => {
    document.body.dataset.resumenes = visibles ? "si" : "no";
    boton.setAttribute("aria-pressed", String(visibles));
  };
  pintar();

  boton.addEventListener("click", () => {
    visibles = !visibles;
    localStorage.setItem("panel:resumenes", visibles ? "si" : "no");
    pintar();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "r" && document.activeElement.tagName !== "INPUT") boton.click();
  });
}

function conectarTeclado() {
  const buscador = $("#buscador");
  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && document.activeElement !== buscador) {
      e.preventDefault();
      buscador.focus();
    }
    if (e.key === "Escape" && document.activeElement === buscador) {
      buscador.value = "";
      buscador.dispatchEvent(new Event("input"));
      buscador.blur();
    }
    const claves = Object.keys(estado.datos?.secciones || {});
    if (/^[1-9]$/.test(e.key) && document.activeElement !== buscador) {
      const clave = claves[Number(e.key) - 1];
      if (clave) activar(clave);
    }
  });

  let temporizador;
  buscador.addEventListener("input", (e) => {
    clearTimeout(temporizador);
    temporizador = setTimeout(() => {
      estado.busqueda = e.target.value.trim();
      dibujarSecciones();
      dibujarLomo();
    }, 140);
  });
}

async function iniciar() {
  $("#fecha").textContent = fechaLarga();

  try {
    const respuesta = await fetch(`datos/noticias.json?v=${Date.now()}`);
    if (!respuesta.ok) throw new Error(`HTTP ${respuesta.status}`);
    estado.datos = await respuesta.json();
  } catch (e) {
    $("#cargando").textContent =
      "No se encontró datos/noticias.json. Corre la acción “Actualizar panel” en GitHub o " +
      "python scripts/recolectar.py en tu computadora.";
    return;
  }

  const claves = Object.keys(estado.datos.secciones);
  const desdeUrl = location.hash.replace("#", "");
  estado.seccionActiva = claves.includes(desdeUrl) ? desdeUrl : claves[0];

  $("#cargando").remove();
  const sello = $("#sello");
  sello.textContent = estado.datos.desde
    ? `Actualizado ${antiguedad(estado.datos.generado)} · ${estado.datos.total} titulares desde la medianoche`
    : `Actualizado ${antiguedad(estado.datos.generado)} · ${estado.datos.total} titulares`;
  sello.dataset.fresco = esFresco(estado.datos.generado) ? "si" : "no";

  dibujarLomo();
  dibujarSecciones();
  dibujarSalud();
  conectarResumenes();
  conectarTeclado();
}

iniciar();
