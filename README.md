# Panel de monitoreo

Un tablero personal de noticias que se arma solo cuatro veces al día y se lee en el
navegador o el celular. Trae los titulares de tus medios por RSS, los reparte en
secciones y publica la página en GitHub Pages. No usa servidor, base de datos ni
servicios de paga: solo un repositorio de GitHub.

**Secciones**

| Código | Sección | Qué trae |
|---|---|---|
| MX | Nacional | Política · Economía · CDMX · Opinión · Tecnología |
| IA | Inteligencia artificial | The New York Times por un lado; Techmeme, TechCrunch, Wired, The Verge, MIT Tech Review y Google Noticias por otro |
| CO | Colombia | Lo más importante del día |
| AR | Argentina | Lo más importante del día |
| ES | España | Lo más importante del día |
| MUNDO | Internacional | Última hora (Google Noticias) · Miradas: Al Jazeera, BBC Mundo, DW, France 24, The Guardian, SCMP, Middle East Eye |
| SHOW | Espectáculos | TMZ, ET y E! |

---

## Cómo se arma

```
fuentes.yaml                lista de medios y a qué sección va cada uno
scripts/recolectar.py       descarga los feeds y escribe docs/datos/noticias.json
scripts/clasificar.py       decide si un titular es de Política, CDMX, IA, etc.
scripts/verificar_fuentes.py  dice qué feeds responden y cuáles se rompieron
scripts/demo.py             llena el panel con ejemplos para ver el diseño
docs/                       la página: index.html, estilos.css, app.js
.github/workflows/          la tarea que corre cada dos horas
```

Se actualiza a las 6:30, 8:00, 10:00, 15:00 y 20:00, hora de la Ciudad de México,
y se reinicia a medianoche: cada día empieza en blanco y solo entran titulares
publicados a partir de las 00:00.
La acción de GitHub descarga, clasifica y guarda `docs/datos/noticias.json` en el
propio repositorio. La página lee ese archivo. Eso es todo el mecanismo.

---

## Puesta en marcha (10 minutos)

**1. Crea el repositorio.** En GitHub: *New repository* → nómbralo `panel-noticias`
→ **Public** (con repositorio público, GitHub Actions y Pages no cuestan nada) →
*Create*.

**2. Sube los archivos.** Con la terminal:

```bash
cd panel-noticias
git init
git add .
git commit -m "Primera versión del panel"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/panel-noticias.git
git push -u origin main
```

O desde el navegador: *Add file → Upload files*, arrastra todas las carpetas
(incluida `.github`, que a veces el Finder oculta: en Mac se muestra con
`Cmd + Shift + .`).

**3. Da permiso de escritura a la acción.** *Settings → Actions → General →
Workflow permissions* → **Read and write permissions** → *Save*. Sin esto, la
acción descarga los titulares pero no puede guardarlos.

**4. Enciende la página.** *Settings → Pages → Source: Deploy from a branch* →
rama `main`, carpeta `/docs` → *Save*. Tu panel queda en
`https://TU-USUARIO.github.io/panel-noticias/`.

**5. Corre la primera actualización.** *Actions → Actualizar panel → Run workflow*.
Tarda un par de minutos. Al terminar, abre tu página: en el pie viene el estado de
cada fuente.

**6. Guárdalo en el celular.** Ábrelo en Safari o Chrome y usa *Compartir → Agregar
a la pantalla de inicio*. Queda como una app.

---

## Antes de subirlo, si quieres probarlo en tu compu

```bash
pip install -r requirements.txt
python scripts/demo.py            # titulares de ejemplo, sin internet
python -m http.server -d docs 8000
# abre http://localhost:8000
```

Y con internet real:

```bash
python scripts/verificar_fuentes.py   # ¿qué medios responden?
python scripts/recolectar.py          # descarga de verdad
```

---

## Cómo lo ajustas

**Agregar o quitar un medio:** edita `fuentes.yaml`. Cada entrada necesita
`nombre`, `url` (la dirección del RSS) y `seccion`. En Nacional puedes fijar la
subsección con `subseccion: economia`; si no la pones, el titular se clasifica
solo. Al guardar el archivo en GitHub, la acción vuelve a correr.

**Cambiar qué cuenta como "Economía" o "CDMX":** las listas de palabras clave
están al principio de `scripts/clasificar.py`, en español y sin acentos. Agrega
las que uses tú: nombres de funcionarios, temas que sigues, palabras de tu
cobertura. El orden de `PRIORIDAD` decide quién gana cuando un titular encaja en
dos secciones.

**Cambiar los horarios:** en `.github/workflows/actualizar.yml`, las líneas
`cron:`. Los números son horas UTC; para saber cuál poner, súmale 6 a la hora que
quieres en la CDMX (las 7:00 de la mañana son las 13). GitHub suele correr la
tarea unos minutos después de la hora marcada, y a veces se retrasa más si sus
servidores están saturados.

**Quitar el reinicio diario:** pon `reinicio_diario: false` en `fuentes.yaml`.
Con el reinicio encendido, el panel descarta lo publicado antes de la medianoche
y también los titulares que llegan sin fecha, porque sin fecha no hay forma de
saber si son de hoy. Con él apagado, el panel arrastra hasta 48 horas.

**Cuántos titulares por bloque y qué tan viejos:** `ajustes` en `fuentes.yaml`.

---

## Atajos en la página

| Tecla | Qué hace |
|---|---|
| `1` – `7` | Cambia de sección |
| `/` | Salta al buscador |
| `Esc` | Limpia la búsqueda |
| `r` | Muestra u oculta los resúmenes |

El botón *Resúmenes*, arriba a la derecha, muestra dos renglones de contexto
bajo cada titular. Se apaga con un clic y el panel recuerda tu preferencia en
ese navegador. No todos los medios mandan resumen, y los que solo repiten el
titular se descartan.

El botón *Copiar titulares de esta sección* deja en el portapapeles la lista con
titular, medio y liga: sirve para pasarla a un correo o a un reporte.

---

## Lo que conviene saber

- **Las direcciones RSS cambian sin avisar.** Las que trae `fuentes.yaml` son las
  públicas conocidas de cada medio, pero algunas pueden haber cambiado o requerir
  otra ruta. Corre `verificar_fuentes.py`, mira el pie de la página y reemplaza
  las que salgan con ✗. Buscar `nombre del medio + RSS` casi siempre da la buena.
- **Algunos medios bloquean descargas automáticas.** Si uno responde `HTTP 401`
  o `403` una y otra vez, cámbialo por otro medio del mismo tema.
- **Varios medios ya no publican RSS propio.** Milenio, Excélsior, Uno TV,
  Debate, Proceso, Aristegui, Animal Político, El Espectador, Blu Radio,
  El Destape y los Infobae por país devolvían 404 o 403 en la primera revisión.
  Todos ellos entran ahora por un feed de búsqueda de Google Noticias limitado a
  su dominio (`site:milenio.com when:1d`). Sigues leyendo al mismo medio; la
  única diferencia es que la liga pasa por `news.google.com`.
- **Las agencias ya no dan RSS.** Reuters cerró sus feeds en 2020 y AP hizo lo
  mismo; por eso el panel usa Techmeme y feeds de búsqueda de Google Noticias
  para recuperar lo que ellas publican. En esos feeds la liga pasa por
  `news.google.com` antes de llegar al medio.
- **El panel guarda titular, resumen corto y liga**, nunca el texto completo: el
  contenido es de cada medio y la liga manda a su sitio.
- **GitHub apaga las tareas programadas** en repositorios sin actividad de la
  persona dueña durante 60 días. Si un día deja de actualizarse, entra a *Actions*
  y dale *Enable workflow*.
- **La primera corrida del día (00:00) deja el panel casi vacío a propósito.**
  Se llena a las 6:30 y va creciendo con cada actualización.
- Los horarios de la página se muestran en hora de la Ciudad de México.
